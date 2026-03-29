"""
Ablation Study — Adaptasyon Stratejileri Karşılaştırması

3 strateji üzerinde simüle edilmiş öğrencilerle karşılaştırmalı analiz:
  1. Sıralı (adaptasyon yok) — konuları zorluk sırasına göre ver
  2. Kural Tabanlı (RuleBasedPolicy) — zayıf konuyu tekrar et
  3. DRL (DQNAgent) — varsa eğitilmiş model, yoksa RuleBasedPolicy

Sonuçlar results/ablation_results.json ve terminale tablo olarak yazdırılır.

Kullanım:
    python scripts/evaluate_strategies.py
    python scripts/evaluate_strategies.py --students 200 --steps 60
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.drl.environment import LearningEnvironment
from modules.drl.policy import RuleBasedPolicy
from config.settings import CURRICULUM, DRLConfig

MASTERY_THRESHOLD = 0.7
NUM_SKILLS = len(CURRICULUM)


# ── Strateji 1: Sıralı ───────────────────────────────────────────────────────

class SequentialPolicy:
    """Konuları zorluk sırasına göre sırayla verir, adaptasyon yok."""

    def __init__(self):
        self._sorted = sorted(range(NUM_SKILLS), key=lambda i: CURRICULUM[i]["difficulty"])
        self._idx = 0

    def select_action(self, _state: np.ndarray) -> int:
        action = self._sorted[self._idx % NUM_SKILLS]
        self._idx += 1
        return action

    def reset(self):
        self._idx = 0


# ── Strateji 2: Kural Tabanlı ────────────────────────────────────────────────

class RuleBasedAdapter:
    """RuleBasedPolicy'yi RL action interface'ine sarar."""

    def __init__(self):
        self._policy = RuleBasedPolicy(mastery_threshold=MASTERY_THRESHOLD)

    def select_action(self, state: np.ndarray) -> int:
        mastery_dict = {CURRICULUM[i]["name"]: float(state[i]) for i in range(NUM_SKILLS)}
        suggestion = self._policy.select_next_topic(mastery_dict)
        topic_name = suggestion["topic"]["name"]
        for i, t in enumerate(CURRICULUM):
            if t["name"] == topic_name:
                return i
        return 0

    def reset(self):
        pass


# ── Strateji 3: DRL ──────────────────────────────────────────────────────────

def _load_drl_agent():
    path = DRLConfig.MODEL_SAVE_PATH
    if not path.exists():
        return None
    try:
        from modules.drl.agent import DQNAgent
        agent = DQNAgent(state_dim=NUM_SKILLS, action_dim=NUM_SKILLS)
        agent.load(str(path))
        agent.epsilon = 0.0  # Tamamen greedy (değerlendirme modu)
        return agent
    except Exception as e:
        print(f"⚠️  DRL modeli yüklenemedi ({e}), kural tabanlı fallback kullanılıyor.")
        return None


# ── Simülasyon ───────────────────────────────────────────────────────────────

def simulate(strategy, n_students: int = 100, max_steps: int = 50) -> dict:
    """
    Verilen stratejiyle n_students simüle öğrencisi üzerinde max_steps adım çalıştırır.

    Returns:
        {
          "avg_final_mastery": float,
          "avg_steps_to_mastery": float,   # 0.7 eşiğine ulaşma adımı (-1 = ulaşamadı)
          "mastery_rate": float,            # eşiğe ulaşan öğrenci oranı
        }
    """
    env = LearningEnvironment()
    steps_to_mastery = []
    final_masteries = []

    for _ in range(n_students):
        initial = np.random.uniform(0.05, 0.45, NUM_SKILLS)
        state = env.reset(initial_mastery=initial)
        if hasattr(strategy, "reset"):
            strategy.reset()

        reached = False
        for step in range(max_steps):
            action = strategy.select_action(state)
            state, _, done, _ = env.step(action)

            if not reached and np.mean(state) >= MASTERY_THRESHOLD:
                steps_to_mastery.append(step + 1)
                reached = True

            if done:
                break

        if not reached:
            steps_to_mastery.append(-1)
        final_masteries.append(float(np.mean(state)))

    reachable = [s for s in steps_to_mastery if s >= 0]
    return {
        "avg_final_mastery": round(float(np.mean(final_masteries)), 4),
        "avg_steps_to_mastery": round(float(np.mean(reachable)) if reachable else -1, 2),
        "mastery_rate": round(len(reachable) / n_students, 4),
    }


def main():
    parser = argparse.ArgumentParser(description="Adaptasyon Stratejileri Ablation Study")
    parser.add_argument("--students", type=int, default=100, help="Simüle öğrenci sayısı")
    parser.add_argument("--steps",    type=int, default=50,  help="Maksimum adım sayısı")
    args = parser.parse_args()

    drl_agent = _load_drl_agent()
    drl_label = "DRL (Eğitilmiş)" if drl_agent else "DRL (Kural Fallback)"
    drl_strategy = drl_agent if drl_agent else RuleBasedAdapter()

    strategies = {
        "Sıralı (Adaptasyonsuz)": SequentialPolicy(),
        "Kural Tabanlı": RuleBasedAdapter(),
        drl_label: drl_strategy,
    }

    print(f"\n🔬 Ablation Study — {args.students} öğrenci × {args.steps} adım")
    print("=" * 70)

    results = {}
    for name, strategy in strategies.items():
        print(f"  ⏳ {name} simüle ediliyor…", end="", flush=True)
        r = simulate(strategy, n_students=args.students, max_steps=args.steps)
        results[name] = r
        print(f"\r  ✅ {name:<30} Tamamlandı")

    print("=" * 70)
    header = f"  {'Strateji':<32} {'Ort. Mastery':>12} {'Yetkinlik Oranı':>16} {'Ort. Adım':>10}"
    print(header)
    print("  " + "-" * 72)
    for name, r in results.items():
        mastery_rate_pct = f"%{r['mastery_rate']*100:.1f}"
        steps_str = str(r["avg_steps_to_mastery"]) if r["avg_steps_to_mastery"] >= 0 else "—"
        print(
            f"  {name:<32} "
            f"{r['avg_final_mastery']:>12.4f} "
            f"{mastery_rate_pct:>16} "
            f"{steps_str:>10}"
        )
    print("=" * 70)

    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "ablation_results.json"
    out_path.write_text(json.dumps(
        {"config": {"students": args.students, "steps": args.steps}, "results": results},
        ensure_ascii=False, indent=2
    ))
    print(f"\n📊 Sonuçlar kaydedildi: results/ablation_results.json\n")


if __name__ == "__main__":
    main()
