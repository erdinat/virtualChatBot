"""Ablation çalışması bar grafiği — poster için."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

strategies = ["Sıralı\n(Baseline)", "Kural\nTabanlı", "DRL\n(DQN)"]
values     = [0.317, 0.278, 0.312]
colors     = ["#95d5b2", "#95d5b2", "#2d6a4f"]  # DRL koyu yeşil

fig, ax = plt.subplots(figsize=(5, 3.5))
bars = ax.bar(strategies, values, color=colors, edgecolor="white",
              linewidth=1.2, width=0.5)

# Değer etiketleri
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.004,
            f"{val:.3f}", ha="center", va="bottom",
            fontsize=10, fontweight="bold", color="#1b4332")

ax.set_ylabel("Ortalama Final Mastery", fontsize=10, color="#1b4332")
ax.set_ylim(0.25, 0.34)
ax.set_title("Adaptasyon Stratejisi Karşılaştırması\n(200 öğrenci × 300 adım)",
             fontsize=10, fontweight="bold", color="#1b4332", pad=10)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#ccc")
ax.tick_params(colors="#1b4332")
ax.yaxis.label.set_color("#1b4332")

legend = mpatches.Patch(color="#2d6a4f", label="Bu çalışma (DQN)")
ax.legend(handles=[legend], fontsize=9, framealpha=0)

fig.patch.set_facecolor("white")
ax.set_facecolor("#f9fafb")

plt.tight_layout()
plt.savefig("results/ablation_chart.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("✅ results/ablation_chart.png kaydedildi")
plt.show()
