"""
DRL – Öğrenme Ortamı (Environment)

Adaptif içerik sıralama için RL ortamı.
Durum: DKT bilgi vektörü, Aksiyon: konu seçimi, Ödül: başarı.

Referans: Pu ve diğ. (2020)
"""

import numpy as np
from typing import Tuple, Optional
from config.settings import CURRICULUM


class LearningEnvironment:
    """
    Öğrenci öğrenme sürecini simüle eden RL ortamı.

    State:  Öğrencinin her konudaki bilgi seviyesi (num_skills,)
    Action: Gösterilecek konu indeksi
    Reward: +1 başarılı, -1 başarısız
    """

    def __init__(self, num_skills: int = None):
        self.num_skills = num_skills or len(CURRICULUM)
        self.state = None
        self.current_topic = 0
        self.steps = 0
        self.max_steps = 50

    def reset(self, initial_mastery: Optional[np.ndarray] = None) -> np.ndarray:
        """Ortamı sıfırlar ve başlangıç durumunu döndürür."""
        if initial_mastery is not None:
            self.state = initial_mastery.copy()
        else:
            # Rastgele başlangıç seviyesi (0.2-0.5 arası)
            self.state = np.random.uniform(0.2, 0.5, self.num_skills)

        self.current_topic = 0
        self.steps = 0
        return self.state.copy()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Aksiyonu uygular ve yeni durumu döndürür.

        Args:
            action: Gösterilecek konu indeksi (0-indexed)

        Returns:
            (next_state, reward, done, info)
        """
        self.steps += 1

        # Öğrencinin başarı olasılığı – mevcut bilgi seviyesine bağlı
        success_prob = self.state[action]
        success = np.random.random() < success_prob

        # Ödül
        if success:
            reward = 1.0
            # Başarılıysa bilgi seviyesi artar
            self.state[action] = min(1.0, self.state[action] + 0.1)
        else:
            reward = -0.5
            # Başarısızsa küçük düşüş
            self.state[action] = max(0.0, self.state[action] - 0.02)

        # Bitiş koşulu
        done = (
            self.steps >= self.max_steps
            or np.all(self.state >= 0.8)  # Tüm konularda yetkin
        )

        info = {
            "success": success,
            "topic": CURRICULUM[action]["name"] if action < len(CURRICULUM) else f"Konu {action}",
            "mastery": self.state.copy(),
        }

        return self.state.copy(), reward, done, info

    @property
    def state_dim(self) -> int:
        return self.num_skills

    @property
    def action_dim(self) -> int:
        return self.num_skills
