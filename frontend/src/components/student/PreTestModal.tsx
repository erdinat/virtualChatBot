import { motion, AnimatePresence } from "framer-motion";
import type { PreTestState, TopicLevel } from "./types";
import { LEVEL_META } from "./types";

interface Props {
  preTest: PreTestState | null;
  onClose: () => void;
  onAnswer: (step: number, optionIndex: number) => void;
  onNext: () => void;
  onSubmit: (preTest: PreTestState) => Promise<void>;
  onStartChat: (topicId: number, topicName: string, level: TopicLevel) => void;
}

export default function PreTestModal({ preTest, onClose, onAnswer, onNext, onSubmit, onStartChat }: Props) {
  return (
    <AnimatePresence>
      {preTest && (
        <>
          <motion.div key="pretest-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/75 z-50" />
          <motion.div key="pretest-modal" initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.92 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="glass-card rounded-3xl p-8 w-full max-w-lg border shadow-2xl"
              style={{ borderColor: "rgba(151,169,255,.2)", background: "#13102e" }}>

              {preTest.result ? (
                /* Sonuç ekranı */
                <div className="flex flex-col items-center gap-6 py-2">
                  <div className="w-16 h-16 rounded-full gradient-bg flex items-center justify-center shadow-xl">
                    <span className="material-symbols-outlined text-white text-3xl"
                      style={{ fontVariationSettings: "'FILL' 1" }}>
                      {preTest.result.level === "advanced" ? "emoji_events" : preTest.result.level === "intermediate" ? "trending_up" : "school"}
                    </span>
                  </div>
                  <div className="text-center">
                    <p className="text-xs uppercase font-bold tracking-widest text-on-surface-variant mb-2">Ön Test Sonucu</p>
                    <h2 className="text-xl font-bold text-on-surface mb-1">{preTest.topicName}</h2>
                    <p className="text-sm text-on-surface-variant mb-4">
                      {preTest.result.score}/{preTest.result.total} doğru cevap
                    </p>
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold"
                      style={{ background: LEVEL_META[preTest.result.level].bg, color: LEVEL_META[preTest.result.level].color }}>
                      <span className="material-symbols-outlined" style={{ fontSize: "18px", fontVariationSettings: "'FILL' 1" }}>verified</span>
                      Seviyeniz: {LEVEL_META[preTest.result.level].label}
                    </div>
                    <p className="text-xs text-on-surface-variant mt-4 leading-relaxed max-w-xs mx-auto">
                      {preTest.result.level === "beginner" && "Temel kavramlardan başlayarak adım adım ilerleyeceğiz."}
                      {preTest.result.level === "intermediate" && "Temel bilgilerini biliyorsun; orta-ileri konulara odaklanacağız."}
                      {preTest.result.level === "advanced" && "Yetkin seviyedesin! Zorlu örnekler ve Pythonic kalıplarla devam edeceğiz."}
                    </p>
                  </div>
                  <button
                    onClick={() => onStartChat(preTest.topicId, preTest.topicName, preTest.result!.level)}
                    className="w-full py-4 rounded-2xl text-sm font-bold text-white gradient-bg shadow-xl">
                    Öğrenmeye Başla →
                  </button>
                  <button onClick={onClose} className="text-xs text-on-surface-variant hover:text-on-surface transition-colors">
                    İptal
                  </button>
                </div>
              ) : (
                /* Soru ekranı */
                <>
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <p className="text-xs uppercase font-bold tracking-widest text-on-surface-variant mb-1">Ön Test</p>
                      <h2 className="text-base font-bold text-on-surface">{preTest.topicName}</h2>
                    </div>
                    <span className="text-xs font-bold text-primary px-3 py-1 rounded-full"
                      style={{ background: "rgba(151,169,255,.1)" }}>
                      {preTest.step + 1} / {preTest.questions.length}
                    </span>
                  </div>

                  <div className="h-1 w-full rounded-full mb-6" style={{ background: "rgba(151,169,255,.12)" }}>
                    <div className="h-full rounded-full gradient-bg transition-all duration-300"
                      style={{ width: `${(preTest.step / preTest.questions.length) * 100}%` }} />
                  </div>

                  <p className="text-sm font-medium text-on-surface leading-relaxed mb-6">
                    {preTest.questions[preTest.step].text}
                  </p>

                  <div className="space-y-3">
                    {preTest.questions[preTest.step].options.map((opt, i) => {
                      const letters = ["A", "B", "C", "D"];
                      const selected = preTest.answers[preTest.step] === i;
                      return (
                        <button key={i}
                          onClick={() => onAnswer(preTest.step, i)}
                          className="w-full flex items-center gap-4 px-5 py-3 rounded-xl text-sm text-left transition-all"
                          style={{
                            background: selected ? "rgba(151,169,255,.15)" : "rgba(255,255,255,.04)",
                            border: selected ? "1px solid rgba(151,169,255,.4)" : "1px solid rgba(255,255,255,.08)",
                            color: selected ? "#97a9ff" : "rgba(255,255,255,.75)",
                          }}>
                          <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                            style={{
                              background: selected ? "rgba(151,169,255,.25)" : "rgba(255,255,255,.07)",
                              color: selected ? "#97a9ff" : "rgba(255,255,255,.5)",
                            }}>
                            {letters[i]}
                          </span>
                          {opt}
                        </button>
                      );
                    })}
                  </div>

                  <button
                    disabled={preTest.answers[preTest.step] === undefined}
                    onClick={async () => {
                      const isLast = preTest.step === preTest.questions.length - 1;
                      if (!isLast) onNext();
                      else await onSubmit(preTest);
                    }}
                    className="mt-6 w-full py-3 rounded-xl text-sm font-bold text-white gradient-bg disabled:opacity-40 transition-opacity">
                    {preTest.step < preTest.questions.length - 1 ? "Sonraki Soru →" : "Seviyemi Belirle"}
                  </button>

                  <button onClick={onClose}
                    className="mt-3 w-full text-center text-xs text-on-surface-variant hover:text-on-surface transition-colors py-2">
                    İptal
                  </button>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
