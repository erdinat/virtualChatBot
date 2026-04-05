import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "../store/authStore";

interface Tool {
  name: string;
  desc: string;
  tag?: string;
  url: string;
  icon: string;
}

const TOOLS: Tool[] = [
  {
    name: "VSCode",
    desc: "Profesyonel, ücretsiz kod editörü. Otomatik tamamlama, hata vurgulama ve Python uzantısı ile tam destek.",
    url: "https://code.visualstudio.com",
    icon: "code",
  },
  {
    name: "Google Colab",
    desc: "Tarayıcıda çalışır, kurulum gerektirmez. Hücre tabanlı not defteri formatı.",
    tag: "Kurulum Yok",
    url: "https://colab.research.google.com",
    icon: "science",
  },
  {
    name: "Replit",
    desc: "Tarayıcıda anında Python yazıp çalıştır. Hesap açman yeterli.",
    tag: "Kurulum Yok",
    url: "https://replit.com",
    icon: "terminal",
  },
];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { username } = useAuthStore();

  function finish() {
    localStorage.setItem(`onboarding_done_${username}`, "1");
    navigate("/student");
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-6"
      style={{ background: "#0d0a27" }}
    >
      {/* Purple radial glow */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 70% 50% at 50% 0%, rgba(151,169,255,.12) 0%, transparent 70%)",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-2xl"
      >
        {/* Header */}
        <div className="text-center mb-10">
          <div
            className="w-16 h-16 rounded-2xl gradient-bg flex items-center justify-center mx-auto mb-5 shadow-xl"
          >
            <span
              className="material-symbols-outlined text-white"
              style={{ fontSize: "32px", fontVariationSettings: "'FILL' 1" }}
            >
              rocket_launch
            </span>
          </div>
          <h1 className="text-3xl font-black gradient-text mb-2">Başlamadan Önce</h1>
          <p className="text-on-surface-variant text-sm">
            Python'a hoş geldin! Başlamak için ihtiyacın olan her şey burada.
          </p>
        </div>

        {/* Step 1 — Python Kurulumu */}
        <div
          className="glass-card rounded-2xl p-6 mb-4"
          style={{ border: "1px solid rgba(151,169,255,.15)" }}
        >
          <div className="flex items-center gap-3 mb-4">
            <span
              className="w-7 h-7 rounded-full gradient-bg flex items-center justify-center text-white text-xs font-bold shrink-0"
            >
              1
            </span>
            <h2 className="font-bold text-on-surface">Python'u Kur</h2>
          </div>
          <p className="text-sm text-on-surface-variant mb-4 leading-relaxed">
            Python'un resmi sitesinden işletim sistemine uygun yükleyiciyi indir.
            Windows, Mac ve Linux için ayrı sürümler var.
          </p>
          <a
            href="https://python.org/downloads"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white gradient-bg shadow-lg"
          >
            <span className="material-symbols-outlined" style={{ fontSize: "16px", fontVariationSettings: "'FILL' 1" }}>
              download
            </span>
            python.org/downloads
          </a>
          <div
            className="mt-4 flex items-start gap-2 p-3 rounded-xl text-xs text-on-surface-variant"
            style={{ background: "rgba(251,191,36,.08)", border: "1px solid rgba(251,191,36,.2)" }}
          >
            <span className="material-symbols-outlined text-amber-400 shrink-0" style={{ fontSize: "15px", fontVariationSettings: "'FILL' 1" }}>
              warning
            </span>
            <span>
              Windows'ta kurulum sırasında <strong className="text-amber-300">"Add Python to PATH"</strong> kutucuğunu işaretlemeyi unutma!
            </span>
          </div>
        </div>

        {/* Step 2 — IDE Seçimi */}
        <div
          className="glass-card rounded-2xl p-6 mb-4"
          style={{ border: "1px solid rgba(151,169,255,.15)" }}
        >
          <div className="flex items-center gap-3 mb-4">
            <span
              className="w-7 h-7 rounded-full gradient-bg flex items-center justify-center text-white text-xs font-bold shrink-0"
            >
              2
            </span>
            <h2 className="font-bold text-on-surface">Kod Editörü Seç</h2>
          </div>
          <p className="text-sm text-on-surface-variant mb-4">
            Kodunu yazacağın ortamı seç. İki web tabanlı seçenek kurulum gerektirmez.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {TOOLS.map((t) => (
              <a
                key={t.name}
                href={t.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col gap-2 p-4 rounded-xl transition-all hover:scale-[1.02]"
                style={{ background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.08)" }}
              >
                <div className="flex items-center justify-between">
                  <span
                    className="material-symbols-outlined text-primary"
                    style={{ fontSize: "22px", fontVariationSettings: "'FILL' 1" }}
                  >
                    {t.icon}
                  </span>
                  {t.tag && (
                    <span
                      className="text-xs font-semibold px-2 py-0.5 rounded-full"
                      style={{ background: "rgba(52,211,153,.15)", color: "#34d399" }}
                    >
                      {t.tag}
                    </span>
                  )}
                </div>
                <p className="text-sm font-bold text-on-surface">{t.name}</p>
                <p className="text-xs text-on-surface-variant leading-relaxed">{t.desc}</p>
              </a>
            ))}
          </div>
        </div>

        {/* Step 3 — İlk Program */}
        <div
          className="glass-card rounded-2xl p-6 mb-8"
          style={{ border: "1px solid rgba(151,169,255,.15)" }}
        >
          <div className="flex items-center gap-3 mb-4">
            <span
              className="w-7 h-7 rounded-full gradient-bg flex items-center justify-center text-white text-xs font-bold shrink-0"
            >
              3
            </span>
            <h2 className="font-bold text-on-surface">İlk Programını Çalıştır</h2>
          </div>
          <p className="text-sm text-on-surface-variant mb-4">
            Kurulum doğru tamamlandıysa bu satırı yaz ve çalıştır (Run):
          </p>
          <div
            className="rounded-xl p-4 font-mono text-sm mb-3"
            style={{ background: "rgba(0,0,0,.4)", border: "1px solid rgba(255,255,255,.08)" }}
          >
            <span className="text-purple-400">print</span>
            <span className="text-on-surface">(</span>
            <span className="text-green-400">"Merhaba!"</span>
            <span className="text-on-surface">)</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-on-surface-variant">
            <span className="material-symbols-outlined text-green-400" style={{ fontSize: "14px", fontVariationSettings: "'FILL' 1" }}>
              check_circle
            </span>
            <span>Ekranda <strong className="text-green-400">Merhaba!</strong> görürsen hazırsın!</span>
          </div>
        </div>

        {/* CTA */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          onClick={finish}
          className="w-full py-4 rounded-2xl text-white font-bold gradient-bg shadow-xl text-sm mb-3"
        >
          Öğrenmeye Başla →
        </motion.button>
        <button
          onClick={finish}
          className="w-full text-xs text-on-surface-variant hover:text-on-surface transition-colors py-2"
        >
          Zaten biliyorum, atla →
        </button>
      </motion.div>
    </div>
  );
}
