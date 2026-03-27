from fastapi import APIRouter, Depends

from backend.auth import require_teacher
from backend.schemas import StudentSummary, LogEntry
from modules.storage import load_all_students, load_chat_log
from config.settings import CURRICULUM

router = APIRouter()


@router.get("/students", response_model=list[StudentSummary])
def get_all_students(teacher: dict = Depends(require_teacher)):
    """Tüm öğrencilerin özet istatistiklerini döner."""
    all_students = load_all_students()
    summaries = []

    for username, data in all_students.items():
        mastery = data.get("student_mastery", {})
        interactions = data.get("interaction_history", [])
        correct = sum(1 for i in interactions if i.get("correct"))
        total = len(interactions)
        avg_m = sum(mastery.values()) / len(mastery) if mastery else 0.0

        summaries.append(StudentSummary(
            username=username,
            interaction_count=total,
            correct_count=correct,
            success_rate=correct / total if total else 0.0,
            avg_mastery=avg_m,
            mastery=mastery,
        ))

    return summaries


@router.get("/logs", response_model=list[LogEntry])
def get_logs(
    last_n: int = 200,
    username: str | None = None,
    role: str | None = None,
    teacher: dict = Depends(require_teacher),
):
    """Sistem sohbet loglarını filtreli döner."""
    logs = load_chat_log(last_n=last_n)

    if username:
        logs = [l for l in logs if l["username"] == username]
    if role:
        logs = [l for l in logs if l["role"] == role]

    return [
        LogEntry(
            timestamp=l.get("timestamp", l.get("ts", "")),
            username=l["username"],
            role=l["role"],
            content=l["content"],
        )
        for l in logs
    ]


@router.get("/curriculum")
def get_curriculum(teacher: dict = Depends(require_teacher)):
    """Müfredat listesini döner."""
    return CURRICULUM
