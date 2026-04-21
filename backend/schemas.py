"""Pydantic şemaları — request / response modelleri."""

from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, Field


# ── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    name: str
    role: str


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str          # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    chat_history: List[ChatMessage] = Field(default=[], max_length=50)
    topic_id: Optional[int] = Field(default=None, ge=1, le=10)
    topic_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None


class FeedbackRequest(BaseModel):
    topic_id: Optional[int] = Field(default=None, ge=1, le=10)
    correct: bool


# ── Mastery ──────────────────────────────────────────────────────────────────

class InteractionItem(BaseModel):
    skill_id: int
    correct: bool


class MasteryResponse(BaseModel):
    mastery: Dict[str, float]
    interaction_history: List[InteractionItem]


# ── Teacher ──────────────────────────────────────────────────────────────────

class StudentSummary(BaseModel):
    username: str
    interaction_count: int
    correct_count: int
    success_rate: float
    avg_mastery: float
    mastery: Dict[str, float]


class LogEntry(BaseModel):
    timestamp: str
    username: str
    role: str
    content: str


# ── Diagnostic ───────────────────────────────────────────────────────────────

class DiagnosticSubmitRequest(BaseModel):
    """POST /api/diagnostic/submit — sınav cevapları (topic_id str → seçilen şık harfi)."""
    answers: Dict[str, str] = Field(
        ...,
        description="topic_id (str) → seçilen şık ('A'|'B'|'C'|'D')",
    )


class TopicLevelRequest(BaseModel):
    """POST /api/diagnostic/topic-level — konu ön testi cevapları."""
    topic_id: int = Field(..., ge=1, le=10)
    answers: Dict[str, int] = Field(
        ...,
        description="soru_idx (str) → seçilen option indeksi (0–3)",
    )


# ── Quiz Generation ──────────────────────────────────────────────────────────

class GenerateQuizRequest(BaseModel):
    """POST /api/chat/generate-quiz — LLM ile seviye ve sohbet bağlamına özel soru üretir."""
    topic_id: int = Field(..., ge=1, le=10)
    level: Literal["beginner", "intermediate", "advanced"]
    chat_history: List[ChatMessage] = Field(default=[], max_length=50)


# ── PDFs ─────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    message: str
    files_processed: int
    chunks_created: int
