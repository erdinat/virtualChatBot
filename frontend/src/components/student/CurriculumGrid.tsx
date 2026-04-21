import { motion } from "framer-motion";
import { TOPICS, TOPIC_ICONS } from "./types";
import type { TopicLevel } from "./types";

const LEVEL_LABEL: Record<TopicLevel, string> = {
  beginner: "Başlangıç",
  intermediate: "Orta",
  advanced: "İleri",
};

interface Props {
  masteredTopics: Set<number>;
  studiedTopics: Set<number>;
  lockedTopics: Set<number>;
  username?: string;
  onTopicClick: (topicId: number, topicName: string) => void;
}

export default function CurriculumGrid({ masteredTopics, studiedTopics, lockedTopics, username, onTopicClick }: Props) {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-on-surface mb-2">Python Müfredatı</h2>
          <p className="text-sm text-on-surface-variant">
            Konuyu seç — kısa bir ön test ile seviyeni belirleyelim ve sana özel içerik sunalım.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {TOPICS.map((topicName, i) => {
            const topicId  = i + 1;
            const mastered = masteredTopics.has(topicId);
            const studied  = studiedTopics.has(topicId);
            const locked   = lockedTopics.has(topicId);

            // Mevcut seviye ve o seviyedeki ilerleme localStorage'dan okunur
            const currentLevel = (localStorage.getItem(`topic_level_${username}_${topicId}`) ?? "beginner") as TopicLevel;
            const pct = studied
              ? parseInt(localStorage.getItem(`level_progress_${username}_${topicId}_${currentLevel}`) ?? "0")
              : 0;

            // Rozet
            const badgeLabel = mastered ? "Tamamlandı"
              : studied && pct > 0 ? "Devam Ediyor"
              : studied ? "Başlandı"
              : "Başlanmadı";
            const badgeColor = mastered ? "#a78bfa"
              : studied && pct > 0 ? "#60a5fa"
              : "rgba(255,255,255,.3)";

            return (
              <motion.button
                key={topicId}
                whileHover={locked ? {} : { scale: 1.02 }}
                whileTap={locked ? {} : { scale: 0.98 }}
                onClick={() => !locked && onTopicClick(topicId, topicName)}
                className="glass-card rounded-2xl p-6 text-left border transition-all group relative overflow-hidden"
                style={{
                  borderColor: mastered
                    ? "rgba(167,139,250,.35)"
                    : locked
                    ? "rgba(255,255,255,.04)"
                    : "rgba(151,169,255,.1)",
                  opacity: locked ? 0.55 : 1,
                  cursor: locked ? "not-allowed" : "pointer",
                }}
              >
                {/* Kilitli overlay */}
                {locked && (() => {
                  const prereqId = topicId - 1;
                  const prereqKey = `level_progress_${username}_${prereqId}_intermediate`;
                  const prereqPct = parseInt(localStorage.getItem(prereqKey) ?? "0");
                  const prereqName = TOPICS[prereqId - 1];
                  return (
                    <div className="absolute inset-0 flex items-center justify-center z-10 rounded-2xl"
                      style={{ background: "rgba(10,8,30,.65)", backdropFilter: "blur(2px)" }}>
                      <div className="flex flex-col items-center gap-2 px-5 w-full">
                        <span className="material-symbols-outlined text-on-surface-variant"
                          style={{ fontSize: "28px", fontVariationSettings: "'FILL' 1" }}>lock</span>
                        <p className="text-xs text-on-surface-variant font-medium text-center leading-snug">
                          <span className="text-primary font-bold">{prereqName}</span> modülünü<br />
                          orta seviyede %50 tamamla
                        </p>
                        {/* Prereq intermediate progress bar */}
                        <div className="w-full mt-1">
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-on-surface-variant" style={{ fontSize: "10px" }}>Orta Seviye İlerlemesi</span>
                            <span className="font-bold text-primary" style={{ fontSize: "10px" }}>{prereqPct}% / 50%</span>
                          </div>
                          <div className="h-1 w-full rounded-full overflow-hidden" style={{ background: "rgba(151,169,255,.1)" }}>
                            <div className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.min(prereqPct, 50) * 2}%`,
                                background: prereqPct >= 50 ? "linear-gradient(90deg,#34d399,#059669)" : "linear-gradient(90deg,#667eea,#f093fb)",
                              }} />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* Tamamlandı rozeti */}
                {mastered && (
                  <div className="absolute top-3 right-3 z-10">
                    <span className="material-symbols-outlined"
                      style={{ fontSize: "20px", color: "#a78bfa", fontVariationSettings: "'FILL' 1" }}>
                      workspace_premium
                    </span>
                  </div>
                )}

                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                    style={{
                      background: mastered
                        ? "linear-gradient(135deg,#a78bfa,#7c3aed)"
                        : "linear-gradient(135deg,#667eea,#764ba2)",
                      boxShadow: "0 4px 12px rgba(151,169,255,.15)",
                    }}>
                    <span className="material-symbols-outlined text-white"
                      style={{ fontSize: "20px", fontVariationSettings: "'FILL' 1" }}>
                      {TOPIC_ICONS[i]}
                    </span>
                  </div>
                  <span className="text-xs font-bold px-2 py-1 rounded-full"
                    style={{ color: badgeColor, background: `${badgeColor}18` }}>
                    {badgeLabel}
                  </span>
                </div>

                <p className="text-xs font-bold text-on-surface-variant mb-1">Modül {topicId}</p>
                <h3 className="text-sm font-bold text-on-surface mb-4 leading-tight group-hover:text-primary transition-colors">
                  {topicName}
                </h3>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-on-surface-variant">
                      {studied ? `${LEVEL_LABEL[currentLevel]} Seviye` : "İlerleme"}
                    </span>
                    <span className="font-bold text-primary">{pct}%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full overflow-hidden" style={{ background: "rgba(151,169,255,.08)" }}>
                    <motion.div
                      className="h-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.8, delay: i * 0.05, ease: "easeOut" }}
                      style={{
                        background: mastered
                          ? "linear-gradient(90deg,#a78bfa,#7c3aed)"
                          : pct >= 80
                          ? "linear-gradient(90deg,#34d399,#059669)"
                          : "linear-gradient(90deg,#667eea,#f093fb)",
                      }}
                    />
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-1.5 text-xs text-on-surface-variant group-hover:text-primary transition-colors">
                  <span className="material-symbols-outlined" style={{ fontSize: "14px" }}>
                    {mastered ? "replay" : locked ? "lock" : "play_circle"}
                  </span>
                  {mastered ? "Tekrar Çalış" : locked ? "Kilitli" : "Konuyu Çalış"}
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
