"""
DKT – Eğitim ve Değerlendirme

DKT modelini eğitir ve AUC-ROC ile değerlendirir.
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path

from config.settings import DKTConfig
from modules.dkt.model import DKTModel


def train_dkt(
    model: DKTModel,
    train_data: torch.Tensor,
    train_labels: torch.Tensor,
    val_data: torch.Tensor = None,
    val_labels: torch.Tensor = None,
    epochs: int = None,
    lr: float = None,
    batch_size: int = None,
) -> dict:
    """
    DKT modelini eğitir.

    Args:
        model: DKTModel instance
        train_data: (N, seq_len, num_skills*2) eğitim verisi
        train_labels: (N, seq_len, num_skills) hedef etiketler
        ...

    Returns:
        {"train_losses": [...], "val_losses": [...]}
    """
    epochs = epochs or DKTConfig.EPOCHS
    lr = lr or DKTConfig.LEARNING_RATE
    batch_size = batch_size or DKTConfig.BATCH_SIZE

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()

    dataset = TensorDataset(train_data, train_labels)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    train_losses = []
    val_losses = []

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0

        for batch_x, batch_y in dataloader:
            optimizer.zero_grad()
            predictions, _ = model(batch_x)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(dataloader)
        train_losses.append(avg_loss)

        # Doğrulama
        if val_data is not None and val_labels is not None:
            model.eval()
            with torch.no_grad():
                val_pred, _ = model(val_data)
                val_loss = criterion(val_pred, val_labels).item()
                val_losses.append(val_loss)

        if (epoch + 1) % 10 == 0:
            msg = f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_loss:.4f}"
            if val_losses:
                msg += f" | Val Loss: {val_losses[-1]:.4f}"
            print(msg)

    return {"train_losses": train_losses, "val_losses": val_losses}


def save_model(model: DKTModel, path: Path = None):
    """Eğitilmiş modeli diske kaydeder."""
    path = path or DKTConfig.MODEL_SAVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)
    print(f"✅ DKT modeli kaydedildi: {path}")


def load_model(model: DKTModel, path: Path = None) -> DKTModel:
    """Kaydedilmiş modeli yükler."""
    path = path or DKTConfig.MODEL_SAVE_PATH
    model.load_state_dict(torch.load(path, weights_only=True))
    model.eval()
    print(f"✅ DKT modeli yüklendi: {path}")
    return model
