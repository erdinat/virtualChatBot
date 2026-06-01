"""
Reproducibility — random seed sabitleme yardımcısı.

DKT ve DRL eğitim scriptleri tarafından kullanılır. Python `random`,
NumPy ve PyTorch (CPU + CUDA) global RNG'lerini aynı seed ile başlatır.

Not: PyTorch'un `DataLoader(shuffle=True)` ile tam deterministik olması için
ayrıca `torch.use_deterministic_algorithms(True)` gerekir; ancak bu LSTM
katmanlarında çekirdek hatası verebildiğinden burada kapatılmıştır.
"""

import os
import random

import numpy as np
import torch

DEFAULT_SEED = 42


def set_seed(seed: int = DEFAULT_SEED) -> int:
    """Tüm RNG'leri sabitler, kullanılan seed'i döner."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    return seed
