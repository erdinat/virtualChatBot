import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { login } from "../api/client";
import { useAuthStore } from "../store/authStore";
import { useParticleCanvas } from "../hooks/useParticleCanvas";

/* ── Snake canvas ── */
function SnakeCanvas({ btnRef, formRef }: {
  btnRef: React.RefObject<HTMLButtonElement | null>;
  formRef: React.RefObject<HTMLDivElement | null>;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;

    // Hide default cursor on login page
    document.body.style.cursor = "none";

    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize();
    window.addEventListener("resize", resize);

    const N = 65;       // longer snake
    const SEG_LEN = 8;

    const getBtn = () => btnRef.current?.getBoundingClientRect() ?? null;
    const getHome = () => {
      const r = getBtn();
      return r
        ? { x: r.left + r.width / 2, y: r.top + r.height / 2 }
        : { x: window.innerWidth / 2, y: window.innerHeight * 0.62 };
    };

    // Init coiled around button
    const h0 = getHome();
    const segs = Array.from({ length: N }, (_, i) => {
      const angle = (i / N) * Math.PI * 3;
      const r = getBtn();
      const rx = r ? r.width / 2 + 20 : 95;
      const ry = r ? r.height / 2 + 20 : 30;
      return { x: h0.x + Math.cos(angle) * rx, y: h0.y + Math.sin(angle) * ry };
    });

    const mouse = { x: -9999, y: -9999, vx: 0, vy: 0 };
    let lastMoveTime = 0;
    let state: "hunt" | "idle" = "idle";
    let idleT = 0;
    let raf: number;

    const onMouse = (e: MouseEvent) => {
      mouse.vx = e.clientX - mouse.x;
      mouse.vy = e.clientY - mouse.y;
      mouse.x = e.clientX;
      mouse.y = e.clientY;
      lastMoveTime = Date.now();
      state = "hunt";
    };
    window.addEventListener("mousemove", onMouse);

    /* ── helpers ── */
    const getNormal = (i: number) => {
      const a = segs[Math.max(i - 1, 0)], b = segs[Math.min(i + 1, N - 1)];
      const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
      return { x: -dy / d, y: dx / d };
    };

    // FIXED: thin nose → thick uniform body → thin tail
    const bodyWidth = (i: number) => {
      const t = i / (N - 1);
      if (t < 0.04) return 2 + t * 200;                          // very thin nose, quickly widens
      if (t < 0.10) return 10 + (t - 0.04) * 50;                 // neck widens
      if (t < 0.60) return 13;                                    // thick uniform mid-body
      return Math.max(1.2, 13 * Math.pow((1 - t) / 0.40, 0.6));  // smooth tail taper
    };

    /* ── draw tapered body ── */
    const drawBody = () => {
      const left: { x: number; y: number }[] = [];
      const right: { x: number; y: number }[] = [];
      for (let i = 0; i < N; i++) {
        const n = getNormal(i), w = bodyWidth(i);
        left.push({ x: segs[i].x + n.x * w, y: segs[i].y + n.y * w });
        right.push({ x: segs[i].x - n.x * w, y: segs[i].y - n.y * w });
      }

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(left[0].x, left[0].y);
      for (let i = 1; i < N - 1; i++) {
        const mx = (left[i].x + left[i + 1].x) / 2, my = (left[i].y + left[i + 1].y) / 2;
        ctx.quadraticCurveTo(left[i].x, left[i].y, mx, my);
      }
      ctx.lineTo(left[N - 1].x, left[N - 1].y);
      // round tail
      ctx.lineTo(segs[N - 1].x, segs[N - 1].y);
      ctx.lineTo(right[N - 1].x, right[N - 1].y);
      for (let i = N - 2; i > 0; i--) {
        const mx = (right[i].x + right[i + 1].x) / 2, my = (right[i].y + right[i + 1].y) / 2;
        ctx.quadraticCurveTo(right[i].x, right[i].y, mx, my);
      }
      ctx.lineTo(right[0].x, right[0].y);
      ctx.closePath();

      // dark purple body fill
      ctx.shadowBlur = 20;
      ctx.shadowColor = "rgba(102,126,234,0.45)";
      ctx.fillStyle = "#14103d";
      ctx.fill();
      ctx.shadowBlur = 0;

      // top sheen
      ctx.beginPath();
      ctx.moveTo(left[0].x, left[0].y);
      for (let i = 1; i < N - 1; i++) {
        const mx = (left[i].x + left[i + 1].x) / 2, my = (left[i].y + left[i + 1].y) / 2;
        ctx.quadraticCurveTo(left[i].x, left[i].y, mx, my);
      }
      ctx.strokeStyle = "rgba(151,169,255,0.22)";
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // belly stripe
      ctx.beginPath();
      ctx.moveTo(segs[0].x, segs[0].y);
      for (let i = 1; i < N - 1; i++) {
        const mx = (segs[i].x + segs[i + 1].x) / 2, my = (segs[i].y + segs[i + 1].y) / 2;
        ctx.quadraticCurveTo(segs[i].x, segs[i].y, mx, my);
      }
      ctx.strokeStyle = "rgba(180,160,255,0.12)";
      ctx.lineWidth = 2.5;
      ctx.stroke();

      ctx.restore();
    };

    /* ── scales ── */
    const drawScales = () => {
      for (let i = 3; i < N - 1; i += 3) {
        const n = getNormal(i), w = bodyWidth(i) * 0.7;
        const angle = Math.atan2(n.y, n.x);
        for (const side of [-0.6, 0, 0.6]) {
          const sx = segs[i].x + n.x * w * side;
          const sy = segs[i].y + n.y * w * side;
          ctx.save();
          ctx.translate(sx, sy);
          ctx.rotate(angle + Math.PI / 2);
          ctx.globalAlpha = 0.18;
          ctx.beginPath();
          ctx.ellipse(0, 0, w * 0.55, w * 0.3, 0, 0, Math.PI * 2);
          ctx.fillStyle = i % 6 === 0 ? "rgba(151,169,255,0.6)" : "rgba(240,147,251,0.5)";
          ctx.fill();
          ctx.strokeStyle = "rgba(151,169,255,0.12)";
          ctx.lineWidth = 0.4;
          ctx.stroke();
          ctx.restore();
        }
      }
    };

    /* ── head ── */
    const drawHead = () => {
      const head = segs[0], neck = segs[2];
      const angle = Math.atan2(head.y - neck.y, head.x - neck.x);
      ctx.save();
      ctx.translate(head.x, head.y);
      ctx.rotate(angle);

      // jaw (lower, wider)
      ctx.shadowBlur = 22;
      ctx.shadowColor = "rgba(102,126,234,0.6)";
      ctx.beginPath();
      ctx.ellipse(5, 1.5, 14, 7, 0, 0, Math.PI * 2);
      ctx.fillStyle = "#111040";
      ctx.fill();
      // snout (upper, narrower)
      ctx.beginPath();
      ctx.ellipse(5, -1, 13, 6, 0, 0, Math.PI * 2);
      ctx.fillStyle = "#1a165a";
      ctx.fill();
      ctx.strokeStyle = "rgba(151,169,255,0.4)";
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // labial groove line
      ctx.beginPath();
      ctx.moveTo(-2, 0); ctx.lineTo(12, 0);
      ctx.strokeStyle = "rgba(80,60,180,0.35)";
      ctx.lineWidth = 0.7;
      ctx.stroke();

      // nostrils
      for (const ny of [-3, 3]) {
        ctx.beginPath();
        ctx.ellipse(10, ny, 1.5, 1, 0, 0, Math.PI * 2);
        ctx.fillStyle = "#080520";
        ctx.fill();
      }

      // eyes
      for (const ey of [-4, 4]) {
        // eye socket
        ctx.beginPath(); ctx.arc(4, ey, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#0a0830"; ctx.fill();
        // iris
        const iris = ctx.createRadialGradient(4, ey, 0.5, 4, ey, 3.5);
        iris.addColorStop(0, "#c0b0ff");
        iris.addColorStop(0.5, "#7060e0");
        iris.addColorStop(1, "#1a1050");
        ctx.beginPath(); ctx.arc(4, ey, 3.5, 0, Math.PI * 2);
        ctx.fillStyle = iris;
        ctx.shadowBlur = 12; ctx.shadowColor = "#97a9ff";
        ctx.fill(); ctx.shadowBlur = 0;
        // vertical slit pupil
        ctx.beginPath(); ctx.ellipse(4, ey, 1, 3, 0, 0, Math.PI * 2);
        ctx.fillStyle = "#000"; ctx.fill();
        // corneal shine
        ctx.beginPath(); ctx.ellipse(3, ey - 1.5, 0.9, 0.6, -0.5, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255,255,255,0.7)"; ctx.fill();
      }

      // tongue
      if (Math.sin(idleT * 6) > 0.1) {
        const flicker = 0.6 + Math.sin(idleT * 18) * 0.4;
        ctx.globalAlpha = flicker;
        ctx.beginPath();
        ctx.moveTo(16, 0); ctx.lineTo(22, 0);
        ctx.moveTo(22, 0); ctx.lineTo(27, -4);
        ctx.moveTo(22, 0); ctx.lineTo(27, 4);
        ctx.strokeStyle = "#f093fb";
        ctx.lineWidth = 1.4; ctx.lineCap = "round";
        ctx.shadowBlur = 6; ctx.shadowColor = "#f093fb";
        ctx.stroke(); ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;
      }

      ctx.restore();
    };

    /* ── rat cursor ── */
    const drawRat = (rx: number, ry: number, overForm: boolean) => {
      if (rx < 0 || ry < 0 || overForm) return;
      const vx = mouse.vx, vy = mouse.vy;
      const angle = Math.hypot(vx, vy) > 0.5 ? Math.atan2(vy, vx) : 0;
      ctx.save();
      ctx.translate(rx, ry);
      ctx.rotate(angle);

      // tail — purple tint
      ctx.beginPath();
      ctx.moveTo(12, 2);
      ctx.bezierCurveTo(22, 8, 28, -4, 34, -2);
      ctx.strokeStyle = "rgba(151,130,220,0.7)";
      ctx.lineWidth = 1.6; ctx.lineCap = "round"; ctx.stroke();

      // body
      ctx.beginPath(); ctx.ellipse(2, 2, 9, 6, 0.25, 0, Math.PI * 2);
      ctx.fillStyle = "#2a2250";
      ctx.shadowBlur = 10; ctx.shadowColor = "rgba(102,126,234,0.4)";
      ctx.fill(); ctx.shadowBlur = 0;

      // body sheen
      ctx.beginPath(); ctx.ellipse(0, 0, 7, 4, 0.25, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(151,169,255,0.12)"; ctx.fill();

      // head
      ctx.beginPath(); ctx.ellipse(-8, 0, 6.5, 5, -0.2, 0, Math.PI * 2);
      ctx.fillStyle = "#322860"; ctx.fill();

      // ears
      for (const s of [-1, 1]) {
        ctx.beginPath(); ctx.arc(-6, s * 5.5, 3, 0, Math.PI * 2);
        ctx.fillStyle = "#4a3880"; ctx.fill();
        ctx.beginPath(); ctx.arc(-6, s * 5.5, 1.6, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(240,147,251,0.5)"; ctx.fill();
      }

      // eye — neon purple
      ctx.beginPath(); ctx.arc(-11, -2, 1.6, 0, Math.PI * 2);
      ctx.fillStyle = "#97a9ff";
      ctx.shadowBlur = 8; ctx.shadowColor = "#97a9ff";
      ctx.fill(); ctx.shadowBlur = 0;
      ctx.beginPath(); ctx.arc(-11, -2, 0.7, 0, Math.PI * 2);
      ctx.fillStyle = "#000"; ctx.fill();
      ctx.beginPath(); ctx.arc(-11.5, -2.5, 0.4, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(255,255,255,0.8)"; ctx.fill();

      // nose
      ctx.beginPath(); ctx.arc(-14, 0.5, 1.2, 0, Math.PI * 2);
      ctx.fillStyle = "#f093fb";
      ctx.shadowBlur = 6; ctx.shadowColor = "#f093fb";
      ctx.fill(); ctx.shadowBlur = 0;

      // whiskers
      for (const wy of [-1.5, 0, 1.5]) {
        ctx.beginPath();
        ctx.moveTo(-14, 0.5 + wy);
        ctx.lineTo(-22, 0.5 + wy * 2.5);
        ctx.strokeStyle = "rgba(151,169,255,0.4)";
        ctx.lineWidth = 0.6; ctx.stroke();
      }

      ctx.restore();
    };

    /* ── catch system ── */
    type Particle = { x: number; y: number; vx: number; vy: number; life: number; color: string };
    let snakeScore = 0;
    let ratHidden = false;
    let ratHiddenTimer = 0;
    let flashTimer = 0;
    let particles: Particle[] = [];
    const floatingTexts: { x: number; y: number; life: number; text: string }[] = [];

    const triggerCatch = (cx: number, cy: number) => {
      snakeScore++;
      ratHidden = true;
      ratHiddenTimer = 120; // 2s at 60fps
      flashTimer = 18;

      // Explosion particles
      for (let i = 0; i < 22; i++) {
        const angle = (i / 22) * Math.PI * 2;
        const speed = 2 + Math.random() * 4;
        const colors = ["#f093fb", "#97a9ff", "#667eea", "#fff", "#ff6eb4"];
        particles.push({
          x: cx, y: cy,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 1,
          color: colors[i % colors.length],
        });
      }

      // Floating score text
      floatingTexts.push({ x: cx, y: cy - 10, life: 1, text: `+1 🐍` });
    };

    const spawnRat = (W: number, H: number) => {
      // Spawn at random edge, far from snake head
      const edge = Math.floor(Math.random() * 4);
      if (edge === 0) { mouse.x = Math.random() * W; mouse.y = 30; }
      else if (edge === 1) { mouse.x = W - 30; mouse.y = Math.random() * H; }
      else if (edge === 2) { mouse.x = Math.random() * W; mouse.y = H - 30; }
      else { mouse.x = 30; mouse.y = Math.random() * H; }
    };

    /* ── score overlay ── */
    const drawScore = (W: number) => {
      ctx.save();
      ctx.font = "bold 14px 'Inter', sans-serif";
      ctx.fillStyle = "rgba(151,169,255,0.7)";
      ctx.textAlign = "right";
      ctx.fillText(`🐍 ${snakeScore}`, W - 20, 30);
      ctx.restore();
    };

    /* ── flash overlay ── */
    const drawFlash = (W: number, H: number) => {
      if (flashTimer <= 0) return;
      const alpha = (flashTimer / 18) * 0.35;
      const g = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.8);
      g.addColorStop(0, `rgba(240,80,180,0)`);
      g.addColorStop(0.6, `rgba(240,80,180,0)`);
      g.addColorStop(1, `rgba(240,80,180,${alpha})`);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
      flashTimer--;
    };

    /* ── draw particles ── */
    const drawParticles = () => {
      particles = particles.filter(p => p.life > 0);
      for (const p of particles) {
        ctx.save();
        ctx.globalAlpha = p.life;
        ctx.shadowBlur = 8; ctx.shadowColor = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3 * p.life, 0, Math.PI * 2);
        ctx.fillStyle = p.color; ctx.fill();
        ctx.restore();
        p.x += p.vx; p.y += p.vy;
        p.vx *= 0.92; p.vy *= 0.92;
        p.life -= 0.035;
      }
    };

    /* ── floating texts ── */
    const drawFloatingTexts = () => {
      for (let i = floatingTexts.length - 1; i >= 0; i--) {
        const ft = floatingTexts[i];
        ctx.save();
        ctx.globalAlpha = ft.life;
        ctx.font = "bold 18px 'Inter',sans-serif";
        ctx.fillStyle = "#f093fb";
        ctx.textAlign = "center";
        ctx.shadowBlur = 10; ctx.shadowColor = "#f093fb";
        ctx.fillText(ft.text, ft.x, ft.y);
        ctx.restore();
        ft.y -= 1.2;
        ft.life -= 0.022;
        if (ft.life <= 0) floatingTexts.splice(i, 1);
      }
    };

    const loop = () => {
      const W = canvas.width, H = canvas.height;
      ctx.clearRect(0, 0, W, H);

      const home = getHome();
      const head = segs[0];

      const formRect = formRef.current?.getBoundingClientRect();
      const mouseOverForm = formRect
        ? mouse.x >= formRect.left - 20 && mouse.x <= formRect.right + 20
          && mouse.y >= formRect.top - 20 && mouse.y <= formRect.bottom + 20
        : false;

      // Rat respawn countdown
      if (ratHidden) {
        ratHiddenTimer--;
        if (ratHiddenTimer <= 0) { ratHidden = false; spawnRat(W, H); state = "hunt"; }
      }

      if (state === "hunt" && (Date.now() - lastMoveTime > 3000 || mouseOverForm)) state = "idle";

      if (state === "hunt" && !ratHidden) {
        const dx = mouse.x - head.x, dy = mouse.y - head.y;
        const d = Math.hypot(dx, dy);

        // CATCH detection
        if (d < 22 && !mouseOverForm) {
          triggerCatch(mouse.x, mouse.y);
        } else if (d > 25) {
          const speed = Math.min(5.5, d * 0.06);
          head.x += (dx / d) * speed;
          head.y += (dy / d) * speed;
        }
      } else {
        idleT += 0.009;
        const r = getBtn();
        const orx = r ? r.width / 2 + 22 : 100, ory = r ? r.height / 2 + 22 : 32;
        const tx = home.x + Math.cos(idleT) * orx;
        const ty = home.y + Math.sin(idleT) * ory;
        head.x += (tx - head.x) * 0.06;
        head.y += (ty - head.y) * 0.06;
      }

      for (let i = 1; i < N; i++) {
        const p = segs[i - 1], c = segs[i];
        const dx = c.x - p.x, dy = c.y - p.y, d = Math.hypot(dx, dy);
        if (d > SEG_LEN) { c.x = p.x + (dx / d) * SEG_LEN; c.y = p.y + (dy / d) * SEG_LEN; }
      }

      drawBody();
      drawScales();
      drawHead();
      drawParticles();
      drawFloatingTexts();
      drawFlash(W, H);
      drawScore(W);
      if (!ratHidden) drawRat(mouse.x, mouse.y, mouseOverForm);

      raf = requestAnimationFrame(loop);
    };
    loop();

    return () => {
      document.body.style.cursor = "";
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouse);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return <canvas ref={canvasRef} style={{ position: "fixed", inset: 0, zIndex: 15, pointerEvents: "none" }} />;
}

/* ── Floating background code cards ──────────────────── */
interface CodeLine { text: string; color: string; indent?: boolean }

function FloatingCodeCard({
  lines, pos, rot, floatDuration, floatDelay, entryFrom, scale = 1,
}: {
  lines: CodeLine[];
  pos: React.CSSProperties;
  rot: number;
  floatDuration: number;
  floatDelay: number;
  entryFrom: { x?: number; y?: number };
  scale?: number;
}) {
  return (
    <motion.div
      className="hidden lg:block"
      initial={{ opacity: 0, x: entryFrom.x ?? 0, y: entryFrom.y ?? 0 }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: 0.4 }}
      whileHover={{ scale: scale * 1.07, zIndex: 5 }}
      style={{ position: "fixed", zIndex: 1, pointerEvents: "auto", cursor: "default",
        transform: `scale(${scale})`, ...pos }}
    >
      <motion.div
        animate={{ y: [0, -12, 0], rotate: [rot, rot - 0.8, rot] }}
        transition={{ duration: floatDuration, repeat: Infinity, ease: "easeInOut", delay: floatDelay }}
        style={{ position: "relative", width: "210px" }}
      >
        {/* Back card — faint code lines */}
        <div style={{
          position: "absolute", inset: 0,
          transform: `rotate(${rot > 0 ? 4 : -4}deg) translate(${rot > 0 ? 7 : -7}px, 8px)`,
          background: "#181538", borderRadius: "16px", padding: "14px",
          border: "1px solid rgba(151,169,255,.07)",
          boxShadow: "0 8px 32px rgba(0,0,0,.3)",
        }}>
          <div style={{ display: "flex", gap: "5px", marginBottom: "10px" }}>
            {["#ff6e84","#fbbf24","#4ade80"].map(c => (
              <div key={c} style={{ width: "8px", height: "8px", borderRadius: "50%", background: c }} />
            ))}
          </div>
          {[0.8, 1, 0.55, 0.75, 0.5, 0.65].map((w, i) => (
            <div key={i} style={{
              height: "5px", borderRadius: "3px", marginBottom: "7px",
              background: i % 3 === 0 ? "rgba(200,154,248,.2)" : i % 3 === 1
                ? "rgba(151,169,255,.15)" : "rgba(248,172,255,.1)",
              width: `${w * 100}%`,
            }} />
          ))}
        </div>

        {/* Front card — actual code */}
        <div style={{
          position: "relative", background: "#13102e",
          borderRadius: "16px", padding: "14px 16px",
          border: "1px solid rgba(151,169,255,.22)",
          boxShadow: "0 20px 56px rgba(0,0,0,.55), 0 0 0 0.5px rgba(151,169,255,.08) inset",
        }}>
          <div style={{ display: "flex", gap: "5px", marginBottom: "10px" }}>
            {["#ff6e84","#fbbf24","#4ade80"].map(c => (
              <div key={c} style={{ width: "7px", height: "7px", borderRadius: "50%", background: c }} />
            ))}
          </div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: "11.5px", lineHeight: "1.75" }}>
            {lines.map((l, i) => (
              <div key={i} style={{
                color: l.color,
                paddingLeft: l.indent ? "14px" : "0",
                whiteSpace: "pre",
              }}>{l.text}</div>
            ))}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

const FLOATING_CARDS = [
  {
    pos: { bottom: "36px", left: "36px" },
    rot: -2, floatDuration: 6, floatDelay: 0, scale: 1,
    entryFrom: { x: -40, y: 0 },
    lines: [
      { text: "def ogrenci_giris(kod):", color: "#c99af8" },
      { text: "print(\"Hoşgeldiniz!\")", color: "#e7e2ff", indent: true },
      { text: "return True", color: "#8197ff", indent: true },
      { text: "# AI öğretmen aktif ✓", color: "#3d3a5c" },
    ],
  },
  {
    pos: { top: "48px", right: "44px" },
    rot: 3, floatDuration: 5, floatDelay: 1.2, scale: 0.9,
    entryFrom: { x: 40, y: -20 },
    lines: [
      { text: "nums = [1,2,3,4,5]", color: "#e7e2ff" },
      { text: "total = sum(nums)", color: "#e7e2ff" },
      { text: "print(total)  # 15", color: "#97a9ff" },
      { text: "# Listeler ✓", color: "#3d3a5c" },
    ],
  },
  {
    pos: { top: "52px", left: "40px" },
    rot: -3, floatDuration: 7, floatDelay: 0.8, scale: 0.85,
    entryFrom: { x: -30, y: -30 },
    lines: [
      { text: "if puan >= 90:", color: "#c99af8" },
      { text: "not = \"A\"", color: "#e7e2ff", indent: true },
      { text: "elif puan >= 70:", color: "#c99af8" },
      { text: "not = \"B\"", color: "#e7e2ff", indent: true },
      { text: "# Koşullar ✓", color: "#3d3a5c" },
    ],
  },
  {
    pos: { bottom: "48px", right: "40px" },
    rot: 2, floatDuration: 5.5, floatDelay: 2, scale: 0.88,
    entryFrom: { x: 40, y: 30 },
    lines: [
      { text: "class Ogrenci:", color: "#f8acff" },
      { text: "def __init__(self, ad):", color: "#c99af8", indent: true },
      { text: "self.ad = ad", color: "#e7e2ff", indent: true },
      { text: "# OOP ✓", color: "#3d3a5c" },
    ],
  },
];

/* ── Demo accounts with flip cards ───────────────────── */
const DEMOS = [
  {
    username: "ali", password: "ali123", label: "Ali", role: "Öğrenci", icon: "👨‍💻",
    code: [`x = "Python"`, `print(f"Merhaba,`, `  {x}!")`, `# Değişkenler ✓`],
  },
  {
    username: "ayse", password: "ayse123", label: "Ayşe", role: "Öğrenci", icon: "👩‍💻",
    code: [`for i in range(3):`, `  print("Öğren!")`, `# Döngüler ✓`],
  },
  {
    username: "ogretmen", password: "ogr123", label: "Öğretmen", role: "Eğitmen", icon: "👩‍🏫",
    code: [`def ders_ver(k):`, `  return k+"✓"`, `# Fonksiyon ✓`],
  },
];

function FlipCard({ acc, selected, onClick }: {
  acc: typeof DEMOS[0];
  selected: boolean;
  onClick: () => void;
}) {
  const [flipped, setFlipped] = useState(false);

  return (
    <div
      style={{ perspective: "700px" }}
      onMouseEnter={() => setFlipped(true)}
      onMouseLeave={() => setFlipped(false)}
    >
      <motion.div
        whileTap={{ scale: 0.96 }}
        onClick={onClick}
        style={{
          position: "relative",
          height: "110px",
          transformStyle: "preserve-3d",
          transition: "transform 0.55s cubic-bezier(.4,0,.2,1)",
          transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
          cursor: "pointer",
        }}
      >
        {/* Front */}
        <div style={{
          position: "absolute", inset: 0, backfaceVisibility: "hidden",
          borderRadius: "14px",
          background: selected ? "rgba(102,126,234,.22)" : "rgba(255,255,255,.05)",
          border: `1px solid ${selected ? "rgba(151,169,255,.5)" : "rgba(71,68,100,.3)"}`,
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", gap: "6px",
          boxShadow: selected ? "0 0 20px rgba(151,169,255,.15)" : "none",
        }}>
          <span style={{ fontSize: "24px" }}>{acc.icon}</span>
          <span style={{ fontSize: "13px", fontWeight: 700, color: selected ? "#97a9ff" : "#e7e2ff" }}>
            {acc.label}
          </span>
          <span style={{ fontSize: "11px", color: "#757294" }}>{acc.role}</span>
        </div>

        {/* Back */}
        <div style={{
          position: "absolute", inset: 0,
          backfaceVisibility: "hidden",
          transform: "rotateY(180deg)",
          borderRadius: "14px",
          background: "#0d0926",
          border: "1px solid rgba(151,169,255,.25)",
          padding: "12px 10px",
          overflow: "hidden",
        }}>
          <div style={{ display: "flex", gap: "5px", marginBottom: "8px" }}>
            {["#ff6e84","#fbbf24","#4ade80"].map(c => (
              <div key={c} style={{ width: "8px", height: "8px", borderRadius: "50%", background: c }} />
            ))}
          </div>
          <div style={{ fontFamily: "monospace", fontSize: "11px", lineHeight: "1.6", color: "#aca7cc" }}>
            {acc.code.map((line, i) => {
              const isComment = line.startsWith("#");
              const hasDef = line.includes("def ") || line.includes("for ") || line.includes("return");
              return (
                <div key={i} style={{
                  color: isComment ? "#474464" : hasDef ? "#c99af8" : "#e7e2ff",
                  paddingLeft: line.startsWith("  ") ? "12px" : "0",
                  whiteSpace: "pre",
                }}>
                  {line.trimStart()}
                </div>
              );
            })}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

/* ── Main login page ──────────────────────────────────── */
export default function LoginPage() {
  const canvasRef = useParticleCanvas();
  const btnRef = useRef<HTMLButtonElement>(null);
  const formRef = useRef<HTMLDivElement>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [focused, setFocused] = useState<"user" | "pass" | null>(null);
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  async function handleSubmit(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!username || !password) return;
    setLoading(true);
    try {
      const data = await login(username, password);
      setAuth(data.access_token, data.username, data.name, data.role);
      toast.success(`Hoş geldin, ${data.name}! 🎉`);
      navigate(data.role === "teacher" ? "/teacher" : "/student");
    } catch {
      toast.error("Kullanıcı adı veya şifre hatalı");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = (isFocused: boolean): React.CSSProperties => ({
    width: "100%", padding: "13px 16px 13px 44px",
    borderRadius: "12px", fontSize: "14px", outline: "none",
    transition: "all .2s",
    background: "rgba(255,255,255,.06)",
    border: `1px solid ${isFocused ? "rgba(151,169,255,.55)" : "rgba(71,68,100,.35)"}`,
    color: "#e7e2ff",
    boxShadow: isFocused
      ? "0 0 0 3px rgba(151,169,255,.13), inset 0 1px 0 rgba(255,255,255,.06)"
      : "inset 0 1px 0 rgba(255,255,255,.03)",
  });

  return (
    <div style={{ minHeight: "100vh", background: "#07051a", position: "relative", overflow: "hidden",
      display: "flex", alignItems: "center", justifyContent: "center" }}>

      {/* Particle canvas */}
      <canvas ref={canvasRef} style={{ position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none" }} />

      {/* Snake */}
      <SnakeCanvas btnRef={btnRef} formRef={formRef} />

      {/* Ambient blobs */}
      <div style={{ position: "fixed", top: "-20%", left: "-10%", width: "60%", height: "60%",
        borderRadius: "50%", background: "radial-gradient(#5c6bc0,transparent 70%)",
        filter: "blur(80px)", opacity: 0.18, zIndex: 0, pointerEvents: "none" }} />
      <div style={{ position: "fixed", bottom: "-20%", right: "-10%", width: "60%", height: "60%",
        borderRadius: "50%", background: "radial-gradient(#9c27b0,transparent 70%)",
        filter: "blur(80px)", opacity: 0.18, zIndex: 0, pointerEvents: "none" }} />

      {/* Floating code cards — 4 corners */}
      {FLOATING_CARDS.map((card, i) => (
        <FloatingCodeCard key={i} {...card} />
      ))}

      {/* ── Main card ── */}
      <motion.div
        ref={formRef}
        initial={{ opacity: 0, y: 36, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        style={{ position: "relative", zIndex: 10, width: "100%", maxWidth: "440px",
          margin: "0 16px", display: "flex", flexDirection: "column" }}
      >
        {/* Gradient border */}
        <div style={{
          position: "absolute", inset: "-1px", borderRadius: "28px",
          background: "linear-gradient(135deg,rgba(102,126,234,.6),rgba(118,75,162,.4),rgba(240,147,251,.6))",
          filter: "blur(0.5px)", zIndex: -1,
        }} />

        <div style={{
          background: "rgba(10,8,30,.92)", backdropFilter: "blur(32px)",
          borderRadius: "28px", overflow: "hidden",
        }}>
          {/* Top shimmer line */}
          <div style={{
            height: "1px", width: "100%",
            background: "linear-gradient(90deg,transparent 0%,rgba(151,169,255,.55) 50%,transparent 100%)",
          }} />

          <div style={{ padding: "36px 36px 32px" }}>
            {/* Logo */}
            <div style={{ display: "flex", justifyContent: "center", marginBottom: "24px" }}>
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
                style={{ position: "relative" }}
              >
                <div style={{
                  position: "absolute", inset: "-8px", borderRadius: "50%",
                  background: "linear-gradient(135deg,#667eea,#764ba2,#f093fb)",
                  filter: "blur(14px)", opacity: 0.5,
                }} />
                <div style={{
                  position: "relative", width: "90px", height: "90px", borderRadius: "50%",
                  background: "linear-gradient(135deg,#667eea,#764ba2,#f093fb)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  boxShadow: "0 0 36px rgba(151,169,255,.45), inset 0 1px 0 rgba(255,255,255,.25)",
                }}>
                  <img
                    src="https://kocaelisaglik.edu.tr/wp-content/uploads/2020/11/logo2-nospace-1.png"
                    alt="KOSTÜ"
                    style={{
                      width: "70px", height: "70px",
                      objectFit: "contain",
                      filter: "brightness(0) invert(1)",
                    }}
                  />
                </div>
              </motion.div>
            </div>

            {/* Title */}
            <div style={{ textAlign: "center", marginBottom: "28px" }}>
              <h1 style={{
                fontSize: "26px", fontWeight: 900, letterSpacing: "-0.5px", margin: "0 0 6px",
                background: "linear-gradient(135deg,#e7e2ff 0%,#97a9ff 50%,#f8acff 100%)",
                WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
              }}>
                Sanal Öğretmen Asistanı
              </h1>
              <p style={{ color: "#aca7cc", fontSize: "13px", margin: 0, fontWeight: 500 }}>
                Yapay Zeka Destekli Python Öğrenim Rehberi
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Username */}
              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 700,
                  textTransform: "uppercase", letterSpacing: "0.1em", color: "#aca7cc", marginBottom: "8px" }}>
                  Kullanıcı Adı
                </label>
                <div style={{ position: "relative" }}>
                  <span className="material-symbols-outlined" style={{
                    position: "absolute", left: "13px", top: "50%", transform: "translateY(-50%)",
                    fontSize: "18px", color: focused === "user" ? "#97a9ff" : "rgba(172,167,204,.4)",
                    transition: "color .2s", userSelect: "none",
                  }}>person</span>
                  <input
                    type="text" value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    onFocus={() => setFocused("user")} onBlur={() => setFocused(null)}
                    placeholder="kullanici_adi" autoComplete="username"
                    style={inputStyle(focused === "user")}
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 700,
                  textTransform: "uppercase", letterSpacing: "0.1em", color: "#aca7cc", marginBottom: "8px" }}>
                  Şifre
                </label>
                <div style={{ position: "relative" }}>
                  <span className="material-symbols-outlined" style={{
                    position: "absolute", left: "13px", top: "50%", transform: "translateY(-50%)",
                    fontSize: "18px", color: focused === "pass" ? "#97a9ff" : "rgba(172,167,204,.4)",
                    transition: "color .2s", userSelect: "none",
                  }}>lock</span>
                  <input
                    type="password" value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setFocused("pass")} onBlur={() => setFocused(null)}
                    placeholder="••••••••" autoComplete="current-password"
                    style={inputStyle(focused === "pass")}
                  />
                </div>
              </div>

              {/* Submit */}
              <motion.button
                ref={btnRef}
                type="submit" disabled={loading}
                whileHover={{ scale: 1.015 }} whileTap={{ scale: 0.975 }}
                style={{
                  position: "relative", width: "100%", padding: "14px",
                  borderRadius: "12px", fontWeight: 700, fontSize: "14px",
                  color: "white", border: "none", cursor: "pointer", overflow: "hidden",
                  background: "linear-gradient(135deg,#667eea,#764ba2,#f093fb)",
                  boxShadow: "0 4px 24px rgba(102,126,234,.35)",
                  opacity: loading ? 0.65 : 1,
                }}
              >
                <div className="shimmer-bar" style={{ position: "absolute", inset: 0, opacity: 0.25 }} />
                <span style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                  {loading ? (
                    <>
                      <span style={{ width: "16px", height: "16px", borderRadius: "50%",
                        border: "2px solid rgba(255,255,255,.4)", borderTopColor: "white",
                        display: "inline-block", animation: "spin 0.8s linear infinite" }} />
                      Giriş yapılıyor…
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined"
                        style={{ fontSize: "18px", fontVariationSettings: "'FILL' 1" }}>login</span>
                      Giriş Yap
                    </>
                  )}
                </span>
              </motion.button>
            </form>

            {/* Divider */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px", margin: "24px 0 16px" }}>
              <div style={{ flex: 1, height: "1px",
                background: "linear-gradient(to right,transparent,rgba(71,68,100,.45))" }} />
              <span style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.12em",
                color: "#474464", fontWeight: 600 }}>Demo hesapları</span>
              <div style={{ flex: 1, height: "1px",
                background: "linear-gradient(to left,transparent,rgba(71,68,100,.45))" }} />
            </div>

            {/* Flip cards */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px" }}>
              {DEMOS.map((acc) => (
                <FlipCard
                  key={acc.username}
                  acc={acc}
                  selected={username === acc.username}
                  onClick={() => { setUsername(acc.username); setPassword(acc.password); }}
                />
              ))}
            </div>
            <p style={{ textAlign: "center", fontSize: "11px", color: "rgba(117,114,148,.5)",
              marginTop: "10px", marginBottom: 0 }}>
              Üzerine gelin → kodu görün · Tıklayın → formu doldurun
            </p>
          </div>
        </div>

        <p style={{ textAlign: "center", fontSize: "11px", color: "rgba(172,167,204,.3)",
          marginTop: "20px" }}>
          © 2024 Sanal Öğretmen Asistanı · Tüm hakları saklıdır
        </p>
      </motion.div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        input::placeholder { color: rgba(117,114,148,.5); }
      `}</style>
    </div>
  );
}
