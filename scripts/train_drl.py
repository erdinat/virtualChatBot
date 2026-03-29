"""
DRL Agent Eğitimi — DQN ile Adaptif Müfredat Sıralama

Eğitilmiş model: models/drl_agent.pt

Kullanım:
    python scripts/train_drl.py
    python scripts/train_drl.py --episodes 1000 --verbose
"""

import argparse
import sys
from pathlib import Path

import numpy as np

# Proje kökünü sys.path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.drl.agent import DQNAgent
from modules.drl.environment import LearningEnvironment
from config.settings import DRLConfig


def train(num_episodes: int = 500, verbose: bool = False) -> DQNAgent:
    """
    DQN ajanını LearningEnvironment üzerinde eğitir.

    Args:
        num_episodes: Eğitim episode sayısı
        verbose: Her 50 episode'da ilerleme yazdır

    Returns:
        Eğitilmiş DQNAgent
    """
    env = LearningEnvironment()
    agent = DQNAgent(state_dim=env.state_dim, action_dim=env.action_dim)

    episode_rewards = []
    episode_lengths = []

    print(f"🚀 DRL Eğitimi Başlıyor — {num_episodes} episode, "
          f"{env.state_dim} durum boyutu, {env.action_dim} eylem")
    print("-" * 60)

    for ep in range(num_episodes):
        # Her episode için rastgele başlangıç mastery
        initial = np.random.uniform(0.1, 0.6, env.num_skills)
        state = env.reset(initial_mastery=initial)

        total_reward = 0.0
        steps = 0

        while True:
            action = agent.select_action(state)
            next_state, reward, done, info = env.step(action)

            agent.store_transition(state, action, reward, next_state, done)
            agent.train_step()

            state = next_state
            total_reward += reward
            steps += 1

            if done:
                break

        episode_rewards.append(total_reward)
        episode_lengths.append(steps)

        # Target network güncelle
        if (ep + 1) % DRLConfig.TARGET_UPDATE == 0:
            agent.update_target_network()

        # İlerleme raporu
        if verbose and (ep + 1) % 50 == 0:
            last50_r = np.mean(episode_rewards[-50:])
            last50_l = np.mean(episode_lengths[-50:])
            print(
                f"  Episode {ep+1:4d}/{num_episodes} | "
                f"Ort. Ödül: {last50_r:+.2f} | "
                f"Ort. Uzunluk: {last50_l:.1f} | "
                f"Epsilon: {agent.epsilon:.3f}"
            )

    print("-" * 60)
    avg_reward = np.mean(episode_rewards[-100:])
    print(f"✅ Eğitim tamamlandı. Son 100 episode ort. ödül: {avg_reward:+.3f}")
    return agent


def main():
    parser = argparse.ArgumentParser(description="DRL Agent Eğitimi")
    parser.add_argument("--episodes", type=int, default=500, help="Episode sayısı (varsayılan: 500)")
    parser.add_argument("--verbose", action="store_true", help="Her 50 episode'da ilerleme yazdır")
    args = parser.parse_args()

    agent = train(num_episodes=args.episodes, verbose=args.verbose)

    # Modeli kaydet
    save_path = DRLConfig.MODEL_SAVE_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)
    agent.save(str(save_path))
    print(f"💾 Model kaydedildi: {save_path}")


if __name__ == "__main__":
    main()
