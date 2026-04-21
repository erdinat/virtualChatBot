import type { TopicLevel } from "./types";

interface Props {
  name: string | null;
  username: string | null;
  activeView: "curriculum" | "chat";
  recentHistory: { role: string; content: string }[];
  nextTopic: { topic?: { name: string } } | null | undefined;
  avgMastery: number;
  avatarUrl: string | undefined;
  initials: string;
  onLogout: () => void;
}

const AVATAR: Record<string, string> = {
  ali:      "https://cdn-icons-png.flaticon.com/512/4202/4202839.png",
  ayse:     "https://cdn-icons-png.flaticon.com/512/4202/4202850.png",
  ogretmen: "https://cdn-icons-png.flaticon.com/512/4202/4202843.png",
};

export function getAvatarUrl(username: string | null): string | undefined {
  return username ? AVATAR[username] : undefined;
}

export default function StudentSidebar({
  name, username, activeView, recentHistory,
  nextTopic, avgMastery, avatarUrl, initials, onLogout,
}: Props) {
  return (
    <>
      <div className="px-6 mb-8 flex items-center gap-3">
        <span className="material-symbols-outlined text-primary text-3xl"
          style={{ fontVariationSettings: "'FILL' 1" }}>school</span>
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
        <div className="p-4 rounded-xl border"
          style={{ background: "rgba(92,49,135,.2)", borderColor: "rgba(92,49,135,.3)" }}>
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
        onClick={onLogout}
        className="mt-6 mx-6 flex items-center gap-3 text-on-surface-variant hover:text-error transition-colors px-4 py-3 group">
        <span className="material-symbols-outlined group-hover:scale-110 transition-transform"
          style={{ fontSize: "20px" }}>logout</span>
        <span className="text-sm font-medium">Çıkış Yap</span>
      </button>
    </>
  );
}
