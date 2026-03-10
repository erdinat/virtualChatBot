"""
DRL – DQN Ajanı

Deep Q-Network ile adaptif içerik sıralama kararları verir.
Epsilon-greedy keşif stratejisi kullanır.
"""

import random
from collections import deque
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from config.settings import DRLConfig


class QNetwork(nn.Module):
    """Q-değer tahmini yapan sinir ağı."""

    def __init__(self, state_dim: int, action_dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class DQNAgent:
    """
    DQN tabanlı adaptif içerik sıralama ajanı.

    - Epsilon-greedy keşif stratejisi
    - Experience replay buffer
    - Target network ile kararlı eğitim
    """

    def __init__(self, state_dim: int, action_dim: int):
        self.state_dim = state_dim
        self.action_dim = action_dim

        # Ağlar
        self.q_network = QNetwork(state_dim, action_dim)
        self.target_network = QNetwork(state_dim, action_dim)
        self.target_network.load_state_dict(self.q_network.state_dict())

        # Optimizer
        self.optimizer = optim.Adam(
            self.q_network.parameters(), lr=DRLConfig.LEARNING_RATE
        )

        # Deneyim tekrar tamponu
        self.memory = deque(maxlen=DRLConfig.MEMORY_SIZE)

        # Keşif parametreleri
        self.epsilon = DRLConfig.EPSILON_START
        self.epsilon_end = DRLConfig.EPSILON_END
        self.epsilon_decay = DRLConfig.EPSILON_DECAY

        # Hiperparametreler
        self.gamma = DRLConfig.GAMMA
        self.batch_size = DRLConfig.BATCH_SIZE

    def select_action(self, state: np.ndarray) -> int:
        """Epsilon-greedy aksiyon seçimi."""
        if random.random() < self.epsilon:
            return random.randrange(self.action_dim)

        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            q_values = self.q_network(state_tensor)
        return q_values.argmax(dim=1).item()

    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        """Geçişi deneyim tamponuna ekler."""
        self.memory.append((state, action, reward, next_state, done))

    def train_step(self) -> float:
        """Bir mini-batch üzerinde eğitim adımı yapar."""
        if len(self.memory) < self.batch_size:
            return 0.0

        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions).unsqueeze(1)
        rewards = torch.FloatTensor(rewards).unsqueeze(1)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones).unsqueeze(1)

        # Mevcut Q-değerleri
        current_q = self.q_network(states).gather(1, actions)

        # Hedef Q-değerleri
        with torch.no_grad():
            next_q = self.target_network(next_states).max(1, keepdim=True)[0]
            target_q = rewards + self.gamma * next_q * (1 - dones)

        # Kayıp ve güncelleme
        loss = nn.MSELoss()(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Epsilon azalt
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return loss.item()

    def update_target_network(self):
        """Hedef ağı günceller."""
        self.target_network.load_state_dict(self.q_network.state_dict())

    def save(self, path: str = None):
        """Ajanı kaydeder."""
        path = path or str(DRLConfig.MODEL_SAVE_PATH)
        torch.save({
            "q_network": self.q_network.state_dict(),
            "target_network": self.target_network.state_dict(),
            "epsilon": self.epsilon,
        }, path)

    def load(self, path: str = None):
        """Kaydedilmiş ajanı yükler."""
        path = path or str(DRLConfig.MODEL_SAVE_PATH)
        checkpoint = torch.load(path, weights_only=True)
        self.q_network.load_state_dict(checkpoint["q_network"])
        self.target_network.load_state_dict(checkpoint["target_network"])
        self.epsilon = checkpoint["epsilon"]
