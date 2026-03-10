"""
Sanal Öğretmen Asistanı – Merkezi Konfigürasyon

Tüm ortam değişkenlerini ve sistem ayarlarını tek bir yerden yönetir.
.env dosyasından değerleri okur ve modüller arası paylaşır.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Proje kök dizini
BASE_DIR = Path(__file__).resolve().parent.parent

# .env dosyasını yükle
load_dotenv(BASE_DIR / ".env")


# ===== LLM Ayarları =====
class LLMConfig:
    API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "deepseek-chat")
    TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))


# ===== RAG Ayarları =====
class RAGConfig:
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    TOP_K: int = int(os.getenv("RETRIEVER_TOP_K", "4"))
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    VECTOR_STORE_PATH: Path = BASE_DIR / os.getenv(
        "VECTOR_STORE_PATH", "data/vector_store"
    )
    RAW_PDFS_PATH: Path = BASE_DIR / "data" / "raw_pdfs"


# ===== DKT Ayarları =====
class DKTConfig:
    HIDDEN_DIM: int = 128
    NUM_LAYERS: int = 1
    DROPOUT: float = 0.2
    LEARNING_RATE: float = 0.001
    EPOCHS: int = 50
    BATCH_SIZE: int = 32
    MODEL_SAVE_PATH: Path = BASE_DIR / "models" / "dkt_model.pt"


# ===== DRL Ayarları =====
class DRLConfig:
    GAMMA: float = 0.99          # İndirim faktörü
    EPSILON_START: float = 1.0   # Başlangıç keşif oranı
    EPSILON_END: float = 0.01    # Minimum keşif oranı
    EPSILON_DECAY: float = 0.995 # Keşif azalma hızı
    LEARNING_RATE: float = 0.001
    MEMORY_SIZE: int = 10000
    BATCH_SIZE: int = 64
    TARGET_UPDATE: int = 10      # Her N episode'da hedef ağ güncelle
    MODEL_SAVE_PATH: Path = BASE_DIR / "models" / "drl_agent.pt"


# ===== Müfredat Tanımı =====
CURRICULUM = [
    {"id": 1, "name": "Değişkenler ve Veri Tipleri", "difficulty": 1},
    {"id": 2, "name": "Operatörler ve İfadeler", "difficulty": 1},
    {"id": 3, "name": "Koşul İfadeleri (if/elif/else)", "difficulty": 2},
    {"id": 4, "name": "Döngüler (for/while)", "difficulty": 2},
    {"id": 5, "name": "Listeler ve Tuple'lar", "difficulty": 3},
    {"id": 6, "name": "Sözlükler ve Kümeler", "difficulty": 3},
    {"id": 7, "name": "Fonksiyonlar", "difficulty": 4},
    {"id": 8, "name": "Dosya İşlemleri", "difficulty": 4},
    {"id": 9, "name": "Hata Yönetimi (try/except)", "difficulty": 5},
    {"id": 10, "name": "Nesne Yönelimli Programlama (OOP)", "difficulty": 5},
]

# ===== Uygulama Ayarları =====
class AppConfig:
    TITLE: str = os.getenv("APP_TITLE", "Sanal Öğretmen Asistanı")
    LANGUAGE: str = os.getenv("APP_LANGUAGE", "tr")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"
