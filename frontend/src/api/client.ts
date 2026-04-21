import axios from "axios";
import { useAuthStore } from "../store/authStore";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Token'ı her isteğe ekle
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 401 → logout (hem localStorage hem Zustand temizlenmeli, yoksa sonsuz yönlendirme döngüsü olur)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/";
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────

export const login = async (username: string, password: string) => {
  const form = new URLSearchParams({ username, password });
  const res = await api.post("/api/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data;
};

// ── Mastery ───────────────────────────────────────────────────────────────

export const getMyMastery = () => api.get("/api/mastery/me").then((r) => r.data);

export const sendFeedback = (topic_id: number | null, correct: boolean) =>
  api.post("/api/mastery/feedback", { topic_id, correct }).then((r) => r.data);

// ── Chat ─────────────────────────────────────────────────────────────────

export const getNextTopic = () => api.get("/api/chat/next-topic").then((r) => r.data);

export const askQuestion = (
  question: string,
  chat_history: { role: string; content: string }[],
  onToken: (token: string) => void,
  onDone: (topicId: number | null) => void,
  onError: () => void,
  topic_id?: number | null,
  topic_level?: string | null,
) => {
  const token = localStorage.getItem("access_token");

  // SSE fetch (axios SSE'yi desteklemiyor)
  fetch(`${API_BASE}/api/chat/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question, chat_history, topic_id, topic_level }),
  }).then(async (res) => {
    if (!res.ok) { onError(); return; }
    if (!res.body) { onError(); return; }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split("\n").filter((l) => l.startsWith("data: "));

      for (const line of lines) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.error) { onError(); return; }
          if (data.token) onToken(data.token);
          if (data.done) onDone(data.topic_id ?? null);
        } catch (e) {
          console.warn("SSE parse error:", e);
        }
      }
    }
  }).catch(() => onError());
};

// ── Teacher ───────────────────────────────────────────────────────────────

export const getStudents   = () => api.get("/api/teacher/students").then((r) => r.data);
export const getLogs       = (username?: string, role?: string) =>
  api.get("/api/teacher/logs", { params: { username, role, last_n: 200 } }).then((r) => r.data);
export const getCurriculum = () => api.get("/api/teacher/curriculum").then((r) => r.data);

// ── Quiz & Diagnostic ─────────────────────────────────────────────────────

export const getQuiz = (topic_id: number) =>
  api.get(`/api/chat/quiz/${topic_id}`).then((r) => r.data);

/** LLM ile seviye + sohbet bağlamına özel 3 soru üretir. Döner: {questions, correct: number[]} */
export const generateQuiz = (
  topic_id: number,
  level: string,
  chat_history: { role: string; content: string }[],
) => api.post("/api/chat/generate-quiz", { topic_id, level, chat_history }).then((r) => r.data);

export const getDiagnosticQuestions = () =>
  api.get("/api/diagnostic/questions").then((r) => r.data);

export const submitDiagnostic = (answers: Record<string, string>) =>
  api.post("/api/diagnostic/submit", { answers }).then((r) => r.data);

export const assessTopicLevel = (topic_id: number, answers: Record<string, number>) =>
  api.post("/api/diagnostic/topic-level", { topic_id, answers }).then((r) => r.data);

// ── PDFs ──────────────────────────────────────────────────────────────────

export const uploadPdfs = (files: File[], topicIds: number[] = []) => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  form.append("topic_ids", topicIds.join(","));
  return api.post("/api/pdfs/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

export const getPdfStatus = () => api.get("/api/pdfs/status").then((r) => r.data);

export const getChatHistory = (topic_id: number) =>
  api.get(`/api/chat/history/${topic_id}`).then((r) => r.data);
