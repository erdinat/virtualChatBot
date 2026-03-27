import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useAuthStore } from "../store/authStore";
import { getMyMastery, getNextTopic, askQuestion, sendFeedback } from "../api/client";

interface Message {
  role: "user" | "assistant";
  content: string;
  topicId?: number | null;
}

// Backend CURRICULUM ile birebir eşleşen konu isimleri
const TOPICS = [
  "Değişkenler ve Veri Tipleri",
  "Operatörler ve İfadeler",
  "Koşul İfadeleri (if/elif/else)",
  "Döngüler (for/while)",
  "Listeler ve Tuple'lar",
  "Sözlükler ve Kümeler",
  "Fonksiyonlar",
  "Dosya İşlemleri",
  "Hata Yönetimi (try/except)",
  "Nesne Yönelimli Programlama (OOP)",
];

function MasteryBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs px-1">
        <span className="text-on-surface-variant">{label}</span>
        <span className="text-primary font-bold">{pct}%</span>
      </div>
      <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
        <motion.div
          className="h-full shimmer-bar"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

function ChatBubble({ msg, isLast, onFeedback }: {
  msg: Message;
  isLast: boolean;
  onFeedback?: (correct: boolean) => void;
}) {
  const isUser = msg.role === "user";

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col gap-2 max-w-2xl ml-auto items-end mb-8"
      >
        <div className="px-6 py-4 rounded-tl-3xl rounded-bl-3xl rounded-br-3xl shadow-xl text-sm leading-relaxed text-white"
          style={{ background: "#667eea", boxShadow: "0 8px 24px rgba(102,126,234,.15)" }}>
          {msg.content}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-3 max-w-2xl mb-8"
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full flex items-center justify-center shadow-lg shrink-0"
          style={{ background: "linear-gradient(135deg,#667eea,#764ba2,#f093fb)", boxShadow: "0 4px 12px rgba(151,169,255,.2)" }}>
          <span className="material-symbols-outlined text-white text-sm" style={{ fontSize: "16px", fontVariationSettings: "'FILL' 1" }}>auto_fix_high</span>
        </div>
        <span className="text-xs font-bold text-on-surface-variant tracking-widest uppercase">Sanal Öğretmen</span>
        {isLast && (
          <div className="flex items-center gap-1.5 ml-auto">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse-dot" />
            <span className="text-xs text-on-surface-variant font-medium">Aktif Öğrenme</span>
          </div>
        )}
      </div>

      <div className="glass-card p-6 rounded-tr-3xl rounded-br-3xl rounded-bl-3xl shadow-2xl">
        <p className="text-on-surface leading-relaxed text-sm whitespace-pre-wrap"
          dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
      </div>

      {isLast && msg.topicId !== null && msg.topicId !== undefined && onFeedback && (
        <div className="flex gap-2">
          <button
            onClick={() => onFeedback(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-colors"
            style={{ border: "1px solid rgba(74,222,128,.3)", background: "rgba(74,222,128,.05)", color: "#4ade80" }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: "16px" }}>thumb_up</span>
            Anladım
          </button>
          <button
            onClick={() => onFeedback(false)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-colors"
            style={{ border: "1px solid rgba(255,110,132,.3)", background: "rgba(255,110,132,.05)", color: "#ff6e84" }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: "16px" }}>thumb_down</span>
            Anlamadım
          </button>
        </div>
      )}
    </motion.div>
  );
}

/** Wrap `code` in styled spans and newlines for HTML rendering */
function formatMessage(text: string): string {
  return text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/`([^`]+)`/g, '<code style="background:#2a2653;padding:2px 6px;border-radius:4px;color:#97a9ff;font-family:monospace;font-size:0.85em">$1</code>')
    .replace(/\n/g, "<br/>");
}

export default function StudentPage() {
  const { name, username, logout } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Merhaba! 👋 Bugün Python hakkında ne öğrenmek istersin? Sana Sokratik yöntemle rehberlik edeceğim." },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const qc = useQueryClient();

  const { data: mastery } = useQuery({ queryKey: ["mastery"], queryFn: getMyMastery, refetchInterval: 15000 });
  const { data: nextTopic } = useQuery({ queryKey: ["nextTopic"], queryFn: getNextTopic });

  const feedbackMutation = useMutation({
    mutationFn: ({ topic_id, correct }: { topic_id: number | null; correct: boolean }) =>
      sendFeedback(topic_id, correct),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mastery"] }),
  });

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  function sendMessage() {
    if (!input.trim() || streaming) return;
    const question = input.trim();
    setInput("");

    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content: question }]);

    let buffer = "";
    setStreaming(true);
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    askQuestion(
      question,
      history,
      (token) => {
        buffer += token;
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "assistant", content: buffer };
          return updated;
        });
      },
      (tid) => {
        setStreaming(false);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { ...updated[updated.length - 1], topicId: tid };
          return updated;
        });
      },
    );
  }

  const masteryMap: Record<string, number> = mastery?.mastery ?? {};
  const avgMastery = Object.values(masteryMap).length
    ? (Object.values(masteryMap) as number[]).reduce((a, b) => a + b, 0) / Object.values(masteryMap).length
    : 0;

  const initials = (name ?? username ?? "?")[0].toUpperCase();

  return (
    <div className="flex h-screen overflow-hidden bg-surface text-on-surface font-body">
      {/* ── Sidebar ────────────────────────────────────── */}
      <aside className="w-80 h-full bg-surface-container border-r border-white/5 flex flex-col py-8 overflow-y-auto z-50">
        {/* Logo */}
        <div className="px-6 mb-8 flex items-center gap-3">
          <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>school</span>
          <h1 className="text-xl font-bold gradient-text tracking-tight">Sanal Öğretmen</h1>
        </div>

        {/* User profile */}
        <div className="flex items-center gap-4 mb-10 mx-6 p-4 rounded-xl bg-surface-container-low border border-white/5">
          <div className="w-12 h-12 rounded-full gradient-bg flex items-center justify-center font-bold text-white text-lg shrink-0">
            {initials}
          </div>
          <div>
            <p className="text-on-surface font-semibold text-sm">{name}</p>
            <p className="text-on-surface-variant text-xs">Python Öğrencisi</p>
          </div>
        </div>

        {/* Mastery section */}
        <div className="px-6 mb-6">
          <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-6 px-1">
            Bilgi Seviyeniz
          </h3>
          <div className="space-y-5">
            {TOPICS.map((t) => (
              <MasteryBar key={t} label={t} value={masteryMap[t] ?? 0} />
            ))}
          </div>
        </div>

        {/* AI recommendation */}
        <div className="mx-6 mt-auto pt-6 border-t border-white/5">
          {nextTopic?.topic?.name ? (
            <div className="p-4 rounded-xl border"
              style={{ background: "rgba(92,49,135,.2)", borderColor: "rgba(92,49,135,.3)" }}>
              <p className="text-xs uppercase font-bold text-secondary mb-2">Yapay Zeka Önerisi</p>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary" style={{ fontSize: "20px" }}>auto_awesome</span>
                <span className="text-sm font-medium text-on-secondary-container leading-tight">
                  Önerilen: '{nextTopic.topic.name}'
                </span>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl border"
              style={{ background: "rgba(92,49,135,.2)", borderColor: "rgba(92,49,135,.3)" }}>
              <p className="text-xs uppercase font-bold text-secondary mb-2">Genel İlerleme</p>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary" style={{ fontSize: "20px" }}>auto_awesome</span>
                <span className="text-sm font-medium text-on-secondary-container">
                  Ort. %{Math.round(avgMastery * 100)} hakimiyet
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Logout */}
        <button
          onClick={() => { logout(); window.location.href = "/"; }}
          className="mt-6 mx-6 flex items-center gap-3 text-on-surface-variant hover:text-error transition-colors px-4 py-3 group"
        >
          <span className="material-symbols-outlined group-hover:scale-110 transition-transform" style={{ fontSize: "20px" }}>logout</span>
          <span className="text-sm font-medium">Çıkış Yap</span>
        </button>
      </aside>

      {/* ── Chat area ──────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden bg-surface">
        {/* Mobile header */}
        <header className="md:hidden flex items-center justify-between px-6 py-4 border-b border-white/5 z-40"
          style={{ background: "rgba(24,21,56,.8)", backdropFilter: "blur(16px)" }}>
          <span className="material-symbols-outlined text-on-surface">menu</span>
          <h2 className="text-lg font-bold gradient-text">Sanal Öğretmen</h2>
          <div className="w-8 h-8 rounded-full flex items-center justify-center gradient-bg">
            <span className="text-white text-sm font-bold">{initials}</span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <AnimatePresence initial={false}>
            {messages.map((m, i) => (
              <ChatBubble
                key={i}
                msg={m}
                isLast={i === messages.length - 1}
                onFeedback={
                  m.role === "assistant" && i === messages.length - 1
                    ? (correct) => {
                        const tid = m.topicId ?? null;
                        feedbackMutation.mutate({ topic_id: tid, correct });
                        toast(correct ? "Harika! Devam et 🎉" : "Sorun değil, tekrar deneyelim 💪");
                      }
                    : undefined
                }
              />
            ))}
          </AnimatePresence>

          {streaming && (
            <div className="flex items-center gap-1.5 mb-6 pl-11">
              {[0, 0.15, 0.3].map((d, i) => (
                <span key={i} className="w-2 h-2 rounded-full animate-pulse-dot"
                  style={{ background: "linear-gradient(135deg,#667eea,#f093fb)", animationDelay: `${d}s` }} />
              ))}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="p-6 md:px-12 md:pb-10"
          style={{ background: "linear-gradient(to top, #0d0a27 60%, transparent)" }}>
          <div className="max-w-4xl mx-auto relative group">
            {/* Glow ring */}
            <div className="absolute -inset-1 rounded-2xl blur opacity-0 group-focus-within:opacity-40 transition-opacity"
              style={{ background: "linear-gradient(90deg,rgba(151,169,255,.3),rgba(240,147,251,.3),rgba(151,169,255,.3))" }} />
            <div className="relative glass-card flex items-center gap-4 px-6 py-4 rounded-2xl border border-white/10">
              <button className="text-on-surface-variant hover:text-primary transition-colors shrink-0">
                <span className="material-symbols-outlined" style={{ fontSize: "22px" }}>attachment</span>
              </button>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                placeholder="Python hakkında bir soru sor…"
                rows={1}
                className="flex-1 bg-transparent border-none focus:ring-0 text-on-surface text-sm resize-none outline-none placeholder:text-on-surface-variant/50"
                style={{ maxHeight: "120px" }}
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={sendMessage}
                disabled={streaming || !input.trim()}
                className="w-10 h-10 rounded-xl gradient-bg flex items-center justify-center shadow-lg disabled:opacity-40 shrink-0"
                style={{ boxShadow: "0 4px 16px rgba(151,169,255,.2)" }}
              >
                <span className="material-symbols-outlined text-white" style={{ fontSize: "18px", fontVariationSettings: "'FILL' 1" }}>send</span>
              </motion.button>
            </div>
            <p className="text-xs text-center text-on-surface-variant mt-4 opacity-50">
              Sanal Öğretmen hata yapabilir. Önemli bilgileri kontrol etmeyi unutmayın.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
