"""
Seviye Tespit Sınavı (Diagnostic Test)

Yeni öğrencinin ilk girişinde bilgi seviyesini belirleyen 10 soruluk sınav.
Sonuçlara göre DKT başlangıç mastery vektörü hesaplanır.
"""

import logging

from fastapi import APIRouter, Depends

from backend.auth import get_current_user
from backend.schemas import DiagnosticSubmitRequest, TopicLevelRequest
from modules.storage import load_student_data, save_student_data
from config.quiz_questions import (
    get_diagnostic_questions,
    get_pretest_questions,
)
from config.settings import CURRICULUM

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/questions")
def get_diagnostic_test(user: dict = Depends(get_current_user)):
    """
    Seviye tespit sınavı sorularını döndürür (10 soru, her konudan 1).
    Sınav daha önce tamamlandıysa 'already_done: true' döner.
    """
    data = load_student_data(user["username"])

    if data.get("diagnostic_done"):
        return {"already_done": True, "questions": []}

    questions = get_diagnostic_questions()
    # Cevabı istemciye göndermiyoruz — sadece soru metni ve şıklar
    safe = [
        {"topic_id": q["topic_id"], "text": q["text"], "options": q["options"]}
        for q in questions
    ]
    return {"already_done": False, "questions": safe}


@router.post("/submit")
def submit_diagnostic(payload: DiagnosticSubmitRequest, user: dict = Depends(get_current_user)):
    """
    Sınav cevaplarını alır, başlangıç mastery hesaplar ve kaydeder.

    payload: {"answers": {"1": "B", "2": "A", ...}}  (topic_id → seçilen şık)
    """
    answers: dict = payload.answers
    reference = get_diagnostic_questions()

    # Doğru/yanlış kontrolü
    topic_correct: dict[int, bool] = {}
    for q in reference:
        tid = q["topic_id"]
        topic_correct[tid] = answers.get(str(tid), "").upper() == q["answer"].upper()

    # Doğru → 0.55 başlangıç mastery, yanlış → 0.0
    # Yanlış cevap "hiç bilmiyor" demek; öğrenci o konuyu görünce sıfırdan başlamalı.
    # 0.15 yerine 0.0 kullanmak öğretmen ekranıyla öğrenci ekranını tutarlı tutar.
    initial_mastery = {
        topic["name"]: (0.55 if topic_correct.get(topic["id"], False) else 0.0)
        for topic in CURRICULUM
    }

    # Sınav etkileşimlerini kaydet (DKT için input)
    interactions = [
        {"skill_id": tid, "correct": correct}
        for tid, correct in topic_correct.items()
    ]

    data = load_student_data(user["username"])
    history = interactions + data.get("interaction_history", [])

    save_student_data(
        user["username"], history, initial_mastery, diagnostic_done=True
    )

    score = sum(1 for v in topic_correct.values() if v)
    return {
        "score": score,
        "total": len(reference),
        "initial_mastery": initial_mastery,
        "message": f"{score}/{len(reference)} doğru — başlangıç seviyeniz belirlendi!",
    }


# Bir zorluk dilimini "geçti" sayma eşiği: o dilimdeki soruların ≥%60'ı doğru.
# 4 beginner için en az 3, 3 intermediate/advanced için en az 2 doğru gerekir.
_TIER_PASS_RATIO = 0.6


@router.get("/pretest/{topic_id}")
def get_pretest(topic_id: int, _user: dict = Depends(get_current_user)):
    """
    Ön test için 10 soruyu kademeli zorluk sırasıyla döner (4 kolay + 3 orta + 3 zor).
    Cevaplar istemciye gönderilmez; değerlendirme /topic-level üzerinden yapılır.
    """
    questions = get_pretest_questions(topic_id)
    safe = [
        {
            "topic_id": topic_id,
            "text": q["text"],
            "options": q["options"],
            "difficulty": q.get("difficulty", "beginner"),
        }
        for q in questions
    ]
    return {"questions": safe}


@router.post("/topic-level")
def assess_topic_level(payload: TopicLevelRequest, _user: dict = Depends(get_current_user)):
    """
    Konu bazlı ön test cevaplarını değerlendirir, seviye döner.

    Kademeli skorlama:
      - Beginner dilimi geçilmediyse → 'beginner'
      - Beginner geçildi ama intermediate geçilmediyse → 'beginner'
        (temeli var ama orta seviyeye hazır değil)
      - Beginner + intermediate geçildi, advanced geçilmediyse → 'intermediate'
      - Üç dilim de geçildi → 'advanced'

    Bir dilim "geçildi" = o dilimdeki soruların ≥%60'ı doğru.

    payload: {"topic_id": int, "answers": {"0": 2, "1": 0, ...}}
             (soru_idx (str) → seçilen option indeksi (int))

    Returns: {
      "score": int, "total": int, "level": str,
      "tier_breakdown": {"beginner": [correct, total], ...}
    }
    """
    topic_id: int = payload.topic_id
    answers: dict = payload.answers
    # Ön test sıralamasıyla aynı: soru indeksleri kademeli zorluğa göre
    questions = get_pretest_questions(topic_id)
    letters = ["A", "B", "C", "D"]

    def _is_correct(i: int, q: dict) -> bool:
        opt = answers.get(str(i))
        if opt is None:
            return False
        try:
            idx = int(opt)
        except (TypeError, ValueError):
            return False
        return 0 <= idx < len(letters) and letters[idx] == q["answer"].upper()

    # Her zorluk dilimi için correct/total ayrı topla
    tier_score: dict[str, list[int]] = {
        "beginner":     [0, 0],
        "intermediate": [0, 0],
        "advanced":     [0, 0],
    }
    for i, q in enumerate(questions):
        diff = q.get("difficulty", "beginner")
        if diff not in tier_score:
            diff = "beginner"
        tier_score[diff][1] += 1
        if _is_correct(i, q):
            tier_score[diff][0] += 1

    def _passed(tier: str) -> bool:
        correct, total = tier_score[tier]
        if total == 0:
            # O seviyede soru yoksa geçilmiş say (geriye uyumluluk)
            return True
        return (correct / total) >= _TIER_PASS_RATIO

    if _passed("beginner") and _passed("intermediate") and _passed("advanced"):
        level = "advanced"
    elif _passed("beginner") and _passed("intermediate"):
        level = "intermediate"
    else:
        level = "beginner"

    total_correct = sum(s[0] for s in tier_score.values())
    total_count = sum(s[1] for s in tier_score.values())

    return {
        "score": total_correct,
        "total": total_count,
        "level": level,
        "tier_breakdown": {k: {"correct": v[0], "total": v[1]} for k, v in tier_score.items()},
    }
