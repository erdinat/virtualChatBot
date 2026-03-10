"""
DKT (Deep Knowledge Tracing) – LSTM Modeli

Öğrencinin bilgi seviyesini zaman içinde takip eden LSTM tabanlı model.
Her beceri (skill) için P(correct) olasılığı üretir.

Referans: Gervet ve diğ. (2020)
"""

import torch
import torch.nn as nn
from config.settings import DKTConfig


class DKTModel(nn.Module):
    """
    Deep Knowledge Tracing modeli.

    Input:  Öğrenci etkileşim dizisi (skill_id, correct) çiftleri
    Output: Her adımda tüm beceriler için doğru cevaplama olasılığı
    """

    def __init__(self, num_skills: int, hidden_dim: int = None, num_layers: int = None, dropout: float = None):
        super().__init__()

        self.num_skills = num_skills
        self.hidden_dim = hidden_dim or DKTConfig.HIDDEN_DIM
        self.num_layers = num_layers or DKTConfig.NUM_LAYERS
        dropout = dropout if dropout is not None else DKTConfig.DROPOUT

        # Input: one-hot encoded (skill_id * 2) – doğru/yanlış ayrımı
        self.input_dim = num_skills * 2

        # Embedding katmanı
        self.input_embedding = nn.Linear(self.input_dim, self.hidden_dim)

        # LSTM katmanı
        self.lstm = nn.LSTM(
            input_size=self.hidden_dim,
            hidden_size=self.hidden_dim,
            num_layers=self.num_layers,
            batch_first=True,
            dropout=dropout if self.num_layers > 1 else 0.0,
        )

        # Dropout
        self.dropout = nn.Dropout(dropout)

        # Çıkış katmanı – her beceri için olasılık
        self.output_layer = nn.Linear(self.hidden_dim, num_skills)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor, hidden=None):
        """
        Args:
            x: (batch_size, seq_len, num_skills * 2) – one-hot encoded etkileşimler
            hidden: Önceki LSTM gizli durum (opsiyonel)

        Returns:
            predictions: (batch_size, seq_len, num_skills) – her beceri için P(correct)
            hidden: Güncel gizli durum
        """
        # Embedding
        embedded = torch.relu(self.input_embedding(x))
        embedded = self.dropout(embedded)

        # LSTM
        lstm_out, hidden = self.lstm(embedded, hidden)
        lstm_out = self.dropout(lstm_out)

        # Çıkış
        output = self.sigmoid(self.output_layer(lstm_out))

        return output, hidden

    def predict_mastery(self, x: torch.Tensor) -> torch.Tensor:
        """
        Öğrencinin mevcut bilgi seviyesini tahmin eder.
        Son zaman adımındaki olasılıkları döndürür.
        """
        self.eval()
        with torch.no_grad():
            predictions, _ = self.forward(x)
            # Son adımdaki tahminleri al
            return predictions[:, -1, :]  # (batch_size, num_skills)
