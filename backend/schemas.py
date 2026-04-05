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


# ── PDFs ─────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    message: str
    files_processed: int
    chunks_created: int
