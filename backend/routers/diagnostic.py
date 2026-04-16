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
from config.quiz_questions import get_diagnostic_questions, get_questions_for_topic
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

    # Doğru → 0.55 başlangıç mastery, yanlış → 0.15
    initial_mastery = {
        topic["name"]: (0.55 if topic_correct.get(topic["id"], False) else 0.15)
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


@router.post("/topic-level")
def assess_topic_level(payload: TopicLevelRequest, _user: dict = Depends(get_current_user)):
    """
    Konu bazlı ön test cevaplarını değerlendirir, seviye döner.

    payload: {"topic_id": int, "answers": {"0": 2, "1": 0, "2": 3}}
             (soru_idx (str) → seçilen option indeksi (int))

    Returns: {"score": int, "total": int, "level": "beginner"|"intermediate"|"advanced"}
    """
    topic_id: int = payload.topic_id
    answers: dict = payload.answers
    questions = get_questions_for_topic(topic_id)
    letters = ["A", "B", "C", "D"]

    correct = sum(
        1 for i, q in enumerate(questions)
        if (opt := answers.get(str(i))) is not None
        and 0 <= int(opt) < len(letters)
        and letters[int(opt)] == q["answer"].upper()
    )
    total = len(questions)

    if correct == total:
        level = "advanced"
    elif correct >= max(1, total // 2):
        level = "intermediate"
    else:
        level = "beginner"

    return {"score": correct, "total": total, "level": level}
