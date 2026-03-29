from fastapi import APIRouter, Depends

from backend.auth import get_current_user
from backend.schemas import MasteryResponse, FeedbackRequest
from modules.storage import load_student_data, save_student_data
from modules.dkt.predict import predict_mastery

router = APIRouter()


@router.get("/me", response_model=MasteryResponse)
def get_my_mastery(user: dict = Depends(get_current_user)):
    """Öğrencinin mevcut mastery skorlarını döner."""
    data = load_student_data(user["username"])
    return MasteryResponse(
        mastery=data["student_mastery"],
        interaction_history=data["interaction_history"],
    )


@router.post("/feedback")
def record_feedback(req: FeedbackRequest, user: dict = Depends(get_current_user)):
    """Doğru/yanlış feedback kaydeder ve mastery'yi günceller."""
    data = load_student_data(user["username"])
    history = data["interaction_history"]

    if req.topic_id is not None:
        history.append({"skill_id": req.topic_id, "correct": req.correct})

    try:
        new_mastery = predict_mastery(interaction_history=history)
    except Exception:
        new_mastery = data["student_mastery"]

    save_student_data(user["username"], history, new_mastery)

    return {"student_mastery": new_mastery, "interaction_history": history}
