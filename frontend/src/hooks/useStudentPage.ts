/**
 * useStudentPage — StudentPage'e ait tüm state ve action logic.
 *
 * Bölünme gerekçesi: StudentPage.tsx God Component (~1000 satır) daha
 * okunabilir hale getirmek için state/logic bu hook'ta, JSX StudentPage'de.
 */

import { useEffect, useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useAuthStore } from "../store/authStore";
import {
  getMyMastery, getNextTopic, askQuestion, sendFeedback,
  getQuiz, generateQuiz, assessTopicLevel, getChatHistory,
} from "../api/client";
import type { TopicLevel, Message, PreTestState, QuizModalState } from "../components/student/types";
import { LEVEL_META, TOPICS, TOPIC_PREREQUISITES, newId } from "../components/student/types";

export function useStudentPage() {
  const { name, username, logout } = useAuthStore();
  const qc = useQueryClient();

  // ── View state ─────────────────────────────────────────────────────────
  const [activeView, setActiveView] = useState<"curriculum" | "chat">("curriculum");
  const [selectedTopic, setSelectedTopic] = useState<{
    id: number; name: string; level: TopicLevel;
  } | null>(null);

  // ── Pre-test state ─────────────────────────────────────────────────────
  const [preTest, setPreTest] = useState<PreTestState | null>(null);

  // ── Chat state ─────────────────────────────────────────────────────────
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const sseAbortRef = useRef<AbortController | null>(null);

  // ── Sidebar state ──────────────────────────────────────────────────────
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [desktopSidebar, setDesktopSidebar] = useState(true);
  const [recentHistory, setRecentHistory] = useState<{ role: string; content: string }[]>([]);

  // ── Quiz / test öneri state ────────────────────────────────────────────
  const [quizModal, setQuizModal] = useState<QuizModalState | null>(null);
  const [pendingTestSuggest, setPendingTestSuggest] = useState<{
    topicId: number; topicName: string;
  } | null>(null);

  // ── Mastered topics ────────────────────────────────────────────────────
  const [masteredTopics, setMasteredTopics] = useState<Set<number>>(() => {
    const set = new Set<number>();
    for (let i = 1; i <= 10; i++) {
      if (localStorage.getItem(`topic_mastered_${username}_${i}`) === "1") set.add(i);
    }
    return set;
  });

  // ── Studied topics — öğrencinin gerçekten sohbet açtığı konular ────────
  const [studiedTopics, setStudiedTopics] = useState<Set<number>>(() => {
    const set = new Set<number>();
    for (let i = 1; i <= 10; i++) {
      if (localStorage.getItem(`topic_studied_${username}_${i}`) === "1") set.add(i);
    }
    return set;
  });

  // ── Level mastery progress (0–100, per topic per level) ────────────────
  const [levelProgress, setLevelProgress] = useState(0);

  useEffect(() => {
    if (!selectedTopic || !username) { setLevelProgress(0); return; }
    const key = `level_progress_${username}_${selectedTopic.id}_${selectedTopic.level}`;
    setLevelProgress(parseInt(localStorage.getItem(key) ?? "0"));
  }, [selectedTopic?.id, selectedTopic?.level, username]);

  function writeLevelProgress(topicId: number, level: string, value: number): number {
    const clamped = Math.min(Math.max(value, 0), 100);
    localStorage.setItem(`level_progress_${username}_${topicId}_${level}`, String(clamped));
    setLevelProgress(clamped);
    return clamped;
  }

  // ── Queries ────────────────────────────────────────────────────────────
  const { data: mastery } = useQuery({
    queryKey: ["mastery"],
    queryFn: getMyMastery,
    refetchInterval: 15000,
  });
  const { data: nextTopic } = useQuery({ queryKey: ["nextTopic"], queryFn: getNextTopic });

  const dktFeedback = useMutation({
    mutationFn: ({ topic_id, correct }: { topic_id: number | null; correct: boolean }) =>
      sendFeedback(topic_id, correct),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mastery"] }),
  });

  // ── Effects ────────────────────────────────────────────────────────────
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  useEffect(() => {
    const sameTopicSuggested = nextTopic?.topic?.id === selectedTopic?.id;
    if (nextTopic?.suggest_test && sameTopicSuggested && !streaming && !quizModal && !pendingTestSuggest) {
      setPendingTestSuggest({ topicId: nextTopic.topic.id, topicName: nextTopic.topic.name });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nextTopic?.suggest_test, nextTopic?.topic?.id, selectedTopic?.id, streaming]);

  // ── Computed values ────────────────────────────────────────────────────
  const rawMastery: Record<string, number> = mastery?.mastery ?? {};
  const masteryMap: Record<string, number> = Object.fromEntries(
    Object.entries(rawMastery).map(([name, score], idx) => [
      name,
      studiedTopics.has(idx + 1) ? score : 0,
    ])
  );
  const avgMastery = Object.values(masteryMap).length
    ? (Object.values(masteryMap) as number[]).reduce((a, b) => a + b, 0) / Object.values(masteryMap).length
    : 0;

  const lockedTopics = new Set<number>();
  for (const [topicIdStr, prereqId] of Object.entries(TOPIC_PREREQUISITES)) {
    const topicId = Number(topicIdStr);
    if (masteredTopics.has(prereqId)) continue;
    const prereqKey = `level_progress_${username}_${prereqId}_intermediate`;
    const prereqIntermediatePct = parseInt(localStorage.getItem(prereqKey) ?? "0");
    if (prereqIntermediatePct < 50) lockedTopics.add(topicId);
  }

  // ── Chat actions ───────────────────────────────────────────────────────

  function sendMessage(overrideQuestion?: string) {
    const question = overrideQuestion ?? input.trim();
    if (!question || streaming) return;
    if (!overrideQuestion) setInput("");

    sseAbortRef.current?.abort();
    const abortController = new AbortController();
    sseAbortRef.current = abortController;

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
        if (abortController.signal.aborted) return;
        buffer += token;
        setMessages((prev) => {
          const updated = [...prev];
          const idx = updated.findIndex((m) => m.id === assistantId);
          if (idx !== -1) updated[idx] = { ...updated[idx], content: buffer };
          return updated;
        });
      },
      (tid) => {
        if (abortController.signal.aborted) return;
        setStreaming(false);
        setMessages((prev) => {
          const updated = [...prev];
          const idx = updated.findIndex((m) => m.id === assistantId);
          if (idx !== -1) updated[idx] = { ...updated[idx], topicId: tid };
          return updated;
        });
        const topicId = tid ?? selectedTopic?.id ?? null;
        if (topicId !== null) dktFeedback.mutate({ topic_id: topicId, correct: true });
        qc.invalidateQueries({ queryKey: ["nextTopic"] });
      },
      () => {
        if (abortController.signal.aborted) return;
        setStreaming(false);
        toast.error("Bağlantı hatası, tekrar dene.");
        setMessages((prev) => prev.filter((m) => m.id !== assistantId));
      },
      selectedTopic?.id ?? null,
      selectedTopic?.level ?? null,
    );
  }

  // ── Topic entry flow ───────────────────────────────────────────────────

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
    sseAbortRef.current?.abort();
    sseAbortRef.current = null;
    setStreaming(false);

    localStorage.setItem(`topic_level_${username}_${topicId}`, level);
    setSelectedTopic({ id: topicId, name: topicName, level });
    setActiveView("chat");
    setPreTest(null);

    localStorage.setItem(`topic_studied_${username}_${topicId}`, "1");
    setStudiedTopics((prev) => new Set([...prev, topicId]));

    const progressKey = `level_progress_${username}_${topicId}_${level}`;
    if (!localStorage.getItem(progressKey)) {
      const dktPct = Math.round((masteryMap[topicName] ?? 0) * 100);
      localStorage.setItem(progressKey, String(dktPct));
      setLevelProgress(dktPct);
    }

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

  // ── Quiz close handler ─────────────────────────────────────────────────

  function handleQuizClose(
    quizState: QuizModalState | null,
    currentLevelProgress: number,
  ) {
    const mode  = quizState?.mode;
    const score = quizState?.score ?? 0;
    const total = quizState?.total ?? 3;
    const passed = total > 0 && score / total >= 2 / 3;
    setQuizModal(null);

    if (mode === "concept-check") {
      if (selectedTopic) dktFeedback.mutate({ topic_id: selectedTopic.id, correct: passed });

      if (!passed) {
        if (selectedTopic) writeLevelProgress(selectedTopic.id, selectedTopic.level, currentLevelProgress - 5);
        sendMessage("anlamadım, daha basit anlat");
      } else {
        const newProg = selectedTopic
          ? writeLevelProgress(selectedTopic.id, selectedTopic.level, currentLevelProgress + 10)
          : 0;
        if (newProg >= 100 && selectedTopic) {
          writeLevelProgress(selectedTopic.id, selectedTopic.level, 0);
          toast.success("Harika! Seviye testine hazırsın 🎯");
          getQuiz(selectedTopic.id).then((data) => {
            if (data.questions?.length) {
              setQuizModal({
                topicId: selectedTopic.id, topicName: selectedTopic.name,
                questions: data.questions, answers: {}, step: 0, done: false, mode: "check",
              });
            }
          }).catch(() => toast.error("Test yüklenemedi."));
        } else {
          toast.success(`Doğru! Seviye hakimiyetin: %${newProg}`);
        }
      }
    } else if (mode === "check") {
      if (!passed) {
        if (selectedTopic) writeLevelProgress(selectedTopic.id, selectedTopic.level, Math.max(currentLevelProgress - 10, 0));
        sendMessage("anlamadım, daha basit anlat");
      } else {
        const levelOrder: TopicLevel[] = ["beginner", "intermediate", "advanced"];
        const currentLevelIdx = levelOrder.indexOf(selectedTopic?.level ?? "beginner");
        const nextLevel: TopicLevel | null = levelOrder[currentLevelIdx + 1] ?? null;

        if (nextLevel && selectedTopic) {
          writeLevelProgress(selectedTopic.id, nextLevel, 0);
          startChat(selectedTopic.id, selectedTopic.name, nextLevel, true);
        } else if (selectedTopic) {
          getQuiz(selectedTopic.id).then((data) => {
            if (data.questions?.length) {
              setQuizModal({
                topicId: selectedTopic.id, topicName: selectedTopic.name,
                questions: data.questions, answers: {}, step: 0, done: false, mode: "final",
              });
            }
          }).catch(() => toast.error("Final testi yüklenemedi."));
        }
      }
    } else if (mode === "final") {
      if (passed) {
        if (selectedTopic) {
          localStorage.setItem(`topic_mastered_${username}_${selectedTopic.id}`, "1");
          setMasteredTopics((prev) => new Set([...prev, selectedTopic.id]));
        }
        const nextTopicId = selectedTopic ? selectedTopic.id + 1 : null;
        if (nextTopicId && nextTopicId <= 10) {
          const nextTopicLevel: TopicLevel = score === total ? "intermediate" : "beginner";
          localStorage.setItem(`topic_level_${username}_${nextTopicId}`, nextTopicLevel);
          openPreTest(nextTopicId, TOPICS[nextTopicId - 1]);
        } else {
          toast.success("Tüm konuları tamamladın! 🎉");
        }
      } else {
        sendMessage("Bu konuyu daha iyi pekiştirmem lazım, tekrar anlat");
      }
    }
    // mode === "review" → sadece kapat
  }

  // ── Feedback handler ───────────────────────────────────────────────────

  async function handleFeedback(correct: boolean) {
    if (!selectedTopic) return;
    if (!correct) {
      sendMessage("anlamadım, daha basit anlat");
      return;
    }
    try {
      const chatHistory = messages
        .filter((m) => !m.content.startsWith("—"))
        .slice(-20)
        .map((m) => ({ role: m.role, content: m.content }));
      const data = await generateQuiz(selectedTopic.id, selectedTopic.level, chatHistory);
      if (data.questions?.length) {
        setQuizModal({
          topicId: selectedTopic.id, topicName: selectedTopic.name,
          questions: data.questions, correctAnswers: data.correct,
          answers: {}, step: 0, done: false, mode: "concept-check",
        });
      }
    } catch {
      toast.error("Test yüklenemedi.");
    }
  }

  return {
    // Auth
    name, username, logout,
    // View
    activeView, setActiveView,
    selectedTopic, setSelectedTopic,
    // Pre-test
    preTest, setPreTest, submitPreTest, openPreTest,
    // Chat
    messages, input, setInput, streaming, bottomRef,
    sendMessage, startChat,
    // Sidebar
    sidebarOpen, setSidebarOpen,
    desktopSidebar, setDesktopSidebar,
    recentHistory,
    // Quiz
    quizModal, setQuizModal, pendingTestSuggest, setPendingTestSuggest,
    handleQuizClose, handleFeedback,
    // Progress
    levelProgress, writeLevelProgress,
    // Computed
    masteryMap, avgMastery, lockedTopics, masteredTopics, studiedTopics,
    // Queries
    nextTopic,
  };
}
