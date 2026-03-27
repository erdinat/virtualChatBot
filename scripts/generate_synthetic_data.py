"""
Sentetik Öğrenci Verisi Üreteci

DKT modelini eğitmek için gerçekçi öğrenci öğrenme yolculukları simüle eder.

Her öğrenci için:
  - Her konunun zorluğuna göre farklı başlangıç mastery değeri
  - Her adımda bir konu seçilir (kolay konular daha sık seçilir)
  - Doğru cevap → mastery +0.05, yanlış → mastery -0.03
  - Gürültü eklenerek gerçekçi öğrenme eğrileri oluşturulur
"""

import numpy as np
import torch
from pathlib import Path
import sys

# Proje kökünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import CURRICULUM

NUM_SKILLS = len(CURRICULUM)  # 10


def simulate_student(seq_len: int = 20, seed: int = None):
    """
    Tek bir öğrencinin öğrenme yolculuğunu simüle eder.

    Args:
        seq_len: Kaç soru-cevap etkileşimi üretileceği
        seed: Tekrarlanabilirlik için rastgele tohum

    Returns:
        interactions: [(skill_idx, correct), ...] — hangi konudan soru geldi, doğru mu?
        mastery_history: [mastery_array, ...] — her adımdaki gerçek mastery durumu
    """
    rng = np.random.default_rng(seed)

    # Başlangıç mastery: zorluk 1 → ~0.45, zorluk 5 → ~0.13
    # Gerçek hayatta öğrenciler kolay konuları daha iyi bilir
    mastery = np.array([
        np.clip(
            0.5 - (topic["difficulty"] - 1) * 0.08 + rng.normal(0, 0.05),
            0.05, 0.90
        )
        for topic in CURRICULUM
    ])

    interactions = []
    mastery_history = []

    for _ in range(seq_len):
        # Bu adımdaki mastery'yi kaydet (label olarak kullanılacak)
        mastery_history.append(mastery.copy())

        # Konu seçimi: zorluk tersine orantılı ağırlık
        # Zorluk 1 → 5x daha sık sorulur; zorluk 5 → 1x
        difficulties = np.array([t["difficulty"] for t in CURRICULUM], dtype=float)
        weights = 1.0 / difficulties
        weights /= weights.sum()
        skill_idx = rng.choice(NUM_SKILLS, p=weights)

        # Cevap: mastery olasılığına göre + küçük gürültü
        answer_prob = np.clip(mastery[skill_idx] + rng.normal(0, 0.05), 0.0, 1.0)
        correct = int(rng.random() < answer_prob)

        interactions.append((skill_idx, correct))

        # Mastery güncelle (öğrenme simülasyonu)
        if correct:
            mastery[skill_idx] = min(1.0, mastery[skill_idx] + 0.05)
        else:
            mastery[skill_idx] = max(0.0, mastery[skill_idx] - 0.03)

    return interactions, mastery_history


def generate_dataset(
    num_students: int,
    seq_len: int = 20,
    seed_offset: int = 0,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Birden fazla öğrenci için eğitim/test verisi üretir.

    Args:
        num_students: Simüle edilecek öğrenci sayısı
        seq_len: Her öğrencinin kaç etkileşiminin olduğu
        seed_offset: Eğitim/validasyon setlerini ayırmak için

    Returns:
        data:   (N, seq_len, NUM_SKILLS * 2) — one-hot encoded etkileşimler
        labels: (N, seq_len, NUM_SKILLS)     — her adımdaki gerçek mastery
    """
    data = np.zeros((num_students, seq_len, NUM_SKILLS * 2), dtype=np.float32)
    labels = np.zeros((num_students, seq_len, NUM_SKILLS), dtype=np.float32)

    for i in range(num_students):
        interactions, mastery_history = simulate_student(
            seq_len=seq_len,
            seed=seed_offset + i,
        )

        for t, ((skill_idx, correct), mastery) in enumerate(zip(interactions, mastery_history)):
            # One-hot encoding:
            #   Doğru cevap → ilk N slot (0..9) içinde skill_idx pozisyonuna 1
            #   Yanlış cevap → son N slot (10..19) içinde skill_idx pozisyonuna 1
            if correct:
                data[i, t, skill_idx] = 1.0
            else:
                data[i, t, NUM_SKILLS + skill_idx] = 1.0

            # Label: bu adımdaki gerçek mastery (LSTM'in tahmin etmeye çalışacağı şey)
            labels[i, t, :] = mastery

    return torch.tensor(data), torch.tensor(labels)


if __name__ == "__main__":
    # Hızlı test
    print("🔬 Sentetik veri üretici testi...")
    interactions, mastery_hist = simulate_student(seq_len=5, seed=42)
    for t, ((s, c), m) in enumerate(zip(interactions, mastery_hist)):
        print(f"  Adım {t+1}: Konu={CURRICULUM[s]['name'][:20]:<20} "
              f"Doğru={bool(c)}  Mastery={m[s]:.2f}")

    train_x, train_y = generate_dataset(num_students=10, seq_len=5)
    print(f"\nVeri boyutları:")
    print(f"  data:   {train_x.shape}  (öğrenci, adım, konu*2)")
    print(f"  labels: {train_y.shape}  (öğrenci, adım, konu)")
    print("✅ Test başarılı")
