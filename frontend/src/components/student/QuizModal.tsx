import { motion, AnimatePresence } from "framer-motion";
import toast from "react-hot-toast";
import { useQueryClient } from "@tanstack/react-query";
import { sendFeedback } from "../../api/client";
import type { QuizModalState } from "./types";

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
  onQuizDone: () => void;
  onPendingAccept: (topicId: number, topicName: string) => void;
  onPendingDismiss: () => void;
}

export default function QuizModal({
  quizModal, pendingTestSuggest, activeView,
  onQuizAnswer, onQuizNext, onQuizClose, onQuizDone,
  onPendingAccept, onPendingDismiss,
}: Props) {
  const qc = useQueryClient();

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
                        <p className="text-xs uppercase font-bold tracking-widest text-on-surface-variant mb-1">Ara Değerlendirme</p>
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

                    <p className="text-sm font-medium text-on-surface leading-relaxed mb-6">
                      {quizModal.questions[quizModal.step].text}
                    </p>

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
                        if (!isLast) {
                          onQuizNext();
                        } else {
                          Promise.all(
                            Array.from({ length: quizModal.questions.length }, (_, i) =>
                              sendFeedback(quizModal.topicId, quizModal.answers[i] !== undefined)
                            )
                          ).then(() => {
                            qc.invalidateQueries({ queryKey: ["mastery"] });
                            qc.invalidateQueries({ queryKey: ["nextTopic"] });
                          });
                          onQuizDone();
                          toast.success("Test tamamlandı! 🎉");
                        }
                      }}
                      className="mt-6 w-full py-3 rounded-xl text-sm font-bold text-white gradient-bg disabled:opacity-40 transition-opacity">
                      {quizModal.step < quizModal.questions.length - 1 ? "Sonraki Soru →" : "Testi Tamamla"}
                    </button>
                  </>
                ) : (
                  <div className="flex flex-col items-center gap-6 py-4">
                    <div className="w-16 h-16 rounded-full gradient-bg flex items-center justify-center shadow-xl">
                      <span className="material-symbols-outlined text-white text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                    </div>
                    <div className="text-center">
                      <h2 className="text-xl font-bold text-on-surface mb-2">Tebrikler!</h2>
                      <p className="text-sm text-on-surface-variant">
                        <strong className="text-primary">{quizModal.topicName}</strong> ara değerlendirmesini tamamladın.
                      </p>
                    </div>
                    <button onClick={onQuizClose}
                      className="px-8 py-3 rounded-xl text-sm font-bold text-white gradient-bg shadow-lg">
                      Devam Et
                    </button>
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
