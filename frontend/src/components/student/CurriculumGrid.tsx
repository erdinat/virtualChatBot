import { motion } from "framer-motion";
import { TOPICS, TOPIC_ICONS, masteryBadge } from "./types";

interface Props {
  masteryMap: Record<string, number>;
  onTopicClick: (topicId: number, topicName: string) => void;
}

export default function CurriculumGrid({ masteryMap, onTopicClick }: Props) {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-on-surface mb-2">Python Müfredatı</h2>
          <p className="text-sm text-on-surface-variant">
            Çalışmak istediğin konuyu seç. Kısa bir ön test ile seviyeni belirleyip sana özel içerik sunalım.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {TOPICS.map((topicName, i) => {
            const topicId = i + 1;
            const score = masteryMap[topicName] ?? 0;
            const badge = masteryBadge(score);
            const pct = Math.round(score * 100);

            return (
              <motion.button
                key={topicId}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onTopicClick(topicId, topicName)}
                className="glass-card rounded-2xl p-6 text-left border transition-all group"
                style={{ borderColor: "rgba(151,169,255,.1)" }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl gradient-bg flex items-center justify-center shrink-0"
                    style={{ boxShadow: "0 4px 12px rgba(151,169,255,.15)" }}>
                    <span className="material-symbols-outlined text-white"
                      style={{ fontSize: "20px", fontVariationSettings: "'FILL' 1" }}>
                      {TOPIC_ICONS[i]}
                    </span>
                  </div>
                  <span className="text-xs font-bold px-2 py-1 rounded-full"
                    style={{ color: badge.color, background: `${badge.color}18` }}>
                    {badge.label}
                  </span>
                </div>

                <p className="text-xs font-bold text-on-surface-variant mb-1">Modül {topicId}</p>
                <h3 className="text-sm font-bold text-on-surface mb-4 leading-tight group-hover:text-primary transition-colors">
                  {topicName}
                </h3>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-on-surface-variant">Hakimiyet</span>
                    <span className="font-bold text-primary">{pct}%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full overflow-hidden" style={{ background: "rgba(151,169,255,.08)" }}>
                    <motion.div className="h-full shimmer-bar"
                      initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.8, delay: i * 0.05, ease: "easeOut" }} />
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-1.5 text-xs text-on-surface-variant group-hover:text-primary transition-colors">
                  <span className="material-symbols-outlined" style={{ fontSize: "14px" }}>play_circle</span>
                  Konuyu Çalış
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
