"""
DKT Model Değerlendirmesi — AUC-ROC ve Binary Cross-Entropy

Eğitilmiş DKT modelinin tahmin doğruluğunu ölçer.
Sonuçlar results/dkt_eval.json dosyasına kaydedilir.

Kullanım:
    python scripts/evaluate_dkt.py
"""

import json
import sys
from pathlib import Path

import torch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.dkt.model import DKTModel
from config.settings import DKTConfig, CURRICULUM


def generate_test_data(n_students: int = 200, seq_len: int = 30) -> list[dict]:
    """
    Değerlendirme için sentetik öğrenci verisi üretir.
    Gerçek veri yoksa sentetik veri kullanılır.
    """
    num_skills = len(CURRICULUM)
    data = []

    for _ in range(n_students):
        # Her öğrencinin başlangıç mastery'si
        mastery = np.random.uniform(0.1, 0.8, num_skills)
        interactions = []

        for _ in range(seq_len):
            skill = np.random.randint(0, num_skills)
            # Başarı olasılığı = mastery + gürültü
            p_correct = np.clip(mastery[skill] + np.random.normal(0, 0.1), 0.05, 0.95)
            correct = np.random.random() < p_correct

            if correct:
                mastery[skill] = min(1.0, mastery[skill] + 0.05)
            else:
                mastery[skill] = max(0.0, mastery[skill] - 0.03)

            interactions.append({"skill_id": skill + 1, "correct": bool(correct)})

        data.append({"interactions": interactions, "true_mastery": mastery.tolist()})

    return data


def evaluate(model_path: Path = None) -> dict:
    path = model_path or DKTConfig.MODEL_SAVE_PATH

    if not path.exists():
        print(f"❌ Model bulunamadı: {path}")
        print("   Önce 'python scripts/train_dkt.py' çalıştırın.")
        sys.exit(1)

    num_skills = len(CURRICULUM)
    model = DKTModel(num_skills=num_skills)
    model.load_state_dict(torch.load(path, weights_only=True))
    model.eval()
    print(f"✅ Model yüklendi: {path}")

    test_data = generate_test_data(n_students=300, seq_len=25)

    all_preds = []
    all_targets = []

    with torch.no_grad():
        for student in test_data:
            interactions = student["interactions"]
            true_mastery = np.array(student["true_mastery"])

            seq_len = len(interactions)
            x = torch.zeros(1, seq_len, num_skills * 2)

            for t, inter in enumerate(interactions):
                sid = inter["skill_id"] - 1
                if inter["correct"]:
                    x[0, t, sid] = 1.0
                else:
                    x[0, t, num_skills + sid] = 1.0

            pred = model.predict_mastery(x).squeeze(0).numpy()

            all_preds.append(pred)
            all_targets.append(true_mastery)

    preds = np.array(all_preds)      # (N, num_skills)
    targets = np.array(all_targets)  # (N, num_skills)

    # Binary labels: mastery >= 0.6 → "yetkin"
    binary_targets = (targets >= 0.6).astype(float)

    # AUC-ROC (per-skill average)
    try:
        from sklearn.metrics import roc_auc_score, log_loss
        # Flatten tüm skill tahminleri
        auc = roc_auc_score(binary_targets.flatten(), preds.flatten())
        bce = log_loss(binary_targets.flatten(), np.clip(preds.flatten(), 1e-7, 1 - 1e-7))
    except ImportError:
        print("⚠️  scikit-learn bulunamadı, AUC hesaplanamadı (pip install scikit-learn)")
        auc = float("nan")
        bce = float("nan")

    # MAE (Mean Absolute Error) — ek metrik
    mae = float(np.mean(np.abs(preds - targets)))
    rmse = float(np.sqrt(np.mean((preds - targets) ** 2)))

    results = {
        "model_path": str(path),
        "test_students": len(test_data),
        "metrics": {
            "auc_roc": round(float(auc), 4),
            "binary_cross_entropy": round(float(bce), 4),
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
        },
    }

    # Sonuçları kaydet
    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "dkt_eval.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    return results


def main():
    results = evaluate()
    m = results["metrics"]
    print("\n" + "=" * 50)
    print("  DKT Model Değerlendirme Sonuçları")
    print("=" * 50)
    print(f"  Test Öğrenci Sayısı : {results['test_students']}")
    print(f"  AUC-ROC             : {m['auc_roc']:.4f}")
    print(f"  Binary Cross-Entropy: {m['binary_cross_entropy']:.4f}")
    print(f"  MAE                 : {m['mae']:.4f}")
    print(f"  RMSE                : {m['rmse']:.4f}")
    print("=" * 50)
    print(f"\n📊 Sonuçlar kaydedildi: results/dkt_eval.json")


if __name__ == "__main__":
    main()
