import { useEffect, useRef, useState } from "react";
import DOMPurify from "dompurify";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useAuthStore } from "../store/authStore";
import {
  getMyMastery,
  getNextTopic,
  askQuestion,
  sendFeedback,
  getQuiz,
  assessTopicLevel,
  getChatHistory,
} from "../api/client";

// ── Types ──────────────────────────────────────────────────────────────────

type TopicLevel = "beginner" | "intermediate" | "advanced";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  topicId?: number | null;
}

interface PreTestState {
  topicId: number;
  topicName: string;
  questions: { topic_id: number; text: string; options: string[] }[];
  answers: Record<number, number>;
  step: number;
  /** null = still answering, set after backend response */
  result: { score: number; total: number; level: TopicLevel } | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

let _msgCounter = 0;
const newId = () => `m${++_msgCounter}`;

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

// Konu bazlı hazır soru önerileri (topic id 1-10 → index 0-9)
const TOPIC_PROMPTS: Record<number, string[]> = {
  1: [
    "Değişken nedir, nasıl tanımlanır?",
    "int, float, str ve bool arasındaki fark nedir?",
    "Tip dönüşümü (type casting) nasıl yapılır?",
    "None nedir, ne zaman kullanılır?",
  ],
  2: [
    "// ve % operatörleri ne işe yarar?",
    "== ile is arasındaki fark nedir?",
    "and, or, not nasıl çalışır?",
    "Karşılaştırma operatörleri nelerdir?",
  ],
  3: [
    "if-elif-else nasıl yazılır?",
    "İç içe if kullanımını göster",
    "Tek satırlık (ternary) if nasıl yazılır?",
    "Bir sayının pozitif mi negatif mi olduğunu nasıl kontrol ederim?",
  ],
  4: [
    "for döngüsü nasıl çalışır?",
    "while döngüsü ne zaman kullanılır?",
    "break ve continue ne işe yarar?",
    "range() fonksiyonunu açıklar mısın?",
  ],
  5: [
    "Liste nasıl oluşturulur ve eleman eklenir?",
    "append(), remove() ve pop() farkları nelerdir?",
    "Liste dilimleme (slicing) nasıl yapılır?",
    "Tuple ile liste arasındaki fark nedir?",
  ],
  6: [
    "Sözlük (dict) nasıl tanımlanır?",
    "Anahtar-değer çifti nasıl eklenir veya güncellenir?",
    "Küme (set) nedir, ne zaman kullanılır?",
    "Sözlükte anahtar var mı nasıl kontrol ederim?",
  ],
  7: [
    "Fonksiyon nasıl tanımlanır?",
    "Parametre ve argüman arasındaki fark nedir?",
    "return ne işe yarar?",
    "Lambda fonksiyonu ne zaman kullanılır?",
  ],
  8: [
    "Dosya nasıl açılır ve okunur?",
    "with open() neden kullanılır?",
    "CSV dosyasına nasıl yazılır?",
    "Dosya modları (r, w, a) ne anlama gelir?",
  ],
  9: [
    "try-except nasıl kullanılır?",
    "Hata türlerini (ValueError, TypeError vb.) nasıl yakalarım?",
    "finally bloğu ne işe yarar?",
    "Kendi hata sınıfımı nasıl oluştururum?",
  ],
  10: [
    "Sınıf (class) nasıl tanımlanır?",
    "__init__ metodu ne işe yarar?",
    "Kalıtım (inheritance) nasıl çalışır?",
    "self nedir, neden kullanılır?",
  ],
};

const TOPIC_ICONS = [
  "data_object", "calculate", "account_tree", "loop",
  "view_list", "dataset", "function", "folder_open",
  "error", "hub",
];

const LEVEL_META: Record<TopicLevel, { label: string; color: string; bg: string }> = {
  beginner:     { label: "Başlangıç", color: "#60a5fa", bg: "rgba(96,165,250,.12)" },
  intermediate: { label: "Orta",      color: "#a78bfa", bg: "rgba(167,139,250,.12)" },
  advanced:     { label: "İleri",     color: "#34d399", bg: "rgba(52,211,153,.12)" },
};

function masteryBadge(score: number): { label: string; color: string } {
  if (score >= 0.7) return { label: "Hakimiyet", color: "#34d399" };
  if (score > 0)   return { label: "Devam Ediyor", color: "#60a5fa" };
  return { label: "Başlanmadı", color: "rgba(255,255,255,.3)" };
}

/** Render markdown code blocks as styled HTML */
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

// ── Sub-components ──────────────────────────────────────────────────────────

function MasteryBar({ label, value, loading }: { label: string; value: number; loading?: boolean }) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs px-1">
        <span className="text-on-surface-variant">{label}</span>
        <span className="text-primary font-bold">{loading ? "—" : `${pct}%`}</span>
      </div>
      <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
        {loading ? (
          <div className="h-full w-full rounded-full animate-pulse" style={{ background: "rgba(151,169,255,0.15)" }} />
        ) : (
          <motion.div
            className="h-full shimmer-bar"
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        )}
      </div>
    </div>
  );
}

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

// ── Main Component ──────────────────────────────────────────────────────────

export default function StudentPage() {
  const { name, username, logout } = useAuthStore();
  const qc = useQueryClient();

  // ── View state ──────────────────────────────────────────────────────────
  const [activeView, setActiveView] = useState<"curriculum" | "chat">("curriculum");
  const [selectedTopic, setSelectedTopic] = useState<{
    id: number; name: string; level: TopicLevel;
  } | null>(null);

  // ── Pre-test state ──────────────────────────────────────────────────────
  const [preTest, setPreTest] = useState<PreTestState | null>(null);

  // ── Chat state ──────────────────────────────────────────────────────────
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ── Sidebar state ───────────────────────────────────────────────────────
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [desktopSidebar, setDesktopSidebar] = useState(true);

  // ── Chat history state ───────────────────────────────────────────────────
  const [recentHistory, setRecentHistory] = useState<{ role: string; content: string }[]>([]);

  // ── Ara değerlendirme state ─────────────────────────────────────────────
  const [quizModal, setQuizModal] = useState<{
    topicId: number; topicName: string;
    questions: { topic_id: number; text: string; options: string[] }[];
    answers: Record<number, number>; step: number; done: boolean;
  } | null>(null);
  const [pendingTestSuggest, setPendingTestSuggest] = useState<{
    topicId: number; topicName: string;
  } | null>(null);

  // ── Queries ─────────────────────────────────────────────────────────────
  const { data: mastery, isLoading: masteryLoading } = useQuery({
    queryKey: ["mastery"],
    queryFn: getMyMastery,
    refetchInterval: 15000,
  });
  const { data: nextTopic } = useQuery({ queryKey: ["nextTopic"], queryFn: getNextTopic });

  const feedbackMutation = useMutation({
    mutationFn: ({ topic_id, correct }: { topic_id: number | null; correct: boolean }) =>
      sendFeedback(topic_id, correct),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mastery"] }),
  });

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  // Suggest mid-topic test when nextTopic recommends it
  useEffect(() => {
    if (nextTopic?.suggest_test && nextTopic?.topic?.id && !streaming && !quizModal && !pendingTestSuggest) {
      setPendingTestSuggest({ topicId: nextTopic.topic.id, topicName: nextTopic.topic.name });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nextTopic?.suggest_test, nextTopic?.topic?.id, streaming]);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }

  function sendMessage() {
    if (!input.trim() || streaming) return;
    const question = input.trim();
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    const assistantId = newId();
    setMessages((prev) => [
      ...prev,
      { id: newId(), role: "user", content: question },
      { id: assistantId, role: "assistant", content: "" },
    ]);

    let buffer = "";
    setStreaming(true);

    askQuestion(
      question,
      history,
      (token) => {
        buffer += token;
        setMessages((prev) => {
          const updated = [...prev];
          const idx = updated.findIndex((m) => m.id === assistantId);
          if (idx !== -1) updated[idx] = { ...updated[idx], content: buffer };
          return updated;
        });
      },
      (tid) => {
        setStreaming(false);
        setMessages((prev) => {
          const updated = [...prev];
          const idx = updated.findIndex((m) => m.id === assistantId);
          if (idx !== -1) updated[idx] = { ...updated[idx], topicId: tid };
          return updated;
        });
        qc.invalidateQueries({ queryKey: ["nextTopic"] });
      },
      () => {
        setStreaming(false);
        toast.error("Bağlantı hatası, tekrar dene.");
        setMessages((prev) => prev.filter((m) => m.id !== assistantId));
      },
      selectedTopic?.id ?? null,
      selectedTopic?.level ?? null,
    );
  }

  // ── Enter topic flow ────────────────────────────────────────────────────
  async function openPreTest(topicId: number, topicName: string) {
    // If the student already completed a pre-test for this topic, skip straight to chat
    const cached = localStorage.getItem(`topic_level_${username}_${topicId}`) as TopicLevel | null;
    if (cached) {
      startChat(topicId, topicName, cached);
      return;
    }
    try {
      const data = await getQuiz(topicId);
      if (data.questions?.length) {
        setPreTest({
          topicId, topicName,
          questions: data.questions,
          answers: {}, step: 0, result: null,
        });
      }
    } catch {
      toast.error("Sorular yüklenemedi.");
    }
  }

  async function submitPreTest(preTestState: PreTestState) {
    try {
      const result = await assessTopicLevel(preTestState.topicId, preTestState.answers);
      setPreTest((prev) => prev ? { ...prev, result } : prev);
    } catch {
      toast.error("Seviye belirlenemedi, başlangıç seviyesi atandı.");
      setPreTest((prev) => prev ? { ...prev, result: { score: 0, total: 3, level: "beginner" } } : prev);
    }
  }

  async function startChat(topicId: number, topicName: string, level: TopicLevel, forceNew = false) {
    localStorage.setItem(`topic_level_${username}_${topicId}`, level);
    setSelectedTopic({ id: topicId, name: topicName, level });
    setActiveView("chat");
    setPreTest(null);

    const sessionStartKey = `session_start_${username}_${topicId}`;

    if (!forceNew) {
      try {
        const data = await getChatHistory(topicId);
        if (data.messages?.length) {
          // Always load all history so old conversations remain accessible.
          // If a new session was started previously, insert a visual divider at that boundary.
          const sessionStartMs = localStorage.getItem(sessionStartKey);
          const allMsgs = data.messages as { role: "user" | "assistant"; content: string; timestamp: string }[];
          const history: Message[] = [];
          let newSessionDividerAdded = false;

          for (const m of allMsgs) {
            if (sessionStartMs && !newSessionDividerAdded &&
                new Date(m.timestamp).getTime() >= parseInt(sessionStartMs)) {
              history.push({
                id: newId(), role: "assistant",
                content: "— Yeni sohbet başladı —",
              });
              newSessionDividerAdded = true;
            }
            history.push({ id: newId(), role: m.role, content: m.content });
          }

          history.push({
            id: newId(), role: "assistant",
            content: `— Sohbet geçmişin yüklendi (${allMsgs.length} mesaj). Kaldığın yerden devam edebilirsin. —`,
          });
          setMessages(history);
          setRecentHistory(allMsgs.filter((m) => m.role === "user"));
          return;
        }
      } catch { /* geçmiş yok veya hata → yeni başlangıç */ }
    }

    // Yeni sohbet
    if (forceNew) {
      // Move current user messages to sidebar so old chat stays visible
      setRecentHistory(
        messages
          .filter((m) => m.role === "user")
          .map((m) => ({ role: m.role, content: m.content }))
      );
      // Store session boundary so future history loads insert a visual divider
      localStorage.setItem(sessionStartKey, Date.now().toString());
    } else {
      setRecentHistory([]);
    }

    setMessages([{
      id: newId(),
      role: "assistant",
      content: `Merhaba! **${topicName}** konusunu öğrenmeye başlıyoruz. ${LEVEL_META[level].label} seviyesin — sana uygun örnekler ve açıklamalarla ilerleceğiz. Ne sormak istersin? 😊`,
    }]);
  }

  // ── Layout helpers ──────────────────────────────────────────────────────
  const masteryMap: Record<string, number> = mastery?.mastery ?? {};
  const avgMastery = Object.values(masteryMap).length
    ? (Object.values(masteryMap) as number[]).reduce((a, b) => a + b, 0) / Object.values(masteryMap).length
    : 0;

  const AVATAR: Record<string, string> = {
    ali: "https://cdn-icons-png.flaticon.com/512/4202/4202839.png",
    ayse: "https://cdn-icons-png.flaticon.com/512/4202/4202850.png",
    ogretmen: "https://cdn-icons-png.flaticon.com/512/4202/4202843.png",
  };
  const avatarUrl = username ? AVATAR[username] : undefined;
  const initials = (name ?? username ?? "?")[0].toUpperCase();

  // ── Sidebar content (reused desktop + mobile) ───────────────────────────
  const sidebarContent = (
    <>
      <div className="px-6 mb-8 flex items-center gap-3">
        <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>school</span>
        <h1 className="text-xl font-bold gradient-text tracking-tight">Sanal Öğretmen</h1>
      </div>

      <div className="flex items-center gap-4 mb-10 mx-6 p-4 rounded-xl bg-surface-container-low border border-white/5">
        <div className="w-12 h-12 rounded-full overflow-hidden gradient-bg flex items-center justify-center font-bold text-white text-lg shrink-0">
          {avatarUrl ? <img src={avatarUrl} alt={name ?? ""} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : initials}
        </div>
        <div>
          <p className="text-on-surface font-semibold text-sm">{name}</p>
          <p className="text-on-surface-variant text-xs">Python Öğrencisi</p>
        </div>
      </div>

      {activeView === "chat" && recentHistory.length > 0 && (
        <div className="px-6 mb-6">
          <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-3 px-1">
            Konu Geçmişi
          </h3>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {recentHistory.slice(-6).map((m, i) => (
              <div key={i} className="px-3 py-2 rounded-lg text-xs text-on-surface-variant"
                style={{ background: "rgba(255,255,255,.04)", borderLeft: "2px solid rgba(151,169,255,.3)" }}>
                <p className="truncate">{m.content.slice(0, 70)}{m.content.length > 70 ? "…" : ""}</p>
              </div>
            ))}
          </div>
        </div>
      )}

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

      <button
        onClick={() => { logout(); window.location.href = "/"; }}
        className="mt-6 mx-6 flex items-center gap-3 text-on-surface-variant hover:text-error transition-colors px-4 py-3 group"
      >
        <span className="material-symbols-outlined group-hover:scale-110 transition-transform" style={{ fontSize: "20px" }}>logout</span>
        <span className="text-sm font-medium">Çıkış Yap</span>
      </button>
    </>
  );

  // ── Render ──────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen overflow-hidden bg-surface text-on-surface font-body">
      {/* Desktop sidebar */}
      <AnimatePresence initial={false}>
        {desktopSidebar && (
          <motion.aside key="desktop-sidebar"
            initial={{ width: 0, opacity: 0 }} animate={{ width: 320, opacity: 1 }} exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            className="hidden md:flex h-full bg-surface-container border-r border-white/5 flex-col py-8 overflow-y-auto overflow-x-hidden z-50 shrink-0">
            {sidebarContent}
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div key="backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)} className="fixed inset-0 bg-black/60 z-40 md:hidden" />
            <motion.aside key="sidebar" initial={{ x: -320 }} animate={{ x: 0 }} exit={{ x: -320 }}
              transition={{ type: "tween", duration: 0.25 }}
              className="fixed left-0 top-0 w-80 h-full bg-surface-container border-r border-white/5 flex flex-col py-8 overflow-y-auto z-50 md:hidden">
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-surface">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-white/5 z-40"
          style={{ background: "rgba(24,21,56,.8)", backdropFilter: "blur(16px)" }}>
          <div className="flex items-center gap-3">
            <button onClick={() => setDesktopSidebar((v) => !v)}
              className="hidden md:flex w-8 h-8 items-center justify-center rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/10 transition-colors">
              <span className="material-symbols-outlined" style={{ fontSize: "20px" }}>menu</span>
            </button>
            <button onClick={() => setSidebarOpen(true)} className="md:hidden">
              <span className="material-symbols-outlined text-on-surface">menu</span>
            </button>

            {/* Breadcrumb: Curriculum → Topic */}
            {activeView === "chat" && selectedTopic ? (
              <div className="flex items-center gap-2">
                <button onClick={() => { setActiveView("curriculum"); setSelectedTopic(null); setMessages([]); }}
                  className="flex items-center gap-1 text-on-surface-variant hover:text-on-surface text-xs transition-colors">
                  <span className="material-symbols-outlined" style={{ fontSize: "16px" }}>arrow_back</span>
                  Müfredat
                </button>
                <span className="text-on-surface-variant text-xs">/</span>
                <span className="text-on-surface text-xs font-semibold">{selectedTopic.name}</span>
                <span className="px-2 py-0.5 rounded-full text-xs font-bold"
                  style={{ background: LEVEL_META[selectedTopic.level].bg, color: LEVEL_META[selectedTopic.level].color }}>
                  {LEVEL_META[selectedTopic.level].label}
                </span>
                <button
                  onClick={() => { if (selectedTopic) startChat(selectedTopic.id, selectedTopic.name, selectedTopic.level, true); }}
                  className="flex items-center gap-1 text-xs text-on-surface-variant hover:text-primary transition-colors px-2 py-1 rounded-lg ml-1"
                  style={{ background: "rgba(255,255,255,.05)" }}
                  title="Geçmişi temizle ve yeni sohbet başlat"
                >
                  <span className="material-symbols-outlined" style={{ fontSize: "15px" }}>add_comment</span>
                  Yeni Sohbet
                </button>
              </div>
            ) : (
              <span className="text-sm font-semibold text-on-surface hidden md:block">Müfredat</span>
            )}
          </div>

          <div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center gradient-bg md:hidden">
            {avatarUrl ? <img src={avatarUrl} alt={name ?? ""} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : <span className="text-white text-sm font-bold">{initials}</span>}
          </div>
        </header>

        {/* ── Curriculum Cards View ─────────────────────────── */}
        {activeView === "curriculum" && (
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
                      onClick={() => openPreTest(topicId, topicName)}
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
        )}

        {/* ── Chat View ─────────────────────────────────────── */}
        {activeView === "chat" && (
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
                        ? (correct) => {
                            feedbackMutation.mutate({ topic_id: m.topicId ?? null, correct });
                            toast(correct ? "Harika! Devam et 🎉" : "Sorun değil, tekrar deneyelim 💪");
                          }
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
                {/* Prompt önerileri — konu seçiliyken ve az mesaj varken göster */}
                {selectedTopic && messages.length < 3 && !streaming && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {(TOPIC_PROMPTS[selectedTopic.id] ?? []).map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => { setInput(prompt); setTimeout(() => textareaRef.current?.focus(), 0); }}
                        className="text-xs px-3 py-1.5 rounded-full border transition-all hover:scale-105 active:scale-95"
                        style={{
                          background: "rgba(151,169,255,.07)",
                          borderColor: "rgba(151,169,255,.22)",
                          color: "rgba(151,169,255,.85)",
                          cursor: "pointer",
                        }}
                      >
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
                    onChange={(e) => { setInput(e.target.value); autoResize(); }}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                    placeholder={selectedTopic ? `${selectedTopic.name} hakkında soru sor…` : "Python hakkında bir soru sor…"}
                    rows={1}
                    className="flex-1 bg-transparent border-none focus:ring-0 text-on-surface text-sm resize-none outline-none placeholder:text-on-surface-variant/50"
                    style={{ maxHeight: "120px", overflowY: "auto" }}
                  />
                  <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                    onClick={sendMessage} disabled={streaming || !input.trim()}
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
        )}
      </main>

      {/* ── Pre-Test Modal ────────────────────────────────── */}
      <AnimatePresence>
        {preTest && (
          <>
            <motion.div key="pretest-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/75 z-50" />
            <motion.div key="pretest-modal" initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.92 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div className="glass-card rounded-3xl p-8 w-full max-w-lg border shadow-2xl"
                style={{ borderColor: "rgba(151,169,255,.2)", background: "#13102e" }}>

                {/* Result screen */}
                {preTest.result ? (
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
                      onClick={() => startChat(preTest.topicId, preTest.topicName, preTest.result!.level)}
                      className="w-full py-4 rounded-2xl text-sm font-bold text-white gradient-bg shadow-xl"
                    >
                      Öğrenmeye Başla →
                    </button>
                    <button onClick={() => setPreTest(null)}
                      className="text-xs text-on-surface-variant hover:text-on-surface transition-colors">
                      İptal
                    </button>
                  </div>
                ) : (
                  /* Quiz questions */
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
                            onClick={() => setPreTest((prev) => prev ? { ...prev, answers: { ...prev.answers, [prev.step]: i } } : prev)}
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
                        if (!isLast) {
                          setPreTest((prev) => prev ? { ...prev, step: prev.step + 1 } : prev);
                        } else {
                          await submitPreTest(preTest);
                        }
                      }}
                      className="mt-6 w-full py-3 rounded-xl text-sm font-bold text-white gradient-bg disabled:opacity-40 transition-opacity"
                    >
                      {preTest.step < preTest.questions.length - 1 ? "Sonraki Soru →" : "Seviyemi Belirle"}
                    </button>

                    <button onClick={() => setPreTest(null)}
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

      {/* ── Test Öneri Balonu ─────────────────────────────── */}
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
                onClick={async () => {
                  const { topicId, topicName } = pendingTestSuggest;
                  setPendingTestSuggest(null);
                  const data = await getQuiz(topicId);
                  if (data.questions?.length) {
                    setQuizModal({ topicId, topicName, questions: data.questions, answers: {}, step: 0, done: false });
                  }
                }}
                className="flex-1 py-2 rounded-xl text-xs font-bold text-white gradient-bg">
                Evet, başlayalım!
              </button>
              <button onClick={() => setPendingTestSuggest(null)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-on-surface-variant hover:text-on-surface transition-colors"
                style={{ background: "rgba(255,255,255,.06)" }}>
                Daha sonra
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Ara Değerlendirme Quiz Modal ──────────────────── */}
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
                      <span className="text-xs font-bold text-primary px-3 py-1 rounded-full" style={{ background: "rgba(151,169,255,.1)" }}>
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
                            onClick={() => setQuizModal((prev) => prev ? { ...prev, answers: { ...prev.answers, [prev.step]: i } } : prev)}
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
                          setQuizModal((prev) => prev ? { ...prev, step: prev.step + 1 } : prev);
                        } else {
                          Promise.all(
                            Array.from({ length: quizModal.questions.length }, (_, i) =>
                              sendFeedback(quizModal.topicId, quizModal.answers[i] !== undefined)
                            )
                          ).then(() => {
                            qc.invalidateQueries({ queryKey: ["mastery"] });
                            qc.invalidateQueries({ queryKey: ["nextTopic"] });
                          });
                          setQuizModal((prev) => prev ? { ...prev, done: true } : prev);
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
                    <button onClick={() => setQuizModal(null)}
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
    </div>
  );
}
