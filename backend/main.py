"""
Sanal Öğretmen Asistanı — FastAPI Backend
Çalıştırmak için: uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import auth, chat, mastery, teacher, pdfs
from backend.routers import diagnostic

app = FastAPI(
    title="Sanal Öğretmen Asistanı API",
    description="RAG + DKT + DRL tabanlı adaptif öğrenme platformu",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth.router,    prefix="/api/auth",    tags=["Auth"])
app.include_router(chat.router,    prefix="/api/chat",    tags=["Chat"])
app.include_router(mastery.router, prefix="/api/mastery", tags=["Mastery"])
app.include_router(teacher.router, prefix="/api/teacher", tags=["Teacher"])
app.include_router(pdfs.router,        prefix="/api/pdfs",       tags=["PDFs"])
app.include_router(diagnostic.router,  prefix="/api/diagnostic", tags=["Diagnostic"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}
