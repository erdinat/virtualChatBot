"""
Kalıcı Veri Yönetimi

Öğrenci etkileşim geçmişini ve sistem loglarını diske yazar/okur.
Her öğrencinin verisi ayrı bir JSON dosyasında tutulur.

Thread-safety: threading.Lock ile tek process içinde güvenli.
Multi-process senaryosu (çoklu uvicorn worker) için Redis/DB gerekir.
"""

import json
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from config.settings import BASE_DIR

STUDENT_LOGS_DIR = BASE_DIR / "data" / "student_logs"
SYSTEM_LOGS_DIR  = BASE_DIR / "data" / "system_logs"
CHAT_LOG_FILE    = SYSTEM_LOGS_DIR / "chat_log.jsonl"

STUDENT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
SYSTEM_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Per-kullanıcı yazma kilitleri — aynı anda iki istek aynı dosyayı bozmaz
_student_locks: dict[str, threading.Lock] = {}
_student_locks_meta = threading.Lock()

# Chat log yazma kilidi
_chat_log_lock = threading.Lock()


def _get_student_lock(username: str) -> threading.Lock:
    with _student_locks_meta:
        if username not in _student_locks:
            _student_locks[username] = threading.Lock()
        return _student_locks[username]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def save_student_data(username: str, interaction_history: list, student_mastery: dict, **extra):
    """
    Öğrencinin mevcut etkileşim geçmişini ve mastery skorlarını diske yazar.
    Threading lock ile eş zamanlı yazma korunur.
    """
    lock = _get_student_lock(username)
    path = _student_path(username)

    with lock:
        existing: dict = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        data = {
            **existing,
            "interaction_history": interaction_history,
            "student_mastery": student_mastery,
            "last_updated": _now_iso(),
            **extra,
        }
        # Atomik yazma: geçici dosyaya yaz → yeniden adlandır
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)


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

def append_chat_log(username: str, role: str, content: str, topic_id: int | None = None):
    """
    Sohbet mesajını sistem log dosyasına ekler.
    Her satır bir JSON nesnesidir (JSONL formatı).
    topic_id varsa konu bazlı filtreleme için kaydedilir.
    """
    entry = {
        "timestamp": _now_iso(),
        "username": username,
        "role": role,        # "user" veya "assistant"
        "content": content[:500],  # Çok uzun mesajları kırp
    }
    if topic_id is not None:
        entry["topic_id"] = topic_id

    with _chat_log_lock:
        with CHAT_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _iter_lines_reversed(path: Path):
    """
    Büyük dosyaları sondan başa satır satır iter eder.
    load_topic_chat_history için tüm dosyayı belleğe almak yerine
    yalnızca gereken kadar satır okur.
    """
    with path.open("rb") as f:
        f.seek(0, 2)
        remaining = f.tell()
        chunk_size = 8192
        buf = b""
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            remaining -= read_size
            f.seek(remaining)
            chunk = f.read(read_size)
            buf = chunk + buf
            lines = buf.split(b"\n")
            # İlk parça bir önceki chunk'a ait olabilir, tamponda tut
            buf = lines[0]
            for line in reversed(lines[1:]):
                stripped = line.strip()
                if stripped:
                    yield stripped.decode("utf-8", errors="replace")
        if buf.strip():
            yield buf.decode("utf-8", errors="replace")


def load_topic_chat_history(username: str, topic_id: int, limit: int = 60) -> list[dict]:
    """
    Belirli kullanıcının belirli konuya ait son N mesajını kronolojik sırayla döner.
    Dosyayı sondan okur → büyük log dosyalarında verimli.

    Returns: [{"role": str, "content": str, "timestamp": str}, ...]
    """
    if not CHAT_LOG_FILE.exists():
        return []

    collected: deque[dict] = deque()
    for line in _iter_lines_reversed(CHAT_LOG_FILE):
        try:
            e = json.loads(line)
            if e.get("username") == username and e.get("topic_id") == topic_id:
                collected.appendleft({
                    "role": e["role"],
                    "content": e["content"],
                    "timestamp": e["timestamp"],
                })
                if len(collected) >= limit:
                    break
        except json.JSONDecodeError:
            continue

    return list(collected)  # eski → yeni (kronolojik)


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
