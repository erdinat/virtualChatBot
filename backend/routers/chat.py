"""Chat endpoint — SSE streaming ile yanıt akışı."""

import json
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.auth import get_current_user
from backend.schemas import ChatRequest
from modules.storage import load_student_data, append_chat_log
from modules.pedagogy.socratic import SocraticManager
from modules.drl.policy import RuleBasedPolicy
from config.settings import CURRICULUM

router = APIRouter()

# Basit in-memory cache (production'da Redis kullanılabilir)
_socratic_managers: dict[str, SocraticManager] = {}
_rag_chain_cache: dict = {"chain": None, "vector_store": None}

# Konu bazlı seviye prompt'ları — ön test sonrası chat'te kullanılır
_LEVEL_PROMPT: dict[str, str] = {
    "beginner": (
        "Öğrenci bu konuya yeni başlıyor. "
        "Temel kavramları basit dil ve günlük hayat örnekleriyle açıkla. "
        "Karmaşık edge-case'lere girme; adım adım ilerle."
    ),
    "intermediate": (
        "Öğrenci temel kavramları biliyor; temel tekrarı atla. "
        "Orta-ileri konulara odaklan: iç içe yapılar, özel durumlar, yaygın hatalar."
    ),
    "advanced": (
        "Öğrenci konuda yetkindir. "
        "Zorlu örnekler, Pythonic kalıplar ve uç durumlar üzerinden ilerle. "
        "Performans, okunabilirlik ve best-practice'lere değin."
    ),
}

_TOPIC_KEYWORDS = {
    1: ["değişken", "veri tipi", "string", "integer", "float", "bool"],
    2: ["operatör", "operator", "ifade", "aritmetik", "modulo"],
    3: ["if", "elif", "else", "koşul", "condition"],
    4: ["for", "while", "döngü", "loop", "range"],
    5: ["liste", "list", "tuple", "append", "index"],
    6: ["sözlük", "dict", "küme", "set", "key", "value"],
    7: ["fonksiyon", "function", "def ", "return", "lambda"],
    8: ["dosya", "file", "open(", "csv", "with open"],
    9: ["hata", "error", "exception", "try:", "except"],
    10: ["sınıf", "class ", "nesne", "object", "oop", "self."],
}

_UNDERSTOOD_PHRASES = ["anladım", "tamam anladım", "teşekkürler", "teşekkür ederim", "sağ ol"]
_SIMPLIFY_PHRASES   = ["anlamadım", "basitçe anlat", "daha basit", "ne demek", "tekrar anlat"]


def _detect_topic(query: str) -> int | None:
    q = query.lower()
    for tid, kws in _TOPIC_KEYWORDS.items():
        if any(kw in q for kw in kws):
            return tid
    return None


def _is_understood(text: str) -> bool:
    t = text.strip().lower()
    return any(t == p or t.startswith(p + " ") for p in _UNDERSTOOD_PHRASES)


def _is_simplify(text: str) -> bool:
    t = text.strip().lower()
    return any(p in t for p in _SIMPLIFY_PHRASES)


def _get_rag_chain():
    if _rag_chain_cache["chain"] is None:
        try:
            from modules.rag import load_vector_store, build_rag_chain
            vs = load_vector_store()
            if vs:
                _rag_chain_cache["chain"] = build_rag_chain(vector_store=vs)
        except Exception:
            pass
    return _rag_chain_cache["chain"]


async def _stream_response(text: str) -> AsyncGenerator[str, None]:
    """Metni kelime kelime SSE formatında akıtar."""
    words = text.split(" ")
    for i, word in enumerate(words):
        chunk = word if i == len(words) - 1 else word + " "
        yield f"data: {json.dumps({'token': chunk})}\n\n"
        await asyncio.sleep(0.02)
    yield f"data: {json.dumps({'done': True})}\n\n"


@router.post("/ask")
async def ask(req: ChatRequest, user: dict = Depends(get_current_user)):
    """
    Soruyu alır, RAG zinciriyle yanıt üretir, SSE stream olarak gönderir.
    Response format: text/event-stream
    Her chunk: data: {"token": "..."}\n\n
    Son chunk:  data: {"done": true, "topic_id": int|null}\n\n
    """
    username = user["username"]
    question = req.question.strip()

    # Konu tespiti: önce req'ten, yoksa keyword ile (log çağrısından önce yapılmalı)
    simplify = _is_simplify(question)
    topic_id = req.topic_id or _detect_topic(question)

    append_chat_log(username, "user", question, topic_id=topic_id)

    # Sokratik manager
    if username not in _socratic_managers:
        _socratic_managers[username] = SocraticManager()
    socratic = _socratic_managers[username]

    # Anladım kontrolü
    if _is_understood(question):
        response = "Harika! Anladığın için sevindim 😊 Başka sorun var mı?"
        append_chat_log(username, "assistant", response, topic_id=topic_id)

        async def stream_understood():
            async for chunk in _stream_response(response):
                yield chunk
            yield f"data: {json.dumps({'done': True, 'topic_id': None, 'understood': True})}\n\n"

        return StreamingResponse(stream_understood(), media_type="text/event-stream")

    topic_name = next((t["name"] for t in CURRICULUM if t["id"] == topic_id), None) if topic_id else None

    # RAG sorgu hazırlama
    if simplify and topic_name:
        rag_query = f"{topic_name} nedir? Tek cümleyle basit tanım."
        suffix = (
            f"Öğrenci anlamadığını belirtti. Sadece '{topic_name} nedir?' sorusunu yanıtla: "
            f"(1) tek cümle tanım, (2) günlük hayattan benzetme, (3) tek satır kod."
        )
    else:
        # Seviye bazlı RAG sorgu zenginleştirmesi
        if topic_name and req.topic_level == "intermediate":
            rag_query = f"{topic_name} ileri kavramlar — {question}"
        elif topic_name and req.topic_level == "advanced":
            rag_query = f"{topic_name} uzmanlık düzeyi — {question}"
        else:
            rag_query = question

        # Sokratik suffix — seviye parametresi ile kalibre edilmiş
        socratic_suffix = (
            socratic.get_socratic_prompt_suffix(topic_name, req.topic_level or "beginner")
            if topic_name else ""
        )

        # Seviye bağlamı: req.topic_level varsa hedefli, yoksa avg mastery'den hesapla
        if req.topic_level and req.topic_level in _LEVEL_PROMPT:
            level_ctx = _LEVEL_PROMPT[req.topic_level]
        else:
            data = load_student_data(username)
            total = len(data["interaction_history"])
            studied = {k: v for k, v in data["student_mastery"].items() if v > 0}
            avg = sum(studied.values()) / len(studied) if studied else 0.0
            level_label = "başlangıç" if avg < 0.4 else ("orta" if avg < 0.65 else "ileri")
            level_ctx = f"Öğrenci genel seviyesi: {level_label} ({total} etkileşim). Buna göre örnekler kullan."

        suffix = f"{socratic_suffix}\n{level_ctx}".strip()

    chain = _get_rag_chain()

    async def generate():
        try:
            if chain:
                from modules.rag import ask as rag_ask
                from modules.rag.chain import build_rag_chain
                vs = _rag_chain_cache.get("vector_store")
                active_chain = (
                    build_rag_chain(vector_store=vs, topic_id=topic_id)
                    if topic_id and vs else chain
                )
                result = rag_ask(active_chain, rag_query, socratic_suffix=suffix)
                response_text = result["answer"]
            else:
                response_text = "📚 Henüz ders notu yüklenmedi. Lütfen öğretmeninize bildirin."

            append_chat_log(username, "assistant", response_text, topic_id=topic_id)

            # Kelime kelime stream
            words = response_text.split(" ")
            for i, word in enumerate(words):
                chunk = word if i == len(words) - 1 else word + " "
                yield f"data: {json.dumps({'token': chunk})}\n\n"
                await asyncio.sleep(0.018)

            yield f"data: {json.dumps({'done': True, 'topic_id': topic_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history/{topic_id}")
def get_topic_history(topic_id: int, user: dict = Depends(get_current_user)):
    """Öğrencinin belirtilen konudaki sohbet geçmişini döner (kronolojik)."""
    from modules.storage import load_topic_chat_history
    messages = load_topic_chat_history(user["username"], topic_id, limit=60)
    return {"messages": messages}


@router.get("/next-topic")
def next_topic(user: dict = Depends(get_current_user)):
    """
    DRL/kural tabanlı politikadan sonraki konu önerisini döner.
    suggest_test: true ise mevcut konuда ara değerlendirme önerisi var demektir.
    """
    data = load_student_data(user["username"])
    mastery = data["student_mastery"]
    policy = RuleBasedPolicy()
    suggestion = policy.select_next_topic(mastery)

    # Önerilen konu için ara değerlendirme gerekli mi?
    topic_name = suggestion.get("topic", {}).get("name")
    suggest_test = policy.should_test(mastery, topic_name) if topic_name else False

    return {**suggestion, "suggest_test": suggest_test}


@router.get("/quiz/{topic_id}")
def get_quiz(topic_id: int, _user: dict = Depends(get_current_user)):
    """Belirtilen konu için 3 soruluk ara değerlendirme soruları döner (cevap dahil değil)."""
    from config.quiz_questions import get_questions_for_topic
    questions = get_questions_for_topic(topic_id)
    if not questions:
        return {"questions": []}
    safe = [
        {"topic_id": topic_id, "text": q["text"], "options": q["options"]}
        for q in questions
    ]
    return {"questions": safe}
