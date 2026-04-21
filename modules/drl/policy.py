"""
DRL – Kural Tabanlı Politika (Fallback)

DRL modeli henüz eğitilmemişken kullanılacak basit karar ağacı.
Öğrencinin bilgi seviyesine göre deterministik konu önerisi yapar.
"""

import logging

import numpy as np
from typing import Dict
from config.settings import CURRICULUM, DRLConfig

logger = logging.getLogger(__name__)


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

        Müfredat sırasına (ID) göre ilerler: önce 1'i tamamla, sonra 2, sonra 3...
        Difficulty sıralaması kullanılmaz — pedagojik olarak yanlış önerilere yol açar.

        Args:
            mastery: {"Konu Adı": P(correct), ...}

        Returns:
            {"action": "review"|"advance", "topic": {...}, "reason": str}
        """
        # Müfredat sırasına göre (ID ascending) tara
        sorted_topics = sorted(CURRICULUM, key=lambda t: t["id"])

        for topic in sorted_topics:
            topic_name = topic["name"]
            score = mastery.get(topic_name, 0.0)

            if score < self.mastery_threshold:
                return {
                    "action": "review",
                    "topic": topic,
                    "reason": f"'{topic_name}' konusunu çalışmaya devam et "
                              f"(hakimiyet: {score:.0%}).",
                }

        # Tüm konularda yetkinse
        return {
            "action": "advance",
            "topic": sorted_topics[-1],
            "reason": "Tebrikler! Tüm konuları tamamladın.",
        }

    def should_test(self, mastery: Dict[str, float], current_topic_name: str) -> bool:
        """Mevcut konu için ara sınav yapılmalı mı?"""
        score = mastery.get(current_topic_name, 0.0)
        # Seviye 0.4-0.7 arasındaysa test öner (çok düşükse önce anlat)
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


class DQNPolicy:
    """
    Eğitilmiş DQN ajanını kullanan adaptif içerik sıralama politikası.

    models/drl_agent.pt dosyası mevcutsa kullanılır; yoksa get_policy()
    otomatik olarak RuleBasedPolicy'ye döner.
    """

    def __init__(self):
        from modules.drl.agent import DQNAgent
        from modules.drl.environment import LearningEnvironment

        env = LearningEnvironment()
        self.agent = DQNAgent(state_dim=env.state_dim, action_dim=env.action_dim)
        self.agent.load(str(DRLConfig.MODEL_SAVE_PATH))
        self.agent.epsilon = 0.0  # Inference: keşif yok, sadece en iyi aksiyon
        self._fallback = RuleBasedPolicy()

    def _mastery_to_state(self, mastery: Dict[str, float]) -> np.ndarray:
        """Mastery dict'ini DQN için sıralı numpy vektörüne dönüştürür."""
        return np.array(
            [mastery.get(t["name"], 0.5) for t in CURRICULUM],
            dtype=np.float32,
        )

    def select_next_topic(self, mastery: Dict[str, float]) -> dict:
        state = self._mastery_to_state(mastery)
        action = self.agent.select_action(state)  # 0-9 arası konu indeksi
        topic = CURRICULUM[action]
        return {
            "action": "dqn",
            "topic": topic,
            "reason": (
                f"DQN politikası mevcut durumunda "
                f"'{topic['name']}' konusunu çalışmanı öneriyor."
            ),
        }

    def should_test(self, mastery: Dict[str, float], current_topic_name: str) -> bool:
        return self._fallback.should_test(mastery, current_topic_name)


def get_policy(mastery_threshold: float = 0.7) -> RuleBasedPolicy | DQNPolicy:
    """
    Eğitilmiş DQN modeli varsa DQNPolicy, yoksa RuleBasedPolicy döner.

    Bu factory fonksiyon sayesinde chat.py model dosyasını bilmek zorunda kalmaz;
    modeli eğitip models/ klasörüne bırakmak yeterli.
    """
    if DRLConfig.MODEL_SAVE_PATH.exists():
        try:
            return DQNPolicy()
        except Exception as e:
            logger.warning("DQN yüklenemedi, kural tabanlı fallback kullanılıyor: %s", e)
    return RuleBasedPolicy(mastery_threshold)
