import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Props { onComplete: () => void; }

const DURATION = 12000;

function useGlitchText(target: string, active: boolean) {
  const [display, setDisplay] = useState("");
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%";
  useEffect(() => {
    if (!active) return;
    let iteration = 0;
    const interval = setInterval(() => {
      setDisplay(
        target.split("").map((char, i) =>
          i < iteration ? char : chars[Math.floor(Math.random() * chars.length)]
        ).join("")
      );
      if (iteration >= target.length) clearInterval(interval);
      iteration += 0.4;
    }, 40);
    return () => clearInterval(interval);
  }, [active]); // eslint-disable-line react-hooks/exhaustive-deps
  return display;
}

export default function SplashScreen({ onComplete }: Props) {
  const [showText, setShowText] = useState(false);
  const [visible, setVisible] = useState(true);
  const glitchText = useGlitchText("PYTHON", showText);

  const dismiss = () => {
    setVisible(false);
    setTimeout(onComplete, 700);
  };

  useEffect(() => {
    const t1 = setTimeout(() => setShowText(true), 2200);
    const t2 = setTimeout(dismiss, DURATION);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key="splash"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.7, ease: "easeInOut" }}
          style={{ position: "fixed", inset: 0, zIndex: 9999, background: "#000", overflow: "hidden" }}
        >
          {/* ── Video ── */}
          <video
            autoPlay
            muted
            playsInline
            onEnded={dismiss}
            style={{
              position: "absolute", inset: 0,
              width: "100%", height: "100%",
              objectFit: "cover",
            }}
          >
            <source src="/snake.mp4" type="video/mp4" />
          </video>

          {/* ── CRT scanlines ── */}
          <div style={{
            position: "absolute", inset: 0, zIndex: 2, pointerEvents: "none",
            background: "repeating-linear-gradient(to bottom, rgba(0,0,0,0) 0px, rgba(0,0,0,0) 2px, rgba(0,0,0,0.1) 2px, rgba(0,0,0,0.1) 4px)",
          }} />

          {/* ── Vignette ── */}
          <div style={{
            position: "absolute", inset: 0, zIndex: 3, pointerEvents: "none",
            background: "radial-gradient(circle, transparent 30%, rgba(0,0,0,0.75) 90%)",
          }} />

          {/* ── Bottom fade ── */}
          <div style={{
            position: "absolute", bottom: 0, left: 0, right: 0,
            height: "40%", zIndex: 4, pointerEvents: "none",
            background: "linear-gradient(to top, rgba(4,2,15,0.95) 0%, transparent 100%)",
          }} />

          {/* ── Text ── */}
          <style>{`
            @keyframes flicker { 0%,100%{opacity:1} 5%{opacity:0.9} 30%{opacity:0.97} }
            @keyframes subIn { from{opacity:0;letter-spacing:0.9em} to{opacity:0.65;letter-spacing:0.55em} }
          `}</style>

          <AnimatePresence>
            {showText && (
              <motion.div
                key="text"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, ease: "easeOut" }}
                style={{
                  position: "absolute", bottom: "12%",
                  left: 0, right: 0, textAlign: "center",
                  zIndex: 10, animation: "flicker 5s infinite",
                }}
              >
                <p style={{
                  fontFamily: "'Rajdhani',sans-serif",
                  fontSize: "11px", letterSpacing: "0.55em",
                  textTransform: "uppercase",
                  color: "rgba(148,163,184,0.65)",
                  margin: "0 0 16px",
                  animation: "subIn 0.9s ease-out forwards",
                }}>
                  YAPAY ZEKA DESTEKLİ
                </p>
                <h1 style={{
                  fontFamily: "'Orbitron',sans-serif",
                  fontWeight: 900,
                  fontSize: "clamp(48px,10vw,100px)",
                  letterSpacing: "0.06em",
                  margin: 0,
                  background: "linear-gradient(90deg,#00B4FF,#8800FF,#f093fb)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                  filter: "drop-shadow(0 0 28px rgba(136,0,255,0.55))",
                }}>
                  {glitchText}
                </h1>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Progress bar ── */}
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: DURATION / 1000, ease: "linear" }}
            style={{
              position: "absolute", bottom: 0, left: 0,
              width: "100%", height: "2px", zIndex: 20,
              background: "linear-gradient(90deg,#00B4FF,#8800FF,#f093fb)",
              transformOrigin: "left center", opacity: 0.6,
            }}
          />

          {/* ── Skip ── */}
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.5 }}
            onClick={dismiss}
            style={{
              position: "absolute", bottom: "5%", left: "50%",
              transform: "translateX(-50%)", zIndex: 20,
              background: "transparent", border: "none",
              borderBottom: "1px solid rgba(255,255,255,0.1)",
              color: "rgba(255,255,255,0.22)", padding: "4px 2px",
              fontSize: "10px", letterSpacing: "0.35em",
              textTransform: "uppercase", cursor: "pointer",
              fontFamily: "'Rajdhani',sans-serif",
              transition: "color .2s, border-color .2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "rgba(255,255,255,0.55)";
              e.currentTarget.style.borderBottomColor = "rgba(255,255,255,0.28)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "rgba(255,255,255,0.22)";
              e.currentTarget.style.borderBottomColor = "rgba(255,255,255,0.1)";
            }}
          >
            ATLA
          </motion.button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
