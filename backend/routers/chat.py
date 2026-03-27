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
_rag_chain_cache: dict = {"chain": None}

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

    append_chat_log(username, "user", question)

    # Sokratik manager
    if username not in _socratic_managers:
        _socratic_managers[username] = SocraticManager()
    socratic = _socratic_managers[username]

    # Anladım kontrolü
    if _is_understood(question):
        response = "Harika! Anladığın için sevindim 😊 Başka sorun var mı?"
        append_chat_log(username, "assistant", response)

        async def stream_understood():
            async for chunk in _stream_response(response):
                yield chunk
            yield f"data: {json.dumps({'done': True, 'topic_id': None, 'understood': True})}\n\n"

        return StreamingResponse(stream_understood(), media_type="text/event-stream")

    # Konu tespiti
    simplify = _is_simplify(question)
    topic_id = _detect_topic(question)
    topic_name = next((t["name"] for t in CURRICULUM if t["id"] == topic_id), None) if topic_id else None

    # RAG sorgu hazırlama
    if simplify and topic_name:
        rag_query = f"{topic_name} nedir? Tek cümleyle basit tanım."
        suffix = (
            f"Öğrenci anlamadığını belirtti. Sadece '{topic_name} nedir?' sorusunu yanıtla: "
            f"(1) tek cümle tanım, (2) günlük hayattan benzetme, (3) tek satır kod."
        )
    else:
        rag_query = question
        socratic_suffix = socratic.get_socratic_prompt_suffix(topic_name) if topic_name else ""
        data = load_student_data(username)
        total = len(data["interaction_history"])
        studied = {k: v for k, v in data["student_mastery"].items() if v > 0}
        avg = sum(studied.values()) / len(studied) if studied else 0.0
        level = "başlangıç" if avg < 0.4 else ("orta" if avg < 0.65 else "ileri")
        level_ctx = f"Öğrenci seviyesi: {level} ({total} etkileşim). Buna göre örnekler kullan."
        suffix = f"{socratic_suffix}\n{level_ctx}".strip()

    chain = _get_rag_chain()

    async def generate():
        try:
            if chain:
                from modules.rag import ask as rag_ask
                result = rag_ask(chain, rag_query, socratic_suffix=suffix)
                response_text = result["answer"]
            else:
                response_text = "📚 Henüz ders notu yüklenmedi. Lütfen öğretmeninize bildirin."

            append_chat_log(username, "assistant", response_text)

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


@router.get("/next-topic")
def next_topic(user: dict = Depends(get_current_user)):
    """DRL politikasından bir sonraki konu önerisini döner."""
    data = load_student_data(user["username"])
    policy = RuleBasedPolicy()
    suggestion = policy.select_next_topic(data["student_mastery"])
    return suggestion
