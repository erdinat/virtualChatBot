"""
DRL – Kural Tabanlı Politika (Fallback)

DRL modeli henüz eğitilmemişken kullanılacak basit karar ağacı.
Öğrencinin bilgi seviyesine göre deterministik konu önerisi yapar.
"""

import numpy as np
from typing import Dict, List
from config.settings import CURRICULUM


class RuleBasedPolicy:
    """
    Basit kural tabanlı adaptif içerik sıralama politikası.

    Mantık:
    - En zayıf konuyu bul → tekrar ettir
    - Tüm konularda yetkin → sonraki zorluk seviyesine geç
    - Yetkinlik eşiği: 0.7
    """

    def __init__(self, mastery_threshold: float = 0.7):
        self.mastery_threshold = mastery_threshold

    def select_next_topic(self, mastery: Dict[str, float]) -> dict:
        """
        Öğrencinin bilgi seviyesine göre sonraki konuyu seçer.

        Args:
            mastery: {"Konu Adı": P(correct), ...}

        Returns:
            {"action": "review"|"advance", "topic": {...}, "reason": str}
        """
        # Konuları zorluk sırasına göre sırala
        sorted_topics = sorted(CURRICULUM, key=lambda t: t["difficulty"])

        for topic in sorted_topics:
            topic_name = topic["name"]
            score = mastery.get(topic_name, 0.5)

            if score < self.mastery_threshold:
                return {
                    "action": "review",
                    "topic": topic,
                    "reason": f"'{topic_name}' konusunda bilgi seviyeniz düşük "
                              f"({score:.0%}). Bu konuyu tekrar etmenizi öneriyorum.",
                }

        # Tüm konularda yetkinse
        return {
            "action": "advance",
            "topic": sorted_topics[-1],
            "reason": "Tebrikler! Tüm konularda yeterli seviyedesiniz. "
                      "İleri düzey alıştırmalara geçebilirsiniz.",
        }

    def should_test(self, mastery: Dict[str, float], current_topic_name: str) -> bool:
        """Mevcut konu için ara sınav yapılmalı mı?"""
        score = mastery.get(current_topic_name, 0.5)
        # Seviye 0.4-0.7 arasındaysa test yap (çok düşükse önce anlat)
        return 0.4 <= score < self.mastery_threshold

    def get_difficulty_level(self, mastery: Dict[str, float]) -> str:
        """Öğrencinin genel seviyesini belirler."""
        avg_mastery = np.mean(list(mastery.values()))
        if avg_mastery < 0.3:
            return "başlangıç"
        elif avg_mastery < 0.6:
            return "orta"
        else:
            return "ileri"
