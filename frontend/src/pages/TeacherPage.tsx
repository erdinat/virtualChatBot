import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useAuthStore } from "../store/authStore";
import { getStudents, getLogs, getCurriculum, uploadPdfs, getPdfStatus } from "../api/client";

type Tab = "analytics" | "logs" | "curriculum";

/* ── Student Analytics Tab ───────────────────────────────── */
function AnalyticsTab() {
  const { data: students = [], isLoading: studentsLoading } = useQuery({ queryKey: ["students"], queryFn: getStudents });
  const { data: curriculum = [] } = useQuery({ queryKey: ["curriculum"], queryFn: getCurriculum });
  const [search, setSearch] = useState("");

  const filtered = (students as any[]).filter((s) =>
    s.username.toLowerCase().includes(search.toLowerCase())
  );

  const topicStats = (curriculum as any[]).slice(0, 4).map((c: any) => {
    const vals = (students as any[]).map((s: any) => s.mastery?.[c.name] ?? 0);
    const avg = vals.length ? vals.reduce((a: number, b: number) => a + b, 0) / vals.length : 0;
    return { name: c.name, avg };
  });

  const icons = [
    "https://cdn-icons-png.flaticon.com/512/2010/2010990.png",
    "https://cdn-icons-png.flaticon.com/512/8013/8013809.png",
    "https://cdn-icons-png.flaticon.com/512/15401/15401183.png",
    "https://cdn-icons-png.flaticon.com/512/18252/18252341.png",
  ];

  return (
    <div className="space-y-8">
      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {topicStats.length > 0 ? topicStats.map((t, i) => {
          const pct = Math.round(t.avg * 100);
          const color = pct >= 80 ? "#4ade80" : pct >= 60 ? "#fbbf24" : "#ff6e84";
          return (
            <div key={t.name} className="glass-card p-6 rounded-xl relative overflow-hidden group flex flex-col justify-between" style={{ minHeight: "140px" }}>
              <div className="absolute top-3 right-3 opacity-10 group-hover:opacity-20 transition-opacity pointer-events-none">
                <img src={icons[i]} alt="" style={{ width: "48px", height: "48px", objectFit: "contain", filter: "brightness(0) invert(1)" }} />
              </div>
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest leading-snug line-clamp-2 pr-12">{t.name}</p>
              <div>
                <h3 className="text-3xl font-black text-white">
                  %{pct}
                  <span className="text-sm font-medium ml-1" style={{ color }}>
                    {pct >= 70 ? "↑" : "↓"}
                  </span>
                </h3>
                <p className="text-xs text-on-surface-variant mt-1 italic">Ortalama başarı oranı</p>
              </div>
            </div>
          );
        }) : Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="glass-card p-6 rounded-xl animate-pulse">
            <div className="h-3 w-24 rounded bg-white/10 mb-3" />
            <div className="h-8 w-16 rounded bg-white/10 mb-2" />
            <div className="h-3 w-32 rounded bg-white/10" />
          </div>
        ))}
      </div>

      {/* Student table */}
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="p-6 border-b border-white/5 flex flex-wrap justify-between items-center gap-4">
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
          {studentsLoading ? (
            <div className="p-8 text-center text-on-surface-variant text-sm">Yükleniyor…</div>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="text-xs uppercase tracking-widest font-black text-on-surface-variant" style={{ background: "rgba(255,255,255,.05)" }}>
                  <th className="px-8 py-4">Öğrenci</th>
                  <th className="px-8 py-4">Etkileşim</th>
                  <th className="px-8 py-4">Genel İlerleme</th>
                  <th className="px-8 py-4">Başarı (/10)</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s: any) => {
                  const pct = Math.round((s.avg_mastery ?? 0) * 100);
                  const score = ((s.success_rate ?? 0) * 10).toFixed(1);
                  const rate = s.success_rate ?? 0;
                  const scoreColor = rate >= 0.8 ? "#4ade80" : rate >= 0.6 ? "#fbbf24" : "#ff6e84";
                  const scoreBg    = rate >= 0.8 ? "rgba(74,222,128,.1)" : rate >= 0.6 ? "rgba(251,191,36,.1)" : "rgba(255,110,132,.1)";
                  const scoreBorder= rate >= 0.8 ? "rgba(74,222,128,.2)" : rate >= 0.6 ? "rgba(251,191,36,.2)" : "rgba(255,110,132,.2)";
                  const initial = (s.username ?? "?")[0]?.toUpperCase() ?? "?";

                  return (
                    <tr key={s.username} className="border-t border-white/5 hover:bg-white/[.03] transition-colors">
                      <td className="px-8 py-5">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full p-[2px] shrink-0"
                            style={{ background: "linear-gradient(135deg,#97a9ff,#f8acff)" }}>
                            <div className="w-full h-full rounded-full bg-surface flex items-center justify-center font-bold text-sm text-primary">
                              {initial}
                            </div>
                          </div>
                          <div>
                            <p className="font-bold text-white capitalize">{s.username}</p>
                            <p className="text-xs text-on-surface-variant">Öğrenci</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-8 py-5 text-sm text-on-surface-variant">{s.interaction_count ?? 0} soru</td>
                      <td className="px-8 py-5">
                        <div className="w-40 h-1.5 bg-surface-container-highest rounded-full overflow-hidden relative">
                          <div className="absolute top-0 left-0 h-full shimmer-bar" style={{ width: `${pct}%` }} />
                        </div>
                        <p className="text-xs mt-2 font-bold text-primary">%{pct}</p>
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
                      {search ? "Öğrenci bulunamadı" : "Henüz öğrenci verisi yok"}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Logs Tab ────────────────────────────────────────────── */
function LogsTab() {
  const [usernameFilter, setUsernameFilter] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ["logs", usernameFilter],
    queryFn: () => getLogs(usernameFilter || undefined),
  });

  return (
    <div className="space-y-4 flex flex-col" style={{ height: "calc(100vh - 280px)" }}>
      <div className="flex gap-3 shrink-0 flex-wrap">
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
        {isLoading ? (
          <div className="p-8 text-center text-on-surface-variant text-sm">Yükleniyor…</div>
        ) : (
          <div className="p-6 space-y-3">
            {(logs as any[]).map((log: any, i: number) => {
              const isUser = log.role === "user";
              const isOpen = expanded === i;
              return (
                <div
                  key={i}
                  onClick={() => setExpanded(isOpen ? null : i)}
                  className="flex gap-4 items-start p-4 rounded-xl border-l-2 transition-colors hover:bg-white/[.02] cursor-pointer"
                  style={{ background: "rgba(255,255,255,.04)", borderLeftColor: isUser ? "#97a9ff" : "#f8acff" }}
                >
                  <span className="material-symbols-outlined mt-0.5 shrink-0"
                    style={{ fontSize: "20px", color: isUser ? "#97a9ff" : "#f8acff" }}>
                    {isUser ? "chat" : "smart_toy"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center mb-1 gap-2">
                      <span className="font-bold text-sm text-on-surface">{log.username}</span>
                      <span className="text-xs text-on-surface-variant shrink-0">
                        {new Date(log.timestamp).toLocaleString("tr-TR")}
                      </span>
                    </div>
                    <p className={`text-xs text-on-surface-variant italic ${isOpen ? "" : "truncate"}`}>
                      {log.content}
                    </p>
                    {!isOpen && log.content?.length > 80 && (
                      <span className="text-xs text-primary mt-1 block">Tümünü gör ↓</span>
                    )}
                  </div>
                </div>
              );
            })}
            {!(logs as any[]).length && (
              <div className="text-center py-12 text-on-surface-variant text-sm">
                {usernameFilter ? `"${usernameFilter}" için log bulunamadı` : "Log kaydı bulunamadı"}
              </div>
            )}
          </div>
        )}
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
        <div className="p-5 border-b border-white/5 flex items-center gap-2">
          <img src="https://cdn-icons-png.flaticon.com/512/942/942799.png" alt="" style={{ width: "18px", height: "18px", filter: "brightness(0) invert(1)", opacity: 0.6 }} />
          <h4 className="font-bold text-on-surface">Müfredat Konuları</h4>
          <span className="ml-auto text-xs text-on-surface-variant">{(curriculum as any[]).length} konu</span>
        </div>
        <div className="p-4 space-y-2">
          {(curriculum as any[]).map((c: any, i: number) => (
            <div key={c.name} className="flex items-center justify-between p-3 rounded-xl transition-colors"
              style={{ background: "rgba(255,255,255,.04)" }}>
              <div className="flex items-center gap-3">
                <span className="w-5 h-5 rounded-full text-xs font-bold flex items-center justify-center text-primary"
                  style={{ background: "rgba(151,169,255,.15)" }}>
                  {i + 1}
                </span>
                <span className="text-sm font-medium text-on-surface">{c.name}</span>
              </div>
              <div className="flex text-amber-400">
                {Array.from({ length: 5 }).map((_, j) => (
                  <span key={j} className="material-symbols-outlined"
                    style={{ fontSize: "13px", fontVariationSettings: j < (c.difficulty ?? 3) ? "'FILL' 1" : "'FILL' 0" }}>
                    star
                  </span>
                ))}
              </div>
            </div>
          ))}
          {!(curriculum as any[]).length && (
            <div className="py-8 text-center text-on-surface-variant text-sm">Müfredat yükleniyor…</div>
          )}
        </div>
      </div>

      {/* PDF Upload */}
      <div className="space-y-4">
        {/* RAG status */}
        <div className="p-4 rounded-xl flex items-center gap-3 glass-card">
          <div className="w-3 h-3 rounded-full shrink-0 animate-pulse" style={{ background: pdfStatus?.loaded ? "#4ade80" : "#ff6e84" }} />
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
          className="p-8 rounded-xl text-center cursor-pointer transition-all"
          style={{ border: "2px dashed rgba(151,169,255,.3)", background: "rgba(255,255,255,.03)" }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "rgba(151,169,255,.6)")}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "rgba(151,169,255,.3)")}
        >
          <span className="material-symbols-outlined text-primary mb-3 block" style={{ fontSize: "40px" }}>upload_file</span>
          <p className="text-sm font-semibold text-on-surface">Müfredat PDF Yükle</p>
          <p className="text-xs text-on-surface-variant mt-1">Sanal asistanı eğitmek için döküman ekleyin</p>
          <input
            ref={fileRef} type="file" accept=".pdf" multiple
            onChange={(e) => setFiles(Array.from(e.target.files ?? []).filter((f) => f.name.endsWith(".pdf")))}
            className="hidden"
          />
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
                <button onClick={() => setFiles((prev) => prev.filter((x) => x.name !== f.name))}
                  className="text-on-surface-variant hover:text-error transition-colors shrink-0">
                  <span className="material-symbols-outlined" style={{ fontSize: "18px" }}>close</span>
                </button>
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
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebar, setMobileSidebar] = useState(false);

  const AVATAR: Record<string, string> = {
    ali:       "https://cdn-icons-png.flaticon.com/512/4202/4202839.png",
    ayse:      "https://cdn-icons-png.flaticon.com/512/4202/4202850.png",
    ogretmen:  "https://cdn-icons-png.flaticon.com/512/4202/4202843.png",
  };
  const avatarUrl = username ? AVATAR[username] : undefined;
  const initials = (name ?? username ?? "?")[0].toUpperCase();

  const TAB_INFO: Record<Tab, { label: string; icon: string; matIcon: string }> = {
    analytics:  { label: "Öğrenci Analitiği", icon: "https://cdn-icons-png.flaticon.com/512/777/777502.png",   matIcon: "bar_chart" },
    logs:       { label: "Sistem Logları",     icon: "https://cdn-icons-png.flaticon.com/512/4731/4731557.png", matIcon: "monitoring" },
    curriculum: { label: "Müfredat",           icon: "https://cdn-icons-png.flaticon.com/512/942/942799.png",   matIcon: "menu_book" },
  };

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="px-6 mb-10">
        <h1 className="text-xl font-black gradient-text tracking-tighter">Sanal Öğretmen</h1>
        <p className="text-slate-400 text-xs mt-0.5 uppercase tracking-widest font-bold">Eğitmen Paneli</p>
      </div>

      {/* Profile */}
      <div className="mx-4 mb-8 p-3 rounded-xl flex items-center gap-3" style={{ background: "rgba(255,255,255,.05)" }}>
        <div className="w-9 h-9 rounded-full overflow-hidden gradient-bg flex items-center justify-center font-bold text-white shrink-0">
          {avatarUrl ? <img src={avatarUrl} alt={name ?? ""} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : initials}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-white truncate">{name}</p>
          <p className="text-xs text-slate-400">Eğitmen</p>
        </div>
      </div>

      {/* Nav — directly controls activeTab */}
      <nav className="flex-1 space-y-1 px-2">
        {(["analytics", "logs", "curriculum"] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => { setActiveTab(tab); setMobileSidebar(false); }}
            className={`w-full text-left py-3 px-4 flex items-center gap-3 rounded-xl transition-all text-sm font-medium ${
              activeTab === tab
                ? "text-white font-bold"
                : "text-slate-400 hover:bg-white/5 hover:text-white"
            }`}
            style={activeTab === tab ? { background: "linear-gradient(to right,rgba(102,126,234,.35),rgba(102,126,234,.1))" } : {}}
          >
            <img
              src={TAB_INFO[tab].icon} alt=""
              style={{ width: "18px", height: "18px", objectFit: "contain", filter: "brightness(0) invert(1)", opacity: activeTab === tab ? 1 : 0.45 }}
            />
            {TAB_INFO[tab].label}
          </button>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-4 mt-auto pt-6 border-t border-white/5 space-y-2">
        <button
          onClick={() => { logout(); window.location.href = "/"; }}
          className="flex items-center gap-3 text-slate-400 hover:text-error w-full px-4 py-2.5 hover:bg-error/10 rounded-xl transition-colors"
        >
          <span className="material-symbols-outlined" style={{ fontSize: "18px" }}>logout</span>
          <span className="font-medium text-sm">Çıkış Yap</span>
        </button>
      </div>
    </>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-surface text-on-surface font-body">

      {/* ── Sidebar (desktop) ── */}
      <AnimatePresence initial={false}>
        {sidebarOpen && (
          <motion.aside
            key="sidebar"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 272, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            className="hidden md:flex h-full flex-col py-8 z-50 border-r border-white/5 overflow-hidden shrink-0"
            style={{ background: "#181538" }}
          >
            <SidebarContent />
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ── Sidebar (mobile overlay) ── */}
      <AnimatePresence>
        {mobileSidebar && (
          <>
            <motion.div
              key="backdrop"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setMobileSidebar(false)}
              className="fixed inset-0 bg-black/60 z-40 md:hidden"
            />
            <motion.aside
              key="mobile-sidebar"
              initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
              transition={{ type: "tween", duration: 0.25 }}
              className="fixed left-0 top-0 w-72 h-full flex flex-col py-8 z-50 border-r border-white/5 md:hidden overflow-hidden"
              style={{ background: "#181538" }}
            >
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── Main ── */}
      <main className="flex-1 h-full overflow-y-auto relative min-w-0" style={{ background: "#0d0a27" }}>
        {/* Decorative glows */}
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full pointer-events-none"
          style={{ background: "rgba(151,169,255,.05)", filter: "blur(120px)", zIndex: 0 }} />
        <div className="absolute bottom-0 left-0 w-72 h-72 rounded-full pointer-events-none"
          style={{ background: "rgba(248,172,255,.05)", filter: "blur(100px)", zIndex: 0 }} />

        <div className="relative z-10 p-6 lg:p-10">
          {/* Header row */}
          <header className="flex items-center gap-4 mb-10">
            {/* Sidebar toggle */}
            <button
              onClick={() => sidebarOpen ? setSidebarOpen(false) : setSidebarOpen(true)}
              className="hidden md:flex w-9 h-9 items-center justify-center rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors shrink-0"
            >
              <span className="material-symbols-outlined" style={{ fontSize: "20px" }}>
                {sidebarOpen ? "menu_open" : "menu"}
              </span>
            </button>
            {/* Mobile hamburger */}
            <button
              onClick={() => setMobileSidebar(true)}
              className="md:hidden flex w-9 h-9 items-center justify-center rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors shrink-0"
            >
              <span className="material-symbols-outlined" style={{ fontSize: "20px" }}>menu</span>
            </button>

            <div className="flex-1 min-w-0">
              <h2 className="text-2xl font-bold text-white">{TAB_INFO[activeTab].label}</h2>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <div className="w-9 h-9 rounded-full overflow-hidden gradient-bg flex items-center justify-center font-bold text-white shrink-0">
                {avatarUrl ? <img src={avatarUrl} alt={name ?? ""} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : initials}
              </div>
            </div>
          </header>

          {/* Tab content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.18 }}
            >
              {activeTab === "analytics"  && <AnalyticsTab />}
              {activeTab === "logs"       && <LogsTab />}
              {activeTab === "curriculum" && <CurriculumTab />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
