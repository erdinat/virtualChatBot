"""
DKT – Tahmin ve Bilgi Seviyesi Analizi

Eğitilmiş DKT modeli ile öğrencinin anlık bilgi seviyesini tahmin eder.
"""

import torch
from typing import List, Dict

from config.settings import CURRICULUM
from modules.dkt.model import DKTModel


def predict_mastery(
    model: DKTModel,
    interaction_history: List[dict],
) -> Dict[str, float]:
    """
    Öğrencinin etkileşim geçmişinden bilgi seviyesini tahmin eder.

    Args:
        model: Eğitilmiş DKTModel
        interaction_history: [{"skill_id": int, "correct": bool}, ...]

    Returns:
        {"Değişkenler ve Veri Tipleri": 0.85, "Döngüler": 0.42, ...}
    """
    if not interaction_history:
        # Geçmiş yoksa nötr olasılıklar döndür
        return {topic["name"]: 0.5 for topic in CURRICULUM}

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
