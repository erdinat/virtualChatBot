import { motion, AnimatePresence } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import DOMPurify from "dompurify";
import { assessTopicLevel } from "../../api/client";
import type { QuizModalState } from "./types";

/** Soru metnindeki ```python ... ``` bloklarını ve \n'leri render eder */
function formatQuestion(text: string): string {
  const parts = text.split(/(```[\w]*\n?[\s\S]*?```)/g);
  return parts.map((part) => {
    const block = part.match(/^```(\w*)\n?([\s\S]*?)```$/);
    if (block) {
      const code = block[2].trimEnd()
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      return `<pre style="background:#0d0b22;border:1px solid rgba(151,169,255,0.18);border-radius:8px;padding:12px 14px;margin:10px 0 4px;overflow-x:auto;white-space:pre;font-family:monospace;font-size:0.8em;line-height:1.75;color:#c8d3ff;text-align:left"><code>${code}</code></pre>`;
    }
    return part
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/`([^`]+)`/g, '<code style="background:#2a2653;padding:2px 5px;border-radius:4px;color:#97a9ff;font-family:monospace;font-size:0.85em">$1</code>')
      .replace(/\n/g, "<br/>");
  }).join("");
}

interface PendingTestSuggest {
  topicId: number;
  topicName: string;
}

interface Props {
  quizModal: QuizModalState | null;
  pendingTestSuggest: PendingTestSuggest | null;
  activeView: "curriculum" | "chat";
  onQuizAnswer: (step: number, optionIndex: number) => void;
  onQuizNext: () => void;
  onQuizClose: () => void;
  onQuizDone: (score: number, total: number) => void;
  onPendingAccept: (topicId: number, topicName: string) => void;
  onPendingDismiss: () => void;
}

export default function QuizModal({
  quizModal, pendingTestSuggest, activeView,
  onQuizAnswer, onQuizNext, onQuizClose, onQuizDone,
  onPendingAccept, onPendingDismiss,
}: Props) {
  const qc = useQueryClient();

  async function handleFinish() {
    if (!quizModal) return;

    // LLM tarafından üretilen sorular: doğru cevaplar client'ta, yerel değerlendir
    if (quizModal.correctAnswers) {
      const correct = quizModal.correctAnswers.reduce((sum, ans, i) => {
        return sum + (quizModal.answers[i] === ans ? 1 : 0);
      }, 0);
      onQuizDone(correct, quizModal.questions.length);
      return;
    }

    // Statik sorular: backend değerlendirmesi
    try {
      const answersRecord: Record<string, number> = {};
      quizModal.questions.forEach((_, i) => {
        if (quizModal.answers[i] !== undefined) {
          answersRecord[String(i)] = quizModal.answers[i];
        }
      });
      const result = await assessTopicLevel(quizModal.topicId, answersRecord);
      qc.invalidateQueries({ queryKey: ["mastery"] });
      qc.invalidateQueries({ queryKey: ["nextTopic"] });
      onQuizDone(result.score, result.total);
    } catch {
      onQuizDone(0, quizModal.questions.length);
    }
  }

  const isConceptCheck = quizModal?.mode === "concept-check";
  const isFinal = quizModal?.mode === "final";

  const passed = quizModal?.score !== undefined && quizModal.total !== undefined
    ? quizModal.score / quizModal.total >= 2 / 3
    : false;

  const modeLabel = (mode: QuizModalState["mode"]) => {
    if (mode === "concept-check") return "Kavrama Sorusu";
    if (mode === "final")         return "Final Testi";
    if (mode === "check")         return "Anlama Testi";
    return "Ara Değerlendirme";
  };

  return (
    <>
      {/* Test öneri balonu */}
      <AnimatePresence>
        {pendingTestSuggest && !quizModal && activeView === "chat" && (
          <motion.div key="test-suggest" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-36 right-6 z-50 max-w-xs glass-card p-5 rounded-2xl border shadow-2xl"
            style={{ borderColor: "rgba(151,169,255,.25)", background: "rgba(24,21,56,.95)" }}>
            <div className="flex items-start gap-3 mb-4">
              <span className="material-symbols-outlined text-primary shrink-0"
                style={{ fontSize: "24px", fontVariationSettings: "'FILL' 1" }}>quiz</span>
              <div>
                <p className="text-sm font-bold text-on-surface mb-1">Ara Değerlendirme</p>
                <p className="text-xs text-on-surface-variant leading-relaxed">
                  <strong className="text-primary">{pendingTestSuggest.topicName}</strong> konusunda kısa bir test yapalım mı? (3 soru)
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => onPendingAccept(pendingTestSuggest.topicId, pendingTestSuggest.topicName)}
                className="flex-1 py-2 rounded-xl text-xs font-bold text-white gradient-bg">
                Evet, başlayalım!
              </button>
              <button onClick={onPendingDismiss}
                className="px-4 py-2 rounded-xl text-xs font-medium text-on-surface-variant hover:text-on-surface transition-colors"
                style={{ background: "rgba(255,255,255,.06)" }}>
                Daha sonra
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quiz modal */}
      <AnimatePresence>
        {quizModal && (
          <>
            <motion.div key="quiz-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/70 z-50" />
            <motion.div key="quiz-modal" initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.92 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div className="glass-card rounded-3xl p-8 w-full max-w-lg border shadow-2xl"
                style={{ borderColor: "rgba(151,169,255,.2)", background: "#13102e" }}>

                {!quizModal.done ? (
                  <>
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <p className="text-xs uppercase font-bold tracking-widest text-on-surface-variant mb-1">
                          {modeLabel(quizModal.mode)}
                        </p>
                        <h2 className="text-base font-bold text-on-surface">{quizModal.topicName}</h2>
                      </div>
                      <span className="text-xs font-bold text-primary px-3 py-1 rounded-full"
                        style={{ background: "rgba(151,169,255,.1)" }}>
                        {quizModal.step + 1} / {quizModal.questions.length}
                      </span>
                    </div>

                    <div className="h-1 w-full rounded-full mb-6" style={{ background: "rgba(151,169,255,.12)" }}>
                      <div className="h-full rounded-full gradient-bg transition-all duration-300"
                        style={{ width: `${(quizModal.step / quizModal.questions.length) * 100}%` }} />
                    </div>

                    <div className="text-sm font-medium text-on-surface leading-relaxed mb-6"
                      dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(formatQuestion(quizModal.questions[quizModal.step].text)) }}
                    />

                    <div className="space-y-3">
                      {quizModal.questions[quizModal.step].options.map((opt, i) => {
                        const letters = ["A", "B", "C", "D"];
                        const selected = quizModal.answers[quizModal.step] === i;
                        return (
                          <button key={i}
                            onClick={() => onQuizAnswer(quizModal.step, i)}
                            className="w-full flex items-center gap-4 px-5 py-3 rounded-xl text-sm text-left transition-all"
                            style={{
                              background: selected ? "rgba(151,169,255,.15)" : "rgba(255,255,255,.04)",
                              border: selected ? "1px solid rgba(151,169,255,.4)" : "1px solid rgba(255,255,255,.08)",
                              color: selected ? "#97a9ff" : "rgba(255,255,255,.75)",
                            }}>
                            <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                              style={{ background: selected ? "rgba(151,169,255,.25)" : "rgba(255,255,255,.07)", color: selected ? "#97a9ff" : "rgba(255,255,255,.5)" }}>
                              {letters[i]}
                            </span>
                            {opt}
                          </button>
                        );
                      })}
                    </div>

                    <button
                      disabled={quizModal.answers[quizModal.step] === undefined}
                      onClick={() => {
                        const isLast = quizModal.step === quizModal.questions.length - 1;
                        if (isLast) {
                          handleFinish();
                        } else {
                          onQuizNext();
                        }
                      }}
                      className="mt-6 w-full py-3 rounded-xl text-sm font-bold text-white gradient-bg disabled:opacity-40 transition-opacity">
                      {quizModal.step < quizModal.questions.length - 1 ? "Sonraki Soru →" : "Testi Tamamla"}
                    </button>
                  </>
                ) : (
                  /* ── Sonuç ekranı ── */
                  <div className="flex flex-col items-center gap-6 py-4">

                    {/* Concept-check done screen */}
                    {isConceptCheck && (
                      <>
                        <div className="w-16 h-16 rounded-full flex items-center justify-center shadow-xl"
                          style={{ background: passed ? "linear-gradient(135deg,#34d399,#059669)" : "linear-gradient(135deg,#f87171,#dc2626)" }}>
                          <span className="material-symbols-outlined text-white text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                            {passed ? "check_circle" : "close"}
                          </span>
                        </div>
                        <div className="text-center">
                          <h2 className="text-xl font-bold text-on-surface mb-2">
                            {passed ? "Doğru! 🎉" : "Yanlış 🤔"}
                          </h2>
                          <p className="text-sm text-on-surface-variant">
                            {passed
                              ? "Kavramı anladığın belli, devam edelim!"
                              : "Konuyu biraz daha açıklayalım."}
                          </p>
                        </div>
                        <button onClick={onQuizClose}
                          className="px-8 py-3 rounded-xl text-sm font-bold text-white gradient-bg shadow-lg">
                          {passed ? "Devam Et →" : "Yeniden Açıkla"}
                        </button>
                      </>
                    )}

                    {/* Final test done screen */}
                    {isFinal && (
                      <>
                        <div className="w-16 h-16 rounded-full flex items-center justify-center shadow-xl"
                          style={{ background: passed ? "linear-gradient(135deg,#fbbf24,#d97706)" : "linear-gradient(135deg,#f87171,#dc2626)" }}>
                          <span className="material-symbols-outlined text-white text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                            {passed ? "emoji_events" : "replay"}
                          </span>
                        </div>
                        <div className="text-center">
                          <h2 className="text-xl font-bold text-on-surface mb-2">
                            {passed ? "Konuyu Tamamladın! 🏆" : "Biraz daha çalışalım 💪"}
                          </h2>
                          <p className="text-sm text-on-surface-variant mb-1">
                            <strong className="text-primary">{quizModal.topicName}</strong>
                          </p>
                          {quizModal.score !== undefined && quizModal.total !== undefined && (
                            <p className="text-2xl font-bold mt-3" style={{ color: passed ? "#fbbf24" : "#f87171" }}>
                              {quizModal.score} / {quizModal.total} doğru
                            </p>
                          )}
                          {passed && (
                            <p className="text-xs mt-3 px-4 py-2 rounded-lg leading-relaxed"
                              style={{ background: "rgba(167,139,250,.12)", color: "rgba(167,139,250,.9)" }}>
                              {(quizModal.score ?? 0) === (quizModal.total ?? 3)
                                ? "Mükemmel! Bir sonraki konu orta seviyeden başlayacak 🚀"
                                : "İyi iş! Bir sonraki konu başlangıç seviyesinden başlayacak 📚"}
                            </p>
                          )}
                          {!passed && (
                            <p className="text-xs text-on-surface-variant mt-2">
                              Konuyu biraz daha pekiştirmen gerekiyor.
                            </p>
                          )}
                        </div>
                        <button onClick={onQuizClose}
                          className="px-8 py-3 rounded-xl text-sm font-bold text-white gradient-bg shadow-lg">
                          {passed ? "Sonraki Konuya Geç →" : "Tekrar Çalış"}
                        </button>
                      </>
                    )}

                    {/* Check / review done screen */}
                    {!isConceptCheck && !isFinal && (
                      <>
                        <div className="w-16 h-16 rounded-full flex items-center justify-center shadow-xl"
                          style={{ background: passed ? "linear-gradient(135deg,#34d399,#059669)" : "linear-gradient(135deg,#f87171,#dc2626)" }}>
                          <span className="material-symbols-outlined text-white text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                            {passed ? "check_circle" : "replay"}
                          </span>
                        </div>
                        <div className="text-center">
                          <h2 className="text-xl font-bold text-on-surface mb-2">
                            {passed ? "Harika! 🎉" : "Biraz daha çalışalım 💪"}
                          </h2>
                          <p className="text-sm text-on-surface-variant mb-1">
                            <strong className="text-primary">{quizModal.topicName}</strong>
                          </p>
                          {quizModal.score !== undefined && quizModal.total !== undefined && (
                            <p className="text-2xl font-bold mt-3" style={{ color: passed ? "#34d399" : "#f87171" }}>
                              {quizModal.score} / {quizModal.total} doğru
                            </p>
                          )}
                          <p className="text-xs text-on-surface-variant mt-2">
                            {passed
                              ? "Bir sonraki seviyeye geçmeye hazırsın!"
                              : "Konuyu biraz daha pekiştirmen gerekiyor."}
                          </p>
                        </div>
                        <button onClick={onQuizClose}
                          className="px-8 py-3 rounded-xl text-sm font-bold text-white gradient-bg shadow-lg">
                          {passed ? "Devam Et →" : "Tekrar Çalış"}
                        </button>
                      </>
                    )}

                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
