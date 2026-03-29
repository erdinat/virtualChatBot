"""
Persona Bazlı Simülasyon — Ali (Başlangıç) vs Ayşe (İleri)

Akademik makalede tanımlanan iki öğrenci personasının sistemin
adaptasyonuna farklı tepkilerini karşılaştırır.

Çıktı:
  - Her persona için konu sırası ve mastery artışı
  - results/persona_simulation.json

Kullanım:
    python scripts/simulate_personas.py
    python scripts/simulate_personas.py --steps 40
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

NUM_SKILLS = len(CURRICULUM)
TOPIC_NAMES = [t["name"] for t in CURRICULUM]


# Persona başlangıç mastery vektörleri
PERSONAS = {
    "Ali (Başlangıç)": {
        "initial_mastery": [0.10] * NUM_SKILLS,  # Tüm konularda düşük
        "description": "Python'a yeni başlayan öğrenci",
        "color": "🔵",
    },
    "Ayşe (İleri)": {
        "initial_mastery": [0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.20, 0.15, 0.10, 0.10],
        "description": "Temel konularda güçlü, ileri konularda zayıf öğrenci",
        "color": "🟢",
    },
}


def simulate_persona(
    name: str,
    persona: dict,
    max_steps: int = 30,
) -> dict:
    """Bir persona için simülasyon çalıştırır."""
    env = LearningEnvironment()
    policy = RuleBasedPolicy(mastery_threshold=0.7)

    initial = np.array(persona["initial_mastery"])
    state = env.reset(initial_mastery=initial.copy())

    # DRL varsa kullan
    drl_agent = None
    if DRLConfig.MODEL_SAVE_PATH.exists():
        try:
            from modules.drl.agent import DQNAgent
            drl_agent = DQNAgent(state_dim=NUM_SKILLS, action_dim=NUM_SKILLS)
            drl_agent.load(str(DRLConfig.MODEL_SAVE_PATH))
            drl_agent.epsilon = 0.0
        except Exception:
            drl_agent = None

    history = []

    for step in range(max_steps):
        # Politikadan eylem seç
        mastery_dict = {CURRICULUM[i]["name"]: float(state[i]) for i in range(NUM_SKILLS)}

        if drl_agent:
            action = drl_agent.select_action(state)
            strategy_used = "DRL"
        else:
            suggestion = policy.select_next_topic(mastery_dict)
            topic_name = suggestion["topic"]["name"]
            action = next(i for i, t in enumerate(CURRICULUM) if t["name"] == topic_name)
            strategy_used = "RuleBasedPolicy"

        prev_mastery = float(state[action])
        next_state, reward, done, info = env.step(action)

        history.append({
            "step": step + 1,
            "topic": TOPIC_NAMES[action],
            "topic_id": action + 1,
            "success": info["success"],
            "mastery_before": round(prev_mastery, 3),
            "mastery_after": round(float(next_state[action]), 3),
            "avg_mastery": round(float(np.mean(next_state)), 3),
            "strategy": strategy_used,
        })

        state = next_state
        if done:
            break

    # Özet istatistikler
    final_mastery = {TOPIC_NAMES[i]: round(float(state[i]), 3) for i in range(NUM_SKILLS)}
    topics_visited = [h["topic"] for h in history]
    topic_counts = {t: topics_visited.count(t) for t in set(topics_visited)}

    return {
        "persona": name,
        "description": persona["description"],
        "initial_avg_mastery": round(float(np.mean(initial)), 3),
        "final_avg_mastery": round(float(np.mean(state)), 3),
        "mastery_gain": round(float(np.mean(state)) - float(np.mean(initial)), 3),
        "steps_taken": len(history),
        "final_mastery": final_mastery,
        "topic_visit_counts": topic_counts,
        "trajectory": history,
    }


def print_report(results: list[dict]):
    print("\n" + "=" * 70)
    print("  PERSONA BAZLI SİMÜLASYON RAPORU")
    print("=" * 70)

    for r in results:
        persona = r["persona"]
        desc = r["description"]
        gain = r["mastery_gain"]
        gain_str = f"+{gain:.3f}" if gain >= 0 else f"{gain:.3f}"

        print(f"\n  👤 {persona}")
        print(f"     {desc}")
        print(f"     Başlangıç Ort. Mastery : {r['initial_avg_mastery']:.3f}")
        print(f"     Final Ort. Mastery     : {r['final_avg_mastery']:.3f}  ({gain_str})")
        print(f"     Toplam Adım            : {r['steps_taken']}")
        print()

        # En çok ziyaret edilen konular
        top_topics = sorted(r["topic_visit_counts"].items(), key=lambda x: -x[1])[:5]
        print("     En Çok Çalışılan Konular:")
        for topic, count in top_topics:
            bar = "█" * count
            print(f"       {topic:<40} {bar} ({count})")

        # Final mastery tablosu
        print()
        print("     Final Mastery:")
        for topic, score in r["final_mastery"].items():
            bar = "█" * int(score * 20)
            level = "✅" if score >= 0.7 else ("⚠️ " if score >= 0.4 else "❌")
            print(f"       {level} {topic:<38} {score:.3f}  {bar}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Persona Bazlı Simülasyon")
    parser.add_argument("--steps", type=int, default=30, help="Her persona için adım sayısı")
    args = parser.parse_args()

    results = []
    for name, persona in PERSONAS.items():
        print(f"  {persona['color']} {name} simüle ediliyor…")
        r = simulate_persona(name, persona, max_steps=args.steps)
        results.append(r)

    print_report(results)

    # Kaydet
    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "persona_simulation.json"
    # Trajectory çok uzun olabilir, özet kaydet
    summary = [{k: v for k, v in r.items() if k != "trajectory"} for r in results]
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n📊 Özet sonuçlar kaydedildi: results/persona_simulation.json")


if __name__ == "__main__":
    main()
