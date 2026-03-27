import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// Token'ı her isteğe ekle
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 401 → logout
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
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
  onDone: (topicId: number | null) => void
) => {
  const token = localStorage.getItem("access_token");

  // SSE fetch (axios SSE'yi desteklemiyor)
  fetch("http://localhost:8000/api/chat/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question, chat_history }),
  }).then(async (res) => {
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split("\n").filter((l) => l.startsWith("data: "));

      for (const line of lines) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.token) onToken(data.token);
          if (data.done) onDone(data.topic_id ?? null);
        } catch {}
      }
    }
  });
};

// ── Teacher ───────────────────────────────────────────────────────────────

export const getStudents   = () => api.get("/api/teacher/students").then((r) => r.data);
export const getLogs       = (username?: string, role?: string) =>
  api.get("/api/teacher/logs", { params: { username, role, last_n: 200 } }).then((r) => r.data);
export const getCurriculum = () => api.get("/api/teacher/curriculum").then((r) => r.data);

// ── PDFs ──────────────────────────────────────────────────────────────────

export const uploadPdfs = (files: File[]) => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return api.post("/api/pdfs/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

export const getPdfStatus = () => api.get("/api/pdfs/status").then((r) => r.data);
