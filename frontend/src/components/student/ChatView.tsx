import { useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import DOMPurify from "dompurify";
import type { Message, TopicLevel } from "./types";
import { TOPIC_PROMPTS } from "./types";

// ── formatMessage ────────────────────────────────────────────────────────────

function formatMessage(raw: string): string {
  const parts = raw.split(/(```[\w]*\n?[\s\S]*?```)/g);
  return parts.map((part) => {
    const blockMatch = part.match(/^```(\w*)\n?([\s\S]*?)```$/);
    if (blockMatch) {
      const lang = blockMatch[1];
      const code = blockMatch[2].trim()
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      const label = lang
        ? `<span style="display:block;font-size:10px;font-family:monospace;opacity:0.45;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px">${lang}</span>`
        : "";
      return `<pre style="background:#12102e;border:1px solid rgba(151,169,255,0.12);border-radius:10px;padding:14px 16px;margin:12px 0;overflow-x:auto;white-space:pre;font-family:monospace;font-size:0.82em;line-height:1.7;color:#c8d3ff">${label}<code>${code}</code></pre>`;
    }
    return part
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/`([^`]+)`/g, '<code style="background:#2a2653;padding:2px 6px;border-radius:4px;color:#97a9ff;font-family:monospace;font-size:0.85em">$1</code>')
      .replace(/\n/g, "<br/>");
  }).join("");
}

// ── ChatBubble ───────────────────────────────────────────────────────────────

function ChatBubble({ msg, isLast, onFeedback }: {
  msg: Message; isLast: boolean; onFeedback?: (correct: boolean) => void;
}) {
  const isUser = msg.role === "user";
  if (isUser) {
    return (
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="flex flex-col gap-2 max-w-2xl ml-auto items-end mb-8">
        <div className="px-6 py-4 rounded-tl-3xl rounded-bl-3xl rounded-br-3xl shadow-xl text-sm leading-relaxed text-white"
          style={{ background: "#667eea", boxShadow: "0 8px 24px rgba(102,126,234,.15)" }}>
          {msg.content}
        </div>
      </motion.div>
    );
  }
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-3 max-w-2xl mb-8">
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
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(formatMessage(msg.content)) }} />
      </div>
      {isLast && msg.topicId !== null && msg.topicId !== undefined && onFeedback && (
        <div className="flex gap-2">
          <button onClick={() => onFeedback(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-colors"
            style={{ border: "1px solid rgba(74,222,128,.3)", background: "rgba(74,222,128,.05)", color: "#4ade80" }}>
            <span className="material-symbols-outlined" style={{ fontSize: "16px" }}>thumb_up</span>
            Anladım
          </button>
          <button onClick={() => onFeedback(false)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-colors"
            style={{ border: "1px solid rgba(255,110,132,.3)", background: "rgba(255,110,132,.05)", color: "#ff6e84" }}>
            <span className="material-symbols-outlined" style={{ fontSize: "16px" }}>thumb_down</span>
            Anlamadım
          </button>
        </div>
      )}
    </motion.div>
  );
}

// ── ChatView ─────────────────────────────────────────────────────────────────

interface Props {
  messages: Message[];
  input: string;
  streaming: boolean;
  selectedTopic: { id: number; name: string; level: TopicLevel } | null;
  onInputChange: (val: string) => void;
  onSend: () => void;
  onFeedback: (topicId: number | null | undefined, correct: boolean) => void;
  onPromptClick: (prompt: string) => void;
}

export default function ChatView({
  messages, input, streaming, selectedTopic,
  onInputChange, onSend, onFeedback, onPromptClick,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }

  return (
    <>
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <AnimatePresence initial={false}>
          {messages.map((m, i) => (
            <ChatBubble
              key={m.id}
              msg={m}
              isLast={i === messages.length - 1}
              onFeedback={
                m.role === "assistant" && i === messages.length - 1
                  ? (correct) => onFeedback(m.topicId, correct)
                  : undefined
              }
            />
          ))}
        </AnimatePresence>

        {streaming && (
          <div className="flex items-center gap-2 mb-6 pl-11">
            <div className="flex items-center gap-1.5">
              {[0, 0.15, 0.3].map((d, i) => (
                <span key={i} className="w-2 h-2 rounded-full animate-pulse-dot"
                  style={{ background: "linear-gradient(135deg,#667eea,#f093fb)", animationDelay: `${d}s` }} />
              ))}
            </div>
            <span className="text-xs text-on-surface-variant">Sanal Öğretmen yazıyor…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="p-6 md:px-12 md:pb-10"
        style={{ background: "linear-gradient(to top, #0d0a27 60%, transparent)" }}>
        <div className="max-w-4xl mx-auto">
          {selectedTopic && messages.length < 3 && !streaming && (
            <div className="flex flex-wrap gap-2 mb-3">
              {(TOPIC_PROMPTS[selectedTopic.id] ?? []).map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => {
                    onPromptClick(prompt);
                    setTimeout(() => textareaRef.current?.focus(), 0);
                  }}
                  className="text-xs px-3 py-1.5 rounded-full border transition-all hover:scale-105 active:scale-95"
                  style={{
                    background: "rgba(151,169,255,.07)",
                    borderColor: "rgba(151,169,255,.22)",
                    color: "rgba(151,169,255,.85)",
                    cursor: "pointer",
                  }}>
                  {prompt}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="max-w-4xl mx-auto relative group">
          <div className="absolute -inset-1 rounded-2xl blur opacity-0 group-focus-within:opacity-40 transition-opacity"
            style={{ background: "linear-gradient(90deg,rgba(151,169,255,.3),rgba(240,147,251,.3),rgba(151,169,255,.3))" }} />
          <div className="relative glass-card flex items-end gap-4 px-6 py-4 rounded-2xl border border-white/10">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => { onInputChange(e.target.value); autoResize(); }}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); } }}
              placeholder={selectedTopic ? `${selectedTopic.name} hakkında soru sor…` : "Python hakkında bir soru sor…"}
              rows={1}
              className="flex-1 bg-transparent border-none focus:ring-0 text-on-surface text-sm resize-none outline-none placeholder:text-on-surface-variant/50"
              style={{ maxHeight: "120px", overflowY: "auto" }}
            />
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={onSend} disabled={streaming || !input.trim()}
              className="w-10 h-10 rounded-xl gradient-bg flex items-center justify-center shadow-lg disabled:opacity-40 shrink-0"
              style={{ boxShadow: "0 4px 16px rgba(151,169,255,.2)" }}>
              <span className="material-symbols-outlined text-white" style={{ fontSize: "18px", fontVariationSettings: "'FILL' 1" }}>send</span>
            </motion.button>
          </div>
          <p className="text-xs text-center text-on-surface-variant mt-4 opacity-50">
            Sanal Öğretmen hata yapabilir. Önemli bilgileri kontrol etmeyi unutmayın.
          </p>
        </div>
      </div>
    </>
  );
}
