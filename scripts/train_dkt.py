"""
DKT Modeli Eğitim Scripti

Sentetik öğrenci verisi üretir ve DKT LSTM modelini eğitir.
Eğitilen model models/dkt_model.pt olarak kaydedilir.

Kullanım:
    cd virtual_teaching_assistant
    source venv/bin/activate
    python scripts/train_dkt.py
"""

import sys
from pathlib import Path

# Proje kökünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import CURRICULUM, DKTConfig
from modules.dkt.model import DKTModel
from modules.dkt.train import train_dkt, save_model
from scripts.generate_synthetic_data import generate_dataset

NUM_SKILLS = len(CURRICULUM)

# ── Hiperparametreler ───────────────────────────────────────────────────────
NUM_TRAIN_STUDENTS = 1000   # Eğitim için simüle edilecek öğrenci sayısı
NUM_VAL_STUDENTS   = 200    # Doğrulama seti öğrenci sayısı
SEQ_LEN            = 25     # Her öğrenci başına kaç soru-cevap etkileşimi
EPOCHS             = 60     # Eğitim turu sayısı
# ────────────────────────────────────────────────────────────────────────────


def main():
    print("=" * 55)
    print("  DKT (Deep Knowledge Tracing) Model Eğitimi")
    print("=" * 55)

    # 1. Sentetik veri üret
    print(f"\n📊 Veri üretiliyor...")
    print(f"   Eğitim: {NUM_TRAIN_STUDENTS} öğrenci × {SEQ_LEN} etkileşim")
    train_data, train_labels = generate_dataset(
        num_students=NUM_TRAIN_STUDENTS,
        seq_len=SEQ_LEN,
        seed_offset=0,
    )

    print(f"   Doğrulama: {NUM_VAL_STUDENTS} öğrenci × {SEQ_LEN} etkileşim")
    val_data, val_labels = generate_dataset(
        num_students=NUM_VAL_STUDENTS,
        seq_len=SEQ_LEN,
        seed_offset=NUM_TRAIN_STUDENTS,  # Ayrı seed → veri sızıntısı yok
    )

    print(f"   data shape : {train_data.shape}")
    print(f"   label shape: {train_labels.shape}")

    # 2. Modeli başlat
    print(f"\n🧠 Model oluşturuluyor...")
    model = DKTModel(
        num_skills=NUM_SKILLS,
        hidden_dim=DKTConfig.HIDDEN_DIM,   # 128
        num_layers=DKTConfig.NUM_LAYERS,   # 1
        dropout=DKTConfig.DROPOUT,         # 0.2
    )
    param_count = sum(p.numel() for p in model.parameters())
    print(f"   Toplam parametre: {param_count:,}")
    print(f"   Mimari: Linear({NUM_SKILLS*2}→128) → LSTM(128) → Linear(128→{NUM_SKILLS}) → Sigmoid")

    # 3. Eğit
    print(f"\n🏋️  Eğitim başlıyor ({EPOCHS} epoch)...\n")
    history = train_dkt(
        model=model,
        train_data=train_data,
        train_labels=train_labels,
        val_data=val_data,
        val_labels=val_labels,
        epochs=EPOCHS,
        lr=DKTConfig.LEARNING_RATE,
        batch_size=DKTConfig.BATCH_SIZE,
    )

    # 4. Sonuçları göster
    final_train = history["train_losses"][-1]
    final_val   = history["val_losses"][-1] if history["val_losses"] else "—"
    print(f"\n📈 Eğitim Sonucu:")
    print(f"   Final Train Loss : {final_train:.4f}")
    print(f"   Final Val Loss   : {final_val:.4f}" if isinstance(final_val, float) else f"   Final Val Loss   : {final_val}")

    # 5. Kaydet
    print()
    save_model(model)

    # 6. Hızlı doğrulama
    print("\n🔍 Model doğrulaması...")
    import torch
    model.eval()
    with torch.no_grad():
        sample = val_data[:1]           # 1 öğrenci
        preds, _ = model(sample)
        last_step = preds[0, -1, :]     # Son adımdaki tahminler
        print("   Son adım mastery tahminleri:")
        for i, topic in enumerate(CURRICULUM):
            bar = "█" * int(last_step[i].item() * 20)
            print(f"   {topic['name'][:35]:<35} {last_step[i]:.2f} {bar}")

    print("\n✅ DKT modeli hazır! 'streamlit run app.py' ile uygulamayı başlatın.")
    print("   Uygulama artık kural tabanlı fallback yerine LSTM modelini kullanacak.")


if __name__ == "__main__":
    main()
