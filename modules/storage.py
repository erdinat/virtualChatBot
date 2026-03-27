"""
Kalıcı Veri Yönetimi

Öğrenci etkileşim geçmişini ve sistem loglarını diske yazar/okur.
Her öğrencinin verisi ayrı bir JSON dosyasında tutulur.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from config.settings import BASE_DIR

STUDENT_LOGS_DIR = BASE_DIR / "data" / "student_logs"
SYSTEM_LOGS_DIR  = BASE_DIR / "data" / "system_logs"
CHAT_LOG_FILE    = SYSTEM_LOGS_DIR / "chat_log.jsonl"

STUDENT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
SYSTEM_LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ── Öğrenci Verisi ──────────────────────────────────────────────────────────

def _student_path(username: str) -> Path:
    return STUDENT_LOGS_DIR / f"{username}.json"


def load_student_data(username: str) -> dict:
    """
    Öğrencinin kaydedilmiş verilerini yükler.
    Dosya yoksa temiz başlangıç verisi döner.
    """
    path = _student_path(username)
    if not path.exists():
        return {"interaction_history": [], "student_mastery": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"interaction_history": [], "student_mastery": {}}


def save_student_data(username: str, interaction_history: list, student_mastery: dict):
    """Öğrencinin mevcut etkileşim geçmişini ve mastery skorlarını diske yazar."""
    data = {
        "interaction_history": interaction_history,
        "student_mastery": student_mastery,
        "last_updated": datetime.now().isoformat(),
    }
    _student_path(username).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_all_students() -> Dict[str, dict]:
    """
    Tüm öğrencilerin verilerini yükler (öğretmen analitiği için).

    Returns:
        {"ali": {"interaction_history": [...], "student_mastery": {...}}, ...}
    """
    result = {}
    for path in sorted(STUDENT_LOGS_DIR.glob("*.json")):
        username = path.stem
        try:
            result[username] = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
    return result


# ── Sistem Logları ───────────────────────────────────────────────────────────

def append_chat_log(username: str, role: str, content: str):
    """
    Sohbet mesajını sistem log dosyasına ekler.
    Her satır bir JSON nesnesidir (JSONL formatı).
    """
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "username": username,
        "role": role,        # "user" veya "assistant"
        "content": content[:500],  # Çok uzun mesajları kırp
    }
    with CHAT_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_chat_log(last_n: int = 100) -> List[dict]:
    """Son N sohbet kaydını döner (öğretmen için)."""
    if not CHAT_LOG_FILE.exists():
        return []
    lines = CHAT_LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in lines[-last_n:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(entries))  # En yenisi üstte
