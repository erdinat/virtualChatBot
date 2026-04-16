import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useAuthStore } from "../store/authStore";
import {
  getMyMastery, getNextTopic, askQuestion, sendFeedback,
  getQuiz, assessTopicLevel, getChatHistory,
} from "../api/client";

import CurriculumGrid  from "../components/student/CurriculumGrid";
import ChatView        from "../components/student/ChatView";
import PreTestModal    from "../components/student/PreTestModal";
import QuizModal       from "../components/student/QuizModal";
import type { TopicLevel, Message, PreTestState, QuizModalState } from "../components/student/types";
import { LEVEL_META, newId } from "../components/student/types";

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

  // ── Sidebar state ───────────────────────────────────────────────────────
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [desktopSidebar, setDesktopSidebar] = useState(true);
  const [recentHistory, setRecentHistory] = useState<{ role: string; content: string }[]>([]);

  // ── Quiz / test öneri state ─────────────────────────────────────────────
  const [quizModal, setQuizModal] = useState<QuizModalState | null>(null);
  const [pendingTestSuggest, setPendingTestSuggest] = useState<{
    topicId: number; topicName: string;
  } | null>(null);

  // ── Queries ─────────────────────────────────────────────────────────────
  const { data: mastery } = useQuery({
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

  useEffect(() => {
    if (nextTopic?.suggest_test && nextTopic?.topic?.id && !streaming && !quizModal && !pendingTestSuggest) {
      setPendingTestSuggest({ topicId: nextTopic.topic.id, topicName: nextTopic.topic.name });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nextTopic?.suggest_test, nextTopic?.topic?.id, streaming]);

  // ── Chat actions ────────────────────────────────────────────────────────

  function sendMessage() {
    if (!input.trim() || streaming) return;
    const question = input.trim();
    setInput("");

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
      question, history,
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

  // ── Topic entry flow ────────────────────────────────────────────────────

  async function openPreTest(topicId: number, topicName: string) {
    const cached = localStorage.getItem(`topic_level_${username}_${topicId}`) as TopicLevel | null;
    if (cached) { startChat(topicId, topicName, cached); return; }
    try {
      const data = await getQuiz(topicId);
      if (data.questions?.length) {
        setPreTest({ topicId, topicName, questions: data.questions, answers: {}, step: 0, result: null });
      }
    } catch { toast.error("Sorular yüklenemedi."); }
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
          const sessionStartMs = localStorage.getItem(sessionStartKey);
          const allMsgs = data.messages as { role: "user" | "assistant"; content: string; timestamp: string }[];
          const history: Message[] = [];
          let dividerAdded = false;

          for (const m of allMsgs) {
            if (sessionStartMs && !dividerAdded &&
                new Date(m.timestamp).getTime() >= parseInt(sessionStartMs)) {
              history.push({ id: newId(), role: "assistant", content: "— Yeni sohbet başladı —" });
              dividerAdded = true;
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
      } catch { /* geçmiş yok → yeni başlangıç */ }
    }

    if (forceNew) {
      setRecentHistory(messages.filter((m) => m.role === "user").map((m) => ({ role: m.role, content: m.content })));
      localStorage.setItem(sessionStartKey, Date.now().toString());
    } else {
      setRecentHistory([]);
    }

    setMessages([{
      id: newId(), role: "assistant",
      content: `Merhaba! **${topicName}** konusunu öğrenmeye başlıyoruz. ${LEVEL_META[level].label} seviyesin — sana uygun örnekler ve açıklamalarla ilerleceğiz. Ne sormak istersin? 😊`,
    }]);
  }

  // ── Layout helpers ──────────────────────────────────────────────────────

  const masteryMap: Record<string, number> = mastery?.mastery ?? {};
  const avgMastery = Object.values(masteryMap).length
    ? (Object.values(masteryMap) as number[]).reduce((a, b) => a + b, 0) / Object.values(masteryMap).length
    : 0;

  const AVATAR: Record<string, string> = {
    ali:      "https://cdn-icons-png.flaticon.com/512/4202/4202839.png",
    ayse:     "https://cdn-icons-png.flaticon.com/512/4202/4202850.png",
    ogretmen: "https://cdn-icons-png.flaticon.com/512/4202/4202843.png",
  };
  const avatarUrl = username ? AVATAR[username] : undefined;
  const initials = (name ?? username ?? "?")[0].toUpperCase();

  // ── Sidebar content ─────────────────────────────────────────────────────
  const sidebarContent = (
    <>
      <div className="px-6 mb-8 flex items-center gap-3">
        <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>school</span>
        <h1 className="text-xl font-bold gradient-text tracking-tight">Sanal Öğretmen</h1>
      </div>

      <div className="flex items-center gap-4 mb-10 mx-6 p-4 rounded-xl bg-surface-container-low border border-white/5">
        <div className="w-12 h-12 rounded-full overflow-hidden gradient-bg flex items-center justify-center font-bold text-white text-lg shrink-0">
          {avatarUrl
            ? <img src={avatarUrl} alt={name ?? ""} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            : initials}
        </div>
        <div>
          <p className="text-on-surface font-semibold text-sm">{name}</p>
          <p className="text-on-surface-variant text-xs">Python Öğrencisi</p>
        </div>
      </div>

      {activeView === "chat" && recentHistory.length > 0 && (
        <div className="px-6 mb-6">
          <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-3 px-1">Konu Geçmişi</h3>
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
        <div className="p-4 rounded-xl border" style={{ background: "rgba(92,49,135,.2)", borderColor: "rgba(92,49,135,.3)" }}>
          <p className="text-xs uppercase font-bold text-secondary mb-2">
            {nextTopic?.topic?.name ? "Yapay Zeka Önerisi" : "Genel İlerleme"}
          </p>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary" style={{ fontSize: "20px" }}>auto_awesome</span>
            <span className="text-sm font-medium text-on-secondary-container leading-tight">
              {nextTopic?.topic?.name
                ? `Önerilen: '${nextTopic.topic.name}'`
                : `Ort. %${Math.round(avgMastery * 100)} hakimiyet`}
            </span>
          </div>
        </div>
      </div>

      <button
        onClick={() => { logout(); window.location.href = "/"; }}
        className="mt-6 mx-6 flex items-center gap-3 text-on-surface-variant hover:text-error transition-colors px-4 py-3 group">
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
                  onClick={() => startChat(selectedTopic.id, selectedTopic.name, selectedTopic.level, true)}
                  className="flex items-center gap-1 text-xs text-on-surface-variant hover:text-primary transition-colors px-2 py-1 rounded-lg ml-1"
                  style={{ background: "rgba(255,255,255,.05)" }}
                  title="Geçmişi temizle ve yeni sohbet başlat">
                  <span className="material-symbols-outlined" style={{ fontSize: "15px" }}>add_comment</span>
                  Yeni Sohbet
                </button>
              </div>
            ) : (
              <span className="text-sm font-semibold text-on-surface hidden md:block">Müfredat</span>
            )}
          </div>

          <div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center gradient-bg md:hidden">
            {avatarUrl
              ? <img src={avatarUrl} alt={name ?? ""} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              : <span className="text-white text-sm font-bold">{initials}</span>}
          </div>
        </header>

        {/* Views */}
        {activeView === "curriculum" && (
          <CurriculumGrid masteryMap={masteryMap} onTopicClick={openPreTest} />
        )}

        {activeView === "chat" && (
          <ChatView
            messages={messages}
            input={input}
            streaming={streaming}
            selectedTopic={selectedTopic}
            onInputChange={setInput}
            onSend={sendMessage}
            onFeedback={(topicId, correct) => {
              feedbackMutation.mutate({ topic_id: topicId ?? null, correct });
              toast(correct ? "Harika! Devam et 🎉" : "Sorun değil, tekrar deneyelim 💪");
            }}
            onPromptClick={setInput}
          />
        )}
      </main>

      {/* Modals */}
      <PreTestModal
        preTest={preTest}
        onClose={() => setPreTest(null)}
        onAnswer={(step, opt) => setPreTest((p) => p ? { ...p, answers: { ...p.answers, [step]: opt } } : p)}
        onNext={() => setPreTest((p) => p ? { ...p, step: p.step + 1 } : p)}
        onSubmit={submitPreTest}
        onStartChat={startChat}
      />

      <QuizModal
        quizModal={quizModal}
        pendingTestSuggest={pendingTestSuggest}
        activeView={activeView}
        onQuizAnswer={(step, opt) => setQuizModal((p) => p ? { ...p, answers: { ...p.answers, [step]: opt } } : p)}
        onQuizNext={() => setQuizModal((p) => p ? { ...p, step: p.step + 1 } : p)}
        onQuizClose={() => setQuizModal(null)}
        onQuizDone={() => setQuizModal((p) => p ? { ...p, done: true } : p)}
        onPendingAccept={async (topicId, topicName) => {
          setPendingTestSuggest(null);
          const data = await getQuiz(topicId);
          if (data.questions?.length) {
            setQuizModal({ topicId, topicName, questions: data.questions, answers: {}, step: 0, done: false });
          }
        }}
        onPendingDismiss={() => setPendingTestSuggest(null)}
      />

    </div>
  );
}
