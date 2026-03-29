"""
DKT – Tahmin ve Bilgi Seviyesi Analizi

Eğitilmiş DKT modeli ile öğrencinin anlık bilgi seviyesini tahmin eder.
Model yoksa kural tabanlı fallback kullanılır.
"""

import torch
from typing import List, Dict, Optional

from config.settings import CURRICULUM, DKTConfig
from modules.dkt.model import DKTModel

# Modeli bir kez yükle, sonraki çağrılarda cache'den kullan
_cached_model: Optional[DKTModel] = None


def _load_model_if_exists() -> Optional[DKTModel]:
    """
    models/dkt_model.pt varsa yükler, yoksa None döner.
    İlk çağrıdan sonra sonucu cache'ler (her soru sonrası disk I/O olmaz).
    """
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    path = DKTConfig.MODEL_SAVE_PATH
    if not path.exists():
        return None

    try:
        model = DKTModel(num_skills=len(CURRICULUM))
        model.load_state_dict(torch.load(path, weights_only=True))
        model.eval()
        _cached_model = model
        print(f"✅ DKT LSTM modeli yüklendi: {path}")
        return model
    except Exception as e:
        print(f"⚠️  DKT modeli yüklenemedi ({e}), kural tabanlı fallback kullanılıyor.")
        return None


def _rule_based_mastery(interaction_history: List[dict]) -> Dict[str, float]:
    """
    LSTM modeli olmadan kural tabanlı mastery hesabı.

    Her doğru cevap +0.05, her yanlış cevap -0.04 (başlangıç: 0.0).
    Yaklaşık 14 doğru cevap → yetkinlik (0.7).
    """
    mastery = {topic["name"]: 0.0 for topic in CURRICULUM}
    topic_id_to_name = {topic["id"]: topic["name"] for topic in CURRICULUM}

    for interaction in interaction_history:
        skill_id = interaction["skill_id"]
        correct = interaction["correct"]
        name = topic_id_to_name.get(skill_id)
        if name is None:
            continue
        if correct:
            mastery[name] = min(1.0, mastery[name] + 0.05)
        else:
            mastery[name] = max(0.0, mastery[name] - 0.04)

    return {k: round(v, 3) for k, v in mastery.items()}


def predict_mastery(
    interaction_history: List[dict],
    model: Optional[DKTModel] = None,
) -> Dict[str, float]:
    """
    Öğrencinin etkileşim geçmişinden bilgi seviyesini tahmin eder.

    Öncelik sırası:
      1. Parametre olarak verilen model
      2. Diskteki eğitilmiş model (models/dkt_model.pt)
      3. Kural tabanlı fallback

    Args:
        interaction_history: [{"skill_id": int, "correct": bool}, ...]
        model: Eğitilmiş DKTModel (None ise otomatik yüklenmeye çalışılır)

    Returns:
        {"Değişkenler ve Veri Tipleri": 0.85, "Döngüler": 0.42, ...}
    """
    if not interaction_history:
        return {topic["name"]: 0.0 for topic in CURRICULUM}

    # DKT modeli az veriyle güvenilir tahmin üretemez; yeterli etkileşim yoksa
    # kural tabanlı yöntemi kullan (sadece etkileşilen konuyu günceller).
    MIN_INTERACTIONS = 10
    if len(interaction_history) < MIN_INTERACTIONS:
        return _rule_based_mastery(interaction_history)

    if model is None:
        model = _load_model_if_exists()

    if model is None:
        return _rule_based_mastery(interaction_history)

    num_skills = len(CURRICULUM)

    # Etkileşim dizisini one-hot encode'a çevir
    seq_len = len(interaction_history)
    input_tensor = torch.zeros(1, seq_len, num_skills * 2)

    for t, interaction in enumerate(interaction_history):
        skill_id = interaction["skill_id"] - 1  # 0-indexed
        correct = interaction["correct"]

        if correct:
            input_tensor[0, t, skill_id] = 1.0
        else:
            input_tensor[0, t, num_skills + skill_id] = 1.0

    # Tahmin
    mastery_probs = model.predict_mastery(input_tensor)  # (1, num_skills)
    mastery_probs = mastery_probs.squeeze(0)  # (num_skills,)

    # Sonuçları isimlendirerek döndür
    result = {}
    for i, topic in enumerate(CURRICULUM):
        result[topic["name"]] = round(mastery_probs[i].item(), 3)

    return result


def get_weak_topics(mastery: Dict[str, float], threshold: float = 0.5) -> List[str]:
    """Öğrencinin zayıf olduğu konuları döndürür."""
    return [topic for topic, score in mastery.items() if score < threshold]


def get_strong_topics(mastery: Dict[str, float], threshold: float = 0.7) -> List[str]:
    """Öğrencinin güçlü olduğu konuları döndürür."""
    return [topic for topic, score in mastery.items() if score >= threshold]
