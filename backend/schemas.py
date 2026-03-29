"""Pydantic şemaları — request / response modelleri."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


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
    question: str
    chat_history: List[ChatMessage] = []
    topic_id: Optional[int] = None      # Seçilen konu (müfredat kartından)
    topic_level: Optional[str] = None   # "beginner" | "intermediate" | "advanced"


class FeedbackRequest(BaseModel):
    topic_id: Optional[int] = None
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
