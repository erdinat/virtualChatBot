import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { getDiagnosticQuestions, submitDiagnostic } from "../api/client";
import { useAuthStore } from "../store/authStore";

interface Question {
  topic_id: number;
  text: string;
  options: string[];
}

export default function DiagnosticPage() {
  const navigate = useNavigate();
  const { username } = useAuthStore();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<{ score: number; total: number; message: string } | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["diagnostic"],
    queryFn: getDiagnosticQuestions,
    retry: false,
  });

  const submitMutation = useMutation({
    mutationFn: submitDiagnostic,
    onSuccess: (res) => {
      // Mark diagnostic as done in localStorage so the route guard skips it next time
      if (username) localStorage.setItem(`diagnostic_done_${username}`, "1");
      setResult(res);
      setSubmitted(true);
    },
    onError: () => toast.error("Gönderim hatası, tekrar dene."),
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="flex items-center gap-3 text-on-surface-variant">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Sorular yükleniyor…</span>
        </div>
      </div>
    );
  }

  if (data?.already_done) {
    if (username) localStorage.setItem(`diagnostic_done_${username}`, "1");
    navigate("/student", { replace: true });
    return null;
  }

  const questions: Question[] = data?.questions ?? [];
  if (!questions.length) return null;

  const current = questions[step];
  const letters = ["A", "B", "C", "D"];
  const progress = ((step) / questions.length) * 100;

  if (submitted && result) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card rounded-3xl p-10 max-w-md w-full text-center border shadow-2xl"
          style={{ borderColor: "rgba(151,169,255,.2)", background: "#13102e" }}
        >
          <div className="w-20 h-20 rounded-full gradient-bg flex items-center justify-center mx-auto mb-6 shadow-xl">
            <span className="material-symbols-outlined text-white text-4xl"
              style={{ fontVariationSettings: "'FILL' 1" }}>school</span>
          </div>
          <h1 className="text-2xl font-bold text-on-surface mb-2">Seviye Belirlendi!</h1>
          <p className="text-on-surface-variant text-sm mb-4">{result.message}</p>
          <div className="flex items-center justify-center gap-2 mb-8">
            <span className="text-4xl font-black gradient-text">{result.score}</span>
            <span className="text-2xl text-on-surface-variant font-bold">/ {result.total}</span>
          </div>
          <p className="text-xs text-on-surface-variant mb-8 leading-relaxed">
            Başlangıç bilgi seviyeniz belirlendi. Sistem artık sana özel bir öğrenme yolu oluşturacak.
          </p>
          <button
            onClick={() => navigate("/student")}
            className="w-full py-4 rounded-2xl text-white font-bold gradient-bg shadow-xl text-sm"
          >
            Öğrenmeye Başla →
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface p-6"
      style={{ background: "radial-gradient(ellipse at 50% 0%, rgba(92,49,135,.15) 0%, transparent 70%), #0d0a27" }}>
      <div className="w-full max-w-xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex items-center justify-center gap-3 mb-3">
            <span className="material-symbols-outlined text-primary text-3xl"
              style={{ fontVariationSettings: "'FILL' 1" }}>quiz</span>
            <h1 className="text-xl font-bold gradient-text">Seviye Tespit Sınavı</h1>
          </div>
          <p className="text-xs text-on-surface-variant">
            10 kısa soru ile başlangıç bilgi seviyeni belirliyoruz
          </p>
        </motion.div>

        {/* Progress */}
        <div className="mb-6">
          <div className="flex justify-between text-xs text-on-surface-variant mb-2 px-1">
            <span>Soru {step + 1} / {questions.length}</span>
            <span>{Math.round(progress)}% tamamlandı</span>
          </div>
          <div className="h-2 w-full rounded-full" style={{ background: "rgba(151,169,255,.1)" }}>
            <motion.div
              className="h-full rounded-full gradient-bg"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.4 }}
            />
          </div>
        </div>

        {/* Question card */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.2 }}
            className="glass-card rounded-3xl p-8 border shadow-2xl"
            style={{ borderColor: "rgba(151,169,255,.15)", background: "#13102e" }}
          >
            <p className="text-sm font-medium text-on-surface leading-relaxed mb-7">
              {current.text}
            </p>

            <div className="space-y-3">
              {current.options.map((opt, i) => {
                const selected = answers[String(current.topic_id)] === letters[i];
                return (
                  <button
                    key={i}
                    onClick={() =>
                      setAnswers((prev) => ({ ...prev, [String(current.topic_id)]: letters[i] }))
                    }
                    className="w-full flex items-center gap-4 px-5 py-3.5 rounded-xl text-sm text-left transition-all"
                    style={{
                      background: selected ? "rgba(151,169,255,.15)" : "rgba(255,255,255,.04)",
                      border: selected ? "1px solid rgba(151,169,255,.4)" : "1px solid rgba(255,255,255,.08)",
                      color: selected ? "#97a9ff" : "rgba(255,255,255,.75)",
                    }}
                  >
                    <span className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
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
              disabled={!answers[String(current.topic_id)]}
              onClick={() => {
                const isLast = step === questions.length - 1;
                if (!isLast) {
                  setStep((s) => s + 1);
                } else {
                  submitMutation.mutate(answers);
                }
              }}
              className="mt-7 w-full py-3.5 rounded-2xl text-sm font-bold text-white gradient-bg disabled:opacity-40 transition-opacity shadow-lg"
            >
              {step < questions.length - 1 ? "Sonraki Soru →" : "Sınavı Tamamla ✓"}
            </button>
          </motion.div>
        </AnimatePresence>

        <p className="text-center text-xs text-on-surface-variant mt-6 opacity-50">
          Bu sınav puanlamaya etki etmez, sadece senin için en iyi öğrenme yolunu belirler.
        </p>
      </div>
    </div>
  );
}
