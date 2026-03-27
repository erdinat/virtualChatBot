import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useAuthStore } from "../store/authStore";
import { getStudents, getLogs, getCurriculum, uploadPdfs, getPdfStatus } from "../api/client";

type Tab = "analytics" | "logs" | "curriculum";

/* ── Student Analytics Tab ───────────────────────────────── */
function AnalyticsTab() {
  const { data: students = [] } = useQuery({ queryKey: ["students"], queryFn: getStudents });
  const { data: curriculum = [] } = useQuery({ queryKey: ["curriculum"], queryFn: getCurriculum });
  const [search, setSearch] = useState("");

  const filtered = (students as any[]).filter((s) =>
    s.username.toLowerCase().includes(search.toLowerCase())
  );

  // Top 4 curriculum topics by avg mastery
  const topicStats = (curriculum as any[]).slice(0, 4).map((c: any) => {
    const vals = (students as any[]).map((s: any) => s.mastery?.[c.name] ?? 0);
    const avg = vals.length ? vals.reduce((a: number, b: number) => a + b, 0) / vals.length : 0;
    return { name: c.name, avg };
  });

  return (
    <div className="space-y-8">
      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {topicStats.map((t, i) => {
          const icons = ["terminal", "account_tree", "function", "data_object"];
          const pct = Math.round(t.avg * 100);
          const color = pct >= 80 ? "#4ade80" : pct >= 60 ? "#fbbf24" : "#ff6e84";
          return (
            <div key={t.name} className="glass-card p-6 rounded-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-3 text-5xl opacity-10 group-hover:opacity-20 transition-opacity pointer-events-none">
                <span className="material-symbols-outlined" style={{ fontSize: "48px" }}>{icons[i]}</span>
              </div>
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-1">{t.name}</p>
              <h3 className="text-3xl font-black text-white">
                %{pct}{" "}
                <span className="text-sm font-medium" style={{ color }}>
                  {pct >= 70 ? "↑" : "↓"}
                </span>
              </h3>
              <p className="text-xs text-on-surface-variant mt-2 italic">Ortalama Başarı Oranı</p>
            </div>
          );
        })}
      </div>

      {/* Student table */}
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="p-6 border-b border-white/5 flex justify-between items-center">
          <h4 className="text-xl font-bold text-on-surface">Öğrenci Gelişim Tablosu</h4>
          <div className="bg-surface-container rounded-full px-4 py-1.5 flex items-center gap-2 border border-white/5">
            <span className="material-symbols-outlined text-primary" style={{ fontSize: "16px" }}>search</span>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-transparent border-none text-xs focus:ring-0 text-white w-32 md:w-48 outline-none"
              placeholder="Öğrenci Ara…"
            />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-xs uppercase tracking-widest font-black text-on-surface-variant" style={{ background: "rgba(255,255,255,.05)" }}>
                <th className="px-8 py-4">Öğrenci</th>
                <th className="px-8 py-4">Etkileşim</th>
                <th className="px-8 py-4">Genel İlerleme</th>
                <th className="px-8 py-4">Başarı Skoru</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s: any) => {
                const pct = Math.round(s.avg_mastery * 100);
                const score = (s.success_rate * 10).toFixed(1);
                const scoreColor =
                  s.success_rate >= 0.8 ? "#4ade80" :
                  s.success_rate >= 0.6 ? "#fbbf24" : "#ff6e84";
                const scoreBg =
                  s.success_rate >= 0.8 ? "rgba(74,222,128,.1)" :
                  s.success_rate >= 0.6 ? "rgba(251,191,36,.1)" : "rgba(255,110,132,.1)";
                const scoreBorder =
                  s.success_rate >= 0.8 ? "rgba(74,222,128,.2)" :
                  s.success_rate >= 0.6 ? "rgba(251,191,36,.2)" : "rgba(255,110,132,.2)";

                return (
                  <tr key={s.username} className="border-t border-white/5 hover:bg-white/[.03] transition-colors group">
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full p-[2px] shrink-0"
                          style={{ background: "linear-gradient(135deg,#97a9ff,#f8acff)" }}>
                          <div className="w-full h-full rounded-full bg-surface flex items-center justify-center font-bold text-sm text-primary">
                            {s.username[0].toUpperCase()}
                          </div>
                        </div>
                        <div>
                          <p className="font-bold text-white capitalize">{s.username}</p>
                          <p className="text-xs text-on-surface-variant">{s.username}@example.com</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-5">
                      <p className="text-sm text-on-surface-variant">{s.interaction_count} soru</p>
                    </td>
                    <td className="px-8 py-5">
                      <div className="w-48 h-1.5 bg-surface-container-highest rounded-full overflow-hidden relative">
                        <div className="absolute top-0 left-0 h-full shimmer-bar" style={{ width: `${pct}%` }} />
                      </div>
                      <p className="text-xs mt-2 font-bold text-primary">%{pct} Tamamlandı</p>
                    </td>
                    <td className="px-8 py-5">
                      <span className="text-xs font-black px-3 py-1 rounded-full border"
                        style={{ color: scoreColor, background: scoreBg, borderColor: scoreBorder }}>
                        {score}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {!filtered.length && (
                <tr>
                  <td colSpan={4} className="px-8 py-12 text-center text-on-surface-variant text-sm">
                    Henüz öğrenci verisi yok
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ── Logs Tab ────────────────────────────────────────────── */
function LogsTab() {
  const [usernameFilter, setUsernameFilter] = useState("");
  const { data: logs = [] } = useQuery({
    queryKey: ["logs", usernameFilter],
    queryFn: () => getLogs(usernameFilter || undefined),
  });

  return (
    <div className="space-y-4 flex flex-col" style={{ height: "calc(100vh - 280px)" }}>
      <div className="flex gap-3 shrink-0">
        <div className="bg-surface-container rounded-full px-4 py-2 flex items-center gap-2 border border-white/5">
          <span className="material-symbols-outlined text-primary" style={{ fontSize: "16px" }}>search</span>
          <input
            value={usernameFilter}
            onChange={(e) => setUsernameFilter(e.target.value)}
            placeholder="Kullanıcıya göre filtrele…"
            className="bg-transparent border-none text-xs focus:ring-0 text-white w-40 outline-none"
          />
        </div>
        {usernameFilter && (
          <button onClick={() => setUsernameFilter("")}
            className="px-3 py-2 rounded-full text-xs text-on-surface-variant hover:text-on-surface transition-colors border border-white/5"
            style={{ background: "rgba(255,255,255,.05)" }}>
            Temizle
          </button>
        )}
        <div className="ml-auto flex items-center gap-2 px-4 py-2 rounded-full border border-white/5"
          style={{ background: "rgba(255,255,255,.04)" }}>
          <span className="text-xs text-on-surface-variant">{(logs as any[]).length} kayıt</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto glass-card rounded-xl">
        <div className="p-6 space-y-4">
          {(logs as any[]).map((log: any, i: number) => {
            const isUser = log.role === "user";
            return (
              <div key={i} className="flex gap-4 items-start p-4 rounded-xl border-l-2 transition-colors hover:bg-white/[.02]"
                style={{ background: "rgba(255,255,255,.04)", borderLeftColor: isUser ? "#97a9ff" : "#f8acff" }}>
                <span className="material-symbols-outlined mt-0.5 shrink-0"
                  style={{ fontSize: "20px", color: isUser ? "#97a9ff" : "#f8acff" }}>
                  {isUser ? "chat" : "smart_toy"}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-sm text-on-surface">{log.username}</span>
                    <span className="text-xs text-on-surface-variant">
                      {new Date(log.timestamp).toLocaleString("tr-TR")}
                    </span>
                  </div>
                  <p className="text-xs text-on-surface-variant italic truncate">{log.content}</p>
                </div>
              </div>
            );
          })}
          {!(logs as any[]).length && (
            <div className="text-center py-12 text-on-surface-variant text-sm">
              Log kaydı bulunamadı
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Curriculum Tab ──────────────────────────────────────── */
function CurriculumTab() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const { data: pdfStatus, refetch } = useQuery({ queryKey: ["pdfStatus"], queryFn: getPdfStatus });
  const { data: curriculum = [] } = useQuery({ queryKey: ["curriculum"], queryFn: getCurriculum });

  const uploadMutation = useMutation({
    mutationFn: () => uploadPdfs(files),
    onSuccess: (data: any) => {
      toast.success(`${data.files_processed} PDF işlendi, ${data.chunks_created} parça oluşturuldu!`);
      setFiles([]);
      refetch();
    },
    onError: () => toast.error("PDF yükleme başarısız"),
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Curriculum list */}
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="p-5 border-b border-white/5">
          <h4 className="font-bold text-on-surface">Müfredat Konuları</h4>
        </div>
        <div className="p-4 space-y-3">
          {(curriculum as any[]).map((c: any, i: number) => (
            <div key={c.name} className="flex items-center justify-between p-3 rounded-xl hover:bg-white/[.03] transition-colors"
              style={{ background: "rgba(255,255,255,.04)" }}>
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-primary">{i + 1}.</span>
                <span className="text-sm font-medium text-on-surface">{c.name}</span>
              </div>
              <div className="flex text-amber-400">
                {Array.from({ length: 5 }).map((_, j) => (
                  <span key={j} className="material-symbols-outlined"
                    style={{ fontSize: "14px", fontVariationSettings: j < (c.difficulty ?? 3) ? "'FILL' 1" : "'FILL' 0" }}>
                    star
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* PDF Upload */}
      <div className="space-y-4">
        {/* RAG status */}
        <div className="p-4 rounded-xl flex items-center gap-3 glass-card">
          <div className="w-3 h-3 rounded-full shrink-0" style={{ background: pdfStatus?.loaded ? "#4ade80" : "#ff6e84" }} />
          <div>
            <div className="text-sm font-medium text-on-surface">
              RAG: {pdfStatus?.loaded ? "Aktif ✓" : "Yüklü Değil"}
            </div>
            <div className="text-xs text-on-surface-variant">
              {pdfStatus?.loaded ? "Vektör veritabanı hazır" : "PDF yükleyerek etkinleştirin"}
            </div>
          </div>
        </div>

        {/* Drop zone */}
        <div
          onClick={() => fileRef.current?.click()}
          className="p-8 rounded-xl text-center cursor-pointer transition-all hover:border-primary/50"
          style={{ border: "2px dashed rgba(151,169,255,.3)", background: "rgba(255,255,255,.03)" }}
        >
          <span className="material-symbols-outlined text-primary mb-3 block" style={{ fontSize: "40px" }}>upload_file</span>
          <p className="text-sm font-semibold text-on-surface">Müfredat PDF Yükle</p>
          <p className="text-xs text-on-surface-variant mt-1">Sanal asistanı eğitmek için döküman ekleyin</p>
          <input ref={fileRef} type="file" accept=".pdf" multiple onChange={(e) => setFiles(Array.from(e.target.files ?? []).filter((f) => f.name.endsWith(".pdf")))} className="hidden" />
        </div>

        {files.length > 0 && (
          <div className="space-y-2">
            {files.map((f) => (
              <div key={f.name} className="flex items-center gap-3 p-3 rounded-xl glass-card">
                <span className="material-symbols-outlined text-primary" style={{ fontSize: "20px" }}>description</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-on-surface truncate">{f.name}</div>
                  <div className="text-xs text-on-surface-variant">{(f.size / 1024).toFixed(0)} KB</div>
                </div>
              </div>
            ))}
            <motion.button
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              onClick={() => uploadMutation.mutate()}
              disabled={uploadMutation.isPending}
              className="w-full py-3 rounded-xl text-sm font-bold text-white gradient-bg shadow-lg disabled:opacity-60"
            >
              {uploadMutation.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  İşleniyor…
                </span>
              ) : `${files.length} PDF Yükle ve İşle`}
            </motion.button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Main Teacher Page ───────────────────────────────────── */
export default function TeacherPage() {
  const { name, username, logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState<Tab>("analytics");
  const [sidebarSection, setSidebarSection] = useState<"overview" | "students" | "reports" | "settings">("overview");

  const initials = (name ?? username ?? "?")[0].toUpperCase();

  const TAB_INFO: Record<Tab, { label: string; icon: string }> = {
    analytics:  { label: "Öğrenci Analitiği", icon: "📊" },
    logs:       { label: "Sistem Logları",     icon: "🗂️" },
    curriculum: { label: "Müfredat",           icon: "📚" },
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface text-on-surface font-body">
      {/* ── Sidebar ── */}
      <aside className="w-72 h-full flex flex-col py-8 z-50 border-r border-white/5"
        style={{ background: "#181538" }}>
        {/* Logo */}
        <div className="px-8 mb-12">
          <h1 className="text-2xl font-black gradient-text tracking-tighter">Sanal Öğretmen</h1>
          <p className="text-slate-400 text-xs mt-1 uppercase tracking-widest font-bold">Eğitmen Paneli</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1">
          {([
            { id: "overview",  icon: "dashboard",  label: "Genel Bakış" },
            { id: "students",  icon: "groups",      label: "Öğrenciler" },
            { id: "reports",   icon: "analytics",   label: "Raporlar" },
            { id: "settings",  icon: "settings",    label: "Ayarlar" },
          ] as const).map((item) => (
            <button
              key={item.id}
              onClick={() => setSidebarSection(item.id)}
              className={`w-full text-left py-3 px-8 flex items-center gap-3 transition-all text-sm font-medium ${
                sidebarSection === item.id
                  ? "text-primary border-l-4 border-primary"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
              style={sidebarSection === item.id
                ? { background: "linear-gradient(to right,rgba(102,126,234,.2),transparent)" }
                : {}}
            >
              <span className="material-symbols-outlined" style={{ fontSize: "20px", fontVariationSettings: sidebarSection === item.id ? "'FILL' 1" : "'FILL' 0" }}>
                {item.icon}
              </span>
              {item.label}
            </button>
          ))}
        </nav>

        {/* PDF upload card */}
        <div className="px-6 mt-auto">
          <button
            onClick={() => setActiveTab("curriculum")}
            className="w-full glass-card p-5 rounded-xl border border-dashed border-primary/30 flex flex-col items-center text-center group hover:border-primary/60 transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-primary text-3xl mb-2">upload_file</span>
            <p className="text-xs font-semibold text-on-surface mb-1">Müfredat PDF Yükle</p>
            <p className="text-xs text-on-surface-variant">Yeni döküman ekle</p>
          </button>

          <button
            onClick={() => { logout(); window.location.href = "/"; }}
            className="mt-6 flex items-center gap-3 text-error w-full px-4 py-2 hover:bg-error/10 rounded-xl transition-colors"
          >
            <span className="material-symbols-outlined" style={{ fontSize: "20px" }}>logout</span>
            <span className="font-bold text-sm">Çıkış Yap</span>
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 h-full overflow-y-auto relative" style={{ background: "#0d0a27" }}>
        {/* Decorative glows */}
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full pointer-events-none"
          style={{ background: "rgba(151,169,255,.05)", filter: "blur(120px)", zIndex: 0 }} />
        <div className="absolute bottom-0 left-0 w-72 h-72 rounded-full pointer-events-none"
          style={{ background: "rgba(248,172,255,.05)", filter: "blur(100px)", zIndex: 0 }} />

        <div className="relative z-10 p-8 lg:p-12">
          {/* Welcome header */}
          <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div>
              <h2 className="text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-2">
                Hoş Geldiniz, <span className="gradient-text">Eğitmen</span>
              </h2>
              <p className="text-on-surface-variant text-lg max-w-xl">
                Python rehberiniz ve öğrenci gelişim takip merkeziniz.
              </p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <div className="w-10 h-10 rounded-full gradient-bg flex items-center justify-center font-bold text-white">
                {initials}
              </div>
              <div>
                <div className="text-sm font-semibold text-on-surface">{name}</div>
                <div className="text-xs text-on-surface-variant">Öğretmen</div>
              </div>
            </div>
          </header>

          {/* Tab navigation */}
          <div className="flex gap-8 mb-10 border-b border-white/5">
            {(["analytics", "logs", "curriculum"] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-4 font-medium transition-all flex items-center gap-2 text-sm border-b-2 ${
                  activeTab === tab
                    ? "text-primary border-primary font-bold"
                    : "text-on-surface-variant hover:text-white border-transparent"
                }`}
              >
                <span>{TAB_INFO[tab].icon}</span>
                {TAB_INFO[tab].label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === "analytics"  && <AnalyticsTab />}
              {activeTab === "logs"       && <LogsTab />}
              {activeTab === "curriculum" && <CurriculumTab />}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* FAB */}
        <motion.button
          whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
          onClick={() => setActiveTab("curriculum")}
          className="fixed bottom-12 right-12 gradient-bg text-white px-6 py-4 rounded-full shadow-2xl flex items-center gap-3 font-bold z-40"
          style={{ boxShadow: "0 8px 32px rgba(151,169,255,.25)" }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: "20px" }}>add</span>
          PDF Ekle
        </motion.button>
      </main>
    </div>
  );
}
