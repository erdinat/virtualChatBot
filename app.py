"""
🎓 Sanal Öğretmen Asistanı – Ana Uygulama

Python Programlama Eğitiminde RAG Destekli ve Adaptif Öğrenme Tabanlı
Sanal Öğretmen Asistanı.

Çalıştırmak için:
    streamlit run app.py
"""

import yaml
import streamlit as st
import streamlit_authenticator as stauth
from pathlib import Path

from config.settings import CURRICULUM
from modules.pedagogy.socratic import SocraticManager
from modules.drl.policy import RuleBasedPolicy
from modules.storage import (
    load_student_data,
    save_student_data,
    load_all_students,
    append_chat_log,
    load_chat_log,
)


# ===== Sayfa Konfigürasyonu =====
st.set_page_config(
    page_title="Sanal Öğretmen Asistanı",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== Özel CSS & Animasyonlar =====
_CSS = """
<style>
/* ── Stitch Design System ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

:root {
    --surface:            #0d0a27;
    --surface-container:  #181538;
    --surface-high:       #1e1a41;
    --surface-highest:    #24204a;
    --surface-bright:     #2a2653;
    --on-surface:         #e7e2ff;
    --on-surface-var:     #aca7cc;
    --primary:            #97a9ff;
    --primary-g1:         #667eea;
    --primary-g2:         #764ba2;
    --primary-g3:         #f093fb;
    --outline-var:        #474464;
    --error:              #ff6e84;
    --success:            #4ade80;
    --secondary-cont:     #5c3187;
    --on-secondary-cont:  #e3c4ff;
}

* { font-family: 'Inter', sans-serif !important; }

/* ── Animasyonlar ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-10px); }
}
@keyframes shimmer-bar {
    0%   { background-position: 200% center; }
    100% { background-position: -200% center; }
}
@keyframes glow-pulse {
    0%, 100% { opacity: .12; transform: scale(1); }
    50%       { opacity: .22; transform: scale(1.05); }
}
@keyframes spin-slow { to { transform: rotate(360deg); } }

/* ── Global ── */
body, .stApp { background-color: var(--surface) !important; }
.main .block-container { animation: fadeInUp .4s ease; max-width: 1200px; }

/* ── Gradient text util ── */
.g-text {
    background: linear-gradient(135deg, var(--primary-g1), var(--primary-g2), var(--primary-g3));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ── Başlıklar ── */
h1 {
    background: linear-gradient(135deg, var(--primary-g1), var(--primary-g3));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800 !important;
    letter-spacing: -.5px;
}
h2, h3 { color: var(--on-surface) !important; font-weight: 700 !important; }

/* ── Glass card ── */
.glass {
    background: rgba(102,126,234,.08);
    backdrop-filter: blur(20px);
    border-top: 1px solid rgba(151,169,255,.1);
    border-left: 1px solid rgba(151,169,255,.1);
    border-radius: 20px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--surface-container) !important;
    border-right: 1px solid rgba(255,255,255,.05) !important;
}
[data-testid="stSidebar"] * { color: var(--on-surface) !important; }
[data-testid="stSidebar"] hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--outline-var), transparent);
    margin: .75rem 0;
}
[data-testid="stSidebar"] .stSuccess > div,
[data-testid="stSidebar"] .stInfo > div {
    border-radius: 12px !important;
}

/* ── Butonlar ── */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    transition: all .25s ease !important;
    border: none !important;
    letter-spacing: .3px;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary-g1), var(--primary-g2), var(--primary-g3)) !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(102,126,234,.3) !important;
}
.stButton > button:hover {
    transform: translateY(-3px) scale(1.01) !important;
    box-shadow: 0 10px 28px rgba(102,126,234,.5) !important;
}
.stButton > button:active { transform: scale(.97) !important; }

/* ── Chat mesajları ── */
[data-testid="stChatMessage"] {
    animation: fadeInUp .3s ease;
    border-radius: 20px !important;
    margin: .5rem 0;
    transition: transform .2s ease, box-shadow .2s ease;
    background: rgba(102,126,234,.06) !important;
    border: 1px solid rgba(151,169,255,.08) !important;
}
[data-testid="stChatMessage"]:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 20px rgba(102,126,234,.12);
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
    background: var(--surface-container) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,.08) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    border: none !important;
    color: var(--on-surface) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: rgba(102,126,234,.5) !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,.15) !important;
}

/* ── Metric kartları (öğretmen) ── */
[data-testid="stMetric"] {
    background: rgba(102,126,234,.07);
    border: 1px solid rgba(151,169,255,.12);
    border-top: 1px solid rgba(151,169,255,.15);
    border-left: 1px solid rgba(151,169,255,.15);
    border-radius: 16px;
    padding: 1.2rem !important;
    transition: all .3s ease;
    animation: fadeInUp .5s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    border-color: rgba(102,126,234,.45);
    box-shadow: 0 12px 32px rgba(102,126,234,.2);
}
[data-testid="stMetricValue"] { color: white !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: var(--on-surface-var) !important; font-weight: 700 !important; font-size: .7rem !important; letter-spacing: .1em; text-transform: uppercase; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 4px;
    border-bottom: 1px solid rgba(255,255,255,.05) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0 !important;
    font-weight: 600 !important;
    color: var(--on-surface-var) !important;
    transition: all .2s ease !important;
    padding: .75rem 1.25rem !important;
}
.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom: 2px solid var(--primary) !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden;
    border: 1px solid rgba(151,169,255,.1) !important;
    box-shadow: 0 4px 24px rgba(0,0,0,.2);
    animation: fadeInUp .5s ease;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(102,126,234,.04) !important;
    border-radius: 14px !important;
    border: 2px dashed rgba(151,169,255,.3) !important;
    transition: all .3s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(151,169,255,.7) !important;
    background: rgba(102,126,234,.08) !important;
}

/* ── Alert ── */
[data-testid="stAlert"] {
    border-radius: 14px !important;
    animation: fadeInUp .35s ease;
    border: 1px solid rgba(255,255,255,.06) !important;
}

/* ══════════════════════════════════════════════
   LOGIN PAGE (Stitch design)
═══════════════════════════════════════════════ */
.sta-glow {
    position: fixed;
    border-radius: 9999px;
    filter: blur(80px);
    opacity: .14;
    pointer-events: none;
    z-index: 0;
    animation: glow-pulse 6s ease-in-out infinite;
}
.sta-glow-1 { width: 55vw; height: 55vw; top: -15%; left: -15%; background: var(--primary-g1); }
.sta-glow-2 { width: 45vw; height: 45vw; bottom: -15%; right: -15%; background: var(--primary-g3); animation-delay: -3s; }
.sta-glow-3 { width: 35vw; height: 35vw; top: 50%; left: 50%; transform: translate(-50%,-50%); background: var(--primary-g2); animation-delay: -1.5s; }

.sta-login-wrap {
    position: relative;
    z-index: 1;
    padding: 1.5rem 0;
}
.sta-logo-wrap {
    width: 88px; height: 88px;
    background: var(--surface-high);
    border-radius: 9999px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 1.5rem;
    border: 1px solid rgba(71,68,100,.3);
    box-shadow: 0 8px 32px rgba(0,0,0,.3);
    font-size: 2.6rem;
    animation: float 3s ease-in-out infinite;
}
.sta-title {
    text-align: center;
    font-size: 1.9rem;
    font-weight: 900;
    background: linear-gradient(135deg, var(--primary-g1), var(--primary-g2), var(--primary-g3));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -.5px;
    margin: 0;
    animation: fadeInUp .5s ease;
}
.sta-sub {
    text-align: center;
    color: var(--on-surface-var);
    font-size: .82rem;
    font-weight: 500;
    letter-spacing: .08em;
    text-transform: uppercase;
    margin: .4rem 0 0;
    animation: fadeInUp .6s ease;
}
.sta-card {
    background: rgba(102,126,234,.08);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(172,167,204,.1);
    border-radius: 24px;
    padding: 2.2rem 2.5rem 2rem;
    box-shadow: 0 24px 64px rgba(0,0,0,.35);
    margin-top: 1.5rem;
    animation: fadeInUp .7s ease;
}
.sta-demo {
    display: flex; align-items: center; justify-content: center; gap: .6rem;
    flex-wrap: wrap;
    background: rgba(92,49,135,.2);
    border: 1px solid rgba(92,49,135,.35);
    border-radius: 9999px;
    padding: .55rem 1.2rem;
    margin-top: 1.2rem;
    font-size: .78rem;
    color: var(--on-secondary-cont, #e3c4ff);
    animation: fadeInUp .9s ease;
}
.sta-demo code {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700;
    color: var(--primary);
    background: rgba(151,169,255,.12);
    padding: .15rem .4rem;
    border-radius: 6px;
    font-size: .76rem;
}
.sta-sep { width: 1px; height: 14px; background: rgba(92,49,135,.5); }

/* ══════════════════════════════════════════════
   MASTERY BARS (Stitch custom HTML bars)
═══════════════════════════════════════════════ */
.sta-bar-wrap { margin-bottom: .9rem; }
.sta-bar-labels {
    display: flex; justify-content: space-between;
    margin-bottom: 5px;
}
.sta-bar-label { font-size: .7rem; color: var(--on-surface-var); font-weight: 500; }
.sta-bar-pct   { font-size: .7rem; color: var(--primary); font-weight: 800; }
.sta-bar-track {
    height: 6px;
    background: var(--surface-highest);
    border-radius: 99px;
    overflow: hidden;
}
.sta-bar-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg,
        var(--primary-g1) 0%, var(--primary-g2) 40%,
        var(--primary-g3) 70%, var(--primary-g1) 100%);
    background-size: 300% auto;
    animation: shimmer-bar 3s linear infinite;
    transition: width 1s cubic-bezier(.4,0,.2,1);
}

/* ══════════════════════════════════════════════
   ÖNERI CHIP
═══════════════════════════════════════════════ */
.sta-chip {
    background: rgba(92,49,135,.2);
    border: 1px solid rgba(92,49,135,.4);
    border-radius: 14px;
    padding: .9rem 1rem;
    margin-top: .5rem;
}
.sta-chip-label {
    font-size: .6rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .12em;
    color: var(--on-secondary-cont);
    margin-bottom: .35rem;
}
.sta-chip-text {
    font-size: .82rem;
    font-weight: 600;
    color: var(--on-surface);
}

/* ══════════════════════════════════════════════
   CHAT MESAJ STİLLERİ (kullanıcı vs asistan)
═══════════════════════════════════════════════ */
/* Asistan mesajı: koyu kart, sol yuvarlak */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: rgba(18,15,47,.92) !important;
    border: 1px solid rgba(151,169,255,.1) !important;
    border-radius: 4px 20px 20px 20px !important;
    padding: 1rem 1.2rem !important;
}
/* Kullanıcı mesajı: mor/mavi, sağ yuvarlak */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: rgba(102,126,234,.22) !important;
    border: 1px solid rgba(102,126,234,.18) !important;
    border-radius: 20px 4px 20px 20px !important;
    padding: 1rem 1.2rem !important;
    margin-left: 10% !important;
}
/* Avatar ikonları */
[data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, #667eea, #f093fb) !important;
    border-radius: 50% !important;
}
[data-testid="chatAvatarIcon-user"] {
    background: rgba(102,126,234,.35) !important;
    border-radius: 50% !important;
}

/* ── Chat header (Aktif Öğrenme) pulse ── */
@keyframes dot-pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: .4; }
}
.sta-pulse-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #4ade80;
    animation: dot-pulse 2s ease-in-out infinite;
    margin-right: 5px;
}

/* ══════════════════════════════════════════════
   ÖĞRETMEN PANELİ
═══════════════════════════════════════════════ */

/* Teacher metric card (Stitch glass) */
.sta-metric-card {
    background: rgba(102,126,234,.07);
    border-top: 1px solid rgba(151,169,255,.12);
    border-left: 1px solid rgba(151,169,255,.12);
    border-right: 1px solid rgba(0,0,0,.2);
    border-bottom: 1px solid rgba(0,0,0,.2);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: transform .25s ease, box-shadow .25s ease;
    animation: fadeInUp .4s ease;
}
.sta-metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(102,126,234,.2);
}
.sta-metric-card-icon {
    position: absolute;
    top: .6rem; right: .8rem;
    font-size: 2.8rem;
    opacity: .08;
}
.sta-metric-label {
    font-size: .6rem;
    font-weight: 800;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: #aca7cc;
    margin: 0 0 .3rem;
}
.sta-metric-value {
    font-size: 2rem;
    font-weight: 900;
    color: white;
    margin: 0;
    letter-spacing: -.5px;
}
.sta-metric-delta-up   { font-size: .8rem; font-weight: 700; color: #4ade80; }
.sta-metric-delta-down { font-size: .8rem; font-weight: 700; color: #fb7185; }
.sta-metric-sub {
    font-size: .65rem;
    color: #757294;
    font-style: italic;
    margin: .3rem 0 0;
}

/* Teacher welcome header */
.sta-teacher-header { margin-bottom: 1.8rem; animation: fadeInUp .4s ease; }
.sta-teacher-header h1 { font-size: 2.8rem !important; font-weight: 900 !important; color: white !important; margin: 0 !important; }
.sta-teacher-header p  { color: var(--on-surface-var); font-size: 1.05rem; margin: .4rem 0 0; }

/* Teacher table (Stitch style) */
.sta-table-wrap {
    background: rgba(102,126,234,.06);
    border: 1px solid rgba(151,169,255,.1);
    border-radius: 16px;
    overflow: hidden;
    animation: fadeInUp .5s ease;
}
.sta-table-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.1rem 1.4rem;
    border-bottom: 1px solid rgba(255,255,255,.05);
}
.sta-table-title { font-size: 1.15rem; font-weight: 800; color: white; margin: 0; }
.sta-student-row {
    display: flex;
    align-items: center;
    padding: .9rem 1.4rem;
    border-bottom: 1px solid rgba(255,255,255,.04);
    gap: 1rem;
    transition: background .2s;
}
.sta-student-row:hover { background: rgba(255,255,255,.03); }
.sta-student-row:last-child { border-bottom: none; }
.sta-avatar {
    width: 42px; height: 42px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #f093fb);
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1rem; color: white;
    flex-shrink: 0;
}
.sta-student-name { font-weight: 700; font-size: .88rem; color: white; margin: 0; }
.sta-student-sub  { font-size: .7rem; color: #757294; margin: .1rem 0 0; }
.sta-mini-bar-track {
    height: 5px; width: 120px;
    background: rgba(255,255,255,.08);
    border-radius: 99px;
    overflow: hidden;
}
.sta-mini-bar-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #667eea, #f093fb);
}
.sta-score-badge {
    padding: .25rem .7rem;
    border-radius: 9999px;
    font-size: .78rem;
    font-weight: 800;
}
.sta-score-green { background: rgba(74,222,128,.12); color: #4ade80; border: 1px solid rgba(74,222,128,.25); }
.sta-score-yellow { background: rgba(251,191,36,.12); color: #fbbf24; border: 1px solid rgba(251,191,36,.25); }
.sta-score-red { background: rgba(248,113,113,.12); color: #f87171; border: 1px solid rgba(248,113,113,.25); }

/* Log entries */
.sta-log-entry {
    display: flex;
    gap: .8rem;
    padding: .8rem 1rem;
    background: rgba(255,255,255,.03);
    border-radius: 10px;
    border-left: 2px solid #667eea;
    margin-bottom: .5rem;
    animation: fadeInUp .3s ease;
}
.sta-log-entry.assistant { border-left-color: #f093fb; }
.sta-log-ts { font-size: .65rem; color: #757294; white-space: nowrap; }
.sta-log-user { font-size: .8rem; font-weight: 700; color: #e7e2ff; margin: 0 0 .2rem; }
.sta-log-text { font-size: .78rem; color: #aca7cc; font-style: italic; margin: 0; }

/* ══════════════════════════════════════════════
   GİRİŞ SAYFASI — STREAMLİT FORM OVERRİDES
   (Stitch tasarımını yansıtır)
═══════════════════════════════════════════════ */

/* ── Tüm sayfa ── */
.stApp { background-color: #0d0a27 !important; }
.stApp > header, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
footer { visibility: hidden !important; }
.main .block-container { padding-top: 2.5rem !important; padding-bottom: 2rem !important; }

/* ── Streamlit form = glassmorphism kart ── */
[data-testid="stForm"] {
    background: rgba(102, 126, 234, 0.1) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border: 1px solid rgba(172, 167, 204, 0.15) !important;
    border-radius: 24px !important;
    padding: 2rem 2.5rem !important;
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.45) !important;
    margin-top: .8rem !important;
}

/* ── Input label ── */
[data-testid="stTextInput"] label p {
    font-size: .65rem !important;
    font-weight: 800 !important;
    letter-spacing: .14em !important;
    text-transform: uppercase !important;
    color: #aca7cc !important;
    margin-bottom: .3rem !important;
}

/* ── Input wrapper (Streamlit'in kendi border'ı) ── */
[data-testid="stTextInput"] > div > div {
    background-color: rgba(0, 0, 0, 0.55) !important;
    border: 1px solid rgba(71, 68, 100, 0.6) !important;
    border-radius: 9999px !important;
    padding: 0 !important;
    transition: border-color .25s, box-shadow .25s;
}
[data-testid="stTextInput"] > div > div:focus-within {
    border-color: rgba(151, 169, 255, 0.7) !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
}

/* ── Input içi (transparent — wrapper'dan renk alıyor) ── */
[data-testid="stTextInput"] input {
    background: transparent !important;
    border: none !important;
    border-radius: 9999px !important;
    color: #e7e2ff !important;
    padding: .75rem 1.2rem !important;
    font-size: .9rem !important;
    box-shadow: none !important;
}
[data-testid="stTextInput"] input::placeholder { color: rgba(172, 167, 204, 0.45) !important; }
[data-testid="stTextInput"] input:focus { outline: none !important; box-shadow: none !important; }

/* ── Giriş butonu — gradient pill ── */
[data-testid="stFormSubmitButton"] button,
[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important;
    border: none !important;
    border-radius: 9999px !important;
    width: 100% !important;
    padding: .85rem 2rem !important;
    font-size: .95rem !important;
    font-weight: 700 !important;
    color: white !important;
    box-shadow: 0 6px 24px rgba(102, 126, 234, 0.4) !important;
    transition: transform .2s ease, box-shadow .2s ease !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 12px 36px rgba(102, 126, 234, 0.6) !important;
}
[data-testid="stFormSubmitButton"] button:active { transform: scale(.97) !important; }

/* Kod dekorasyonu */
.sta-code-deco {
    position: fixed;
    bottom: 8%;
    left: 4%;
    z-index: 0;
    pointer-events: none;
    opacity: .38;
}
.sta-code-back {
    background: #181538;
    border-radius: 18px;
    padding: 1.1rem 1.4rem;
    border: 1px solid rgba(71,68,100,.2);
    transform: rotate(3deg);
    position: absolute;
    width: 230px;
    top: 0; left: 0;
}
.sta-code-back-dots { display: flex; gap: 5px; margin-bottom: 10px; }
.sta-code-back-dots span {
    width: 8px; height: 8px; border-radius: 50%;
    display: inline-block;
}
.sta-code-front {
    background: #1e1a41;
    border-radius: 18px;
    padding: 1.1rem 1.4rem;
    border: 1px solid rgba(71,68,100,.25);
    transform: rotate(-3deg) translate(18px, 18px);
    position: relative;
    width: 230px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: .7rem;
    line-height: 1.7;
    box-shadow: 0 8px 32px rgba(0,0,0,.4);
}
</style>
"""


def _inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)

# ===== Kimlik Doğrulama Konfigürasyonu =====
_CONFIG_PATH = Path(__file__).parent / "config" / "users.yaml"
with open(_CONFIG_PATH, encoding="utf-8") as f:
    _AUTH_CONFIG = yaml.safe_load(f)

_AUTHENTICATOR = stauth.Authenticate(
    _AUTH_CONFIG["credentials"],
    _AUTH_CONFIG["cookie"]["name"],
    _AUTH_CONFIG["cookie"]["key"],
    _AUTH_CONFIG["cookie"]["expiry_days"],
)


# ===== Konu Anahtar Kelime Tablosu =====
_TOPIC_KEYWORDS = {
    1: ["değişken", "veri tipi", "string", "integer", "float", "bool", "variable", "str(", "int(", "type("],
    2: ["operatör", "operator", "ifade", "expression", "aritmetik", "karşılaştır", "modulo", " % ", " ** "],
    3: ["if", "elif", "else", "koşul", "condition", "dallanma", "ternary"],
    4: ["for", "while", "döngü", "loop", "range(", "iterate", "break", "continue"],
    5: ["liste", "list", "tuple", "append", "extend", "index", "slice", "pop("],
    6: ["sözlük", "dict", "küme", "set", "key", "value", "items(", "keys(", "values("],
    7: ["fonksiyon", "function", "def ", "return", "parametre", "argument", "lambda", "*args", "**kwargs"],
    8: ["dosya", "file", "open(", "read(", "write(", "csv", "with open", "readline"],
    9: ["hata", "error", "exception", "try:", "except", "finally", "raise", "traceback"],
    10: ["sınıf", "class ", "nesne", "object", "oop", "inheritance", "miras", "__init__", "self.", "super("],
}

_UNDERSTOOD_PHRASES = [
    "anladım", "tamam anladım", "evet anladım", "anladım teşekkürler",
    "teşekkürler", "teşekkür ederim", "çok teşekkürler", "sağ ol",
]

_SIMPLIFY_PHRASES = [
    "anlamadım", "anlayamadım", "anlamıyorum", "anlamadım diyorum",
    "basitçe anlat", "daha basit anlat", "sadece anlat", "kısaca anlat",
    "ne demek", "ne anlama geliyor",
]

_CURRICULUM_NAV_PHRASES = [
    "diğer konu", "sıradaki konu", "sonraki konu", "ne öğren",
    "müfredat", "konu listesi", "hangi konular", "konular neler",
    "sıra nedir", "ne var", "neleri öğreneceğim", "program nedir",
]


# ===== Yardımcı Fonksiyonlar =====

def is_understood(text: str) -> bool:
    t = text.strip().lower()
    return any(t == p or t.startswith(p + " ") or t.startswith(p + ",") for p in _UNDERSTOOD_PHRASES)


def is_simplify_request(text: str) -> bool:
    t = text.strip().lower()
    return any(phrase in t for phrase in _SIMPLIFY_PHRASES)


def is_curriculum_query(text: str) -> bool:
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in _CURRICULUM_NAV_PHRASES)


def detect_topic(query: str) -> int | None:
    query_lower = query.lower()
    for topic_id, keywords in _TOPIC_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            return topic_id
    return None


def build_curriculum_response(current_topic_id: int | None) -> str:
    lines = ["📚 **Python Programlama Müfredatı:**\n"]
    for topic in CURRICULUM:
        if topic["id"] == current_topic_id:
            marker = "▶️"
        elif current_topic_id and topic["id"] < current_topic_id:
            marker = "✅"
        else:
            marker = "⬜"
        stars = "⭐" * topic["difficulty"]
        lines.append(f"{marker} **{topic['id']}. {topic['name']}** {stars}")

    if current_topic_id:
        next_topic = next((t for t in CURRICULUM if t["id"] == current_topic_id + 1), None)
        if next_topic:
            lines.append(f"\n➡️ Sıradaki konu: **{next_topic['name']}**")
    else:
        lines.append("\n➡️ İstediğin konuya geçebiliriz. Hangisiyle başlamak istersin?")
    return "\n".join(lines)


def get_level_context(interaction_history: list, student_mastery: dict) -> str:
    total = len(interaction_history)
    if total == 0:
        return "Seviye: Yeni başlayan (henüz etkileşim yok). Çok basit örnekler kullan."

    studied = {k: v for k, v in student_mastery.items() if v > 0}
    avg_score = sum(studied.values()) / len(studied) if studied else 0.0

    if avg_score < 0.4:
        level = "başlangıç (acemi)"
        note = "En temel örnekleri kullan. OOP, sınıf (class), nesne (object) gibi ileri kavramlardan bahsetme."
    elif avg_score < 0.65:
        level = "orta başlangıç"
        note = "Temel ve orta düzey örnekler kullan."
    else:
        level = "orta-ileri"
        note = "Orta ve ileri düzey örnekler kullanabilirsin."

    return f"Öğrenci seviyesi: {level} ({total} etkileşim, ortalama skor: {avg_score:.0%}). {note}"


# ===== Öğrenci Oturum Yönetimi =====

def init_student_session(username: str):
    """Öğrencinin session state'ini başlatır; diskteki veriyi yükler."""
    # Sadece ilk kez (veya kullanıcı değişince) başlat
    if st.session_state.get("_loaded_user") != username:
        saved = load_student_data(username)
        st.session_state["interaction_history"] = saved["interaction_history"]
        st.session_state["student_mastery"]     = saved["student_mastery"]
        st.session_state["messages"]            = []
        st.session_state["current_topic"]       = None
        st.session_state["pending_topic_id"]    = None
        st.session_state["awaiting_feedback"]   = False
        st.session_state["socratic_manager"]    = SocraticManager()
        st.session_state["drl_policy"]          = RuleBasedPolicy()
        st.session_state["rag_chain"]           = None
        st.session_state["vector_store"]        = None
        st.session_state["pdfs_loaded"]         = False
        st.session_state["_loaded_user"]        = username

    # Vektör veritabanı diskte varsa otomatik yükle
    if not st.session_state.rag_chain:
        try:
            from modules.rag import load_vector_store, build_rag_chain
            vs = load_vector_store()
            if vs is not None:
                st.session_state.vector_store = vs
                st.session_state.rag_chain = build_rag_chain(vector_store=vs)
                st.session_state.pdfs_loaded = True
        except Exception:
            pass


def _save_current_student():
    """Mevcut öğrencinin verilerini diske kaydeder."""
    username = st.session_state.get("username")
    if username:
        save_student_data(
            username,
            st.session_state.interaction_history,
            st.session_state.student_mastery,
        )


def _record_feedback(correct: bool):
    """Kullanıcı feedbackini kaydeder, mastery günceller, diske yazar."""
    from modules.dkt.predict import predict_mastery

    topic_id = st.session_state.pending_topic_id
    if topic_id is not None:
        st.session_state.interaction_history.append(
            {"skill_id": topic_id, "correct": correct}
        )

    st.session_state.student_mastery = predict_mastery(
        interaction_history=st.session_state.interaction_history
    )
    st.session_state.awaiting_feedback = False
    st.session_state.pending_topic_id = None
    _save_current_student()
    st.rerun()


# ===== PDF İşleme =====

def process_uploaded_pdfs(uploaded_files):
    """Yüklenen PDF'leri işle ve vektör veritabanı oluştur."""
    save_dir = Path("data/raw_pdfs")
    save_dir.mkdir(parents=True, exist_ok=True)

    for file in uploaded_files:
        with open(save_dir / file.name, "wb") as f:
            f.write(file.getbuffer())
        st.sidebar.write(f"  📄 {file.name}")

    try:
        from modules.rag import (
            load_all_pdfs, split_documents,
            get_embedding_model, create_vector_store, build_rag_chain,
        )
        documents = load_all_pdfs(save_dir)
        chunks = split_documents(documents)
        embedding_model = get_embedding_model()
        vector_store = create_vector_store(chunks, embedding_model)
        st.session_state.vector_store = vector_store
        st.session_state.rag_chain = build_rag_chain(vector_store=vector_store)
        st.session_state.pdfs_loaded = True
        st.sidebar.success(f"✅ {len(uploaded_files)} PDF işlendi, {len(chunks)} parça oluşturuldu!")
    except Exception as e:
        st.sidebar.error(f"❌ Hata: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# ÖĞRENCİ PANELİ
# ═══════════════════════════════════════════════════════════════════════════════

def render_student_sidebar(full_name: str):
    """Öğrenci yan paneli: bilgi seviyesi + DRL önerisi."""
    initial = full_name[0].upper() if full_name else "?"

    with st.sidebar:
        # Logo + başlık
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:.6rem;padding:.6rem 0 1.2rem;">
                <span style="font-size:1.6rem;">🎓</span>
                <span style="font-size:1rem;font-weight:900;
                             background:linear-gradient(135deg,#667eea,#f093fb);
                             -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                             background-clip:text;letter-spacing:-.3px;">Sanal Öğretmen</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Profil kartı
        status_color = "#4ade80" if st.session_state.pdfs_loaded else "#aca7cc"
        status_dot   = "●" if st.session_state.pdfs_loaded else "○"
        status_text  = "Ders notları yüklendi" if st.session_state.pdfs_loaded else "Ders notu bekleniyor"
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:.75rem;padding:.8rem;
                        background:#120f2f;border-radius:14px;
                        border:1px solid rgba(255,255,255,.05);margin-bottom:1rem;">
                <div style="width:44px;height:44px;border-radius:50%;flex-shrink:0;
                            background:linear-gradient(135deg,#667eea,#f093fb);
                            display:flex;align-items:center;justify-content:center;
                            font-weight:900;font-size:1.1rem;color:white;">{initial}</div>
                <div>
                    <p style="font-weight:700;font-size:.88rem;margin:0;color:#e7e2ff;">{full_name}</p>
                    <p style="font-size:.7rem;color:{status_color};margin:.1rem 0 0;">{status_dot} {status_text}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- Bilgi Seviyesi (Stitch HTML bar'lar) ---
        mastery = st.session_state.student_mastery
        interaction_count = len(st.session_state.interaction_history)

        st.markdown(
            '<p style="font-size:.6rem;font-weight:800;letter-spacing:.12em;'
            'text-transform:uppercase;color:#aca7cc;margin:.5rem 0 .8rem;">📊 Bilgi Seviyeniz</p>',
            unsafe_allow_html=True,
        )

        if interaction_count == 0:
            st.markdown(
                '<p style="font-size:.75rem;color:#aca7cc;">Soru sordukça bilgi seviyeniz burada görünecek.</p>',
                unsafe_allow_html=True,
            )
        else:
            bars_html = f'<p style="font-size:.7rem;color:#aca7cc;margin-bottom:.8rem;">Toplam {interaction_count} etkileşim</p>'
            for topic in CURRICULUM:
                score = mastery.get(topic["name"], 0.0)
                pct = int(score * 100)
                name = topic["name"][:17] + ("…" if len(topic["name"]) > 17 else "")
                bars_html += f"""
                <div class="sta-bar-wrap">
                    <div class="sta-bar-labels">
                        <span class="sta-bar-label">{name}</span>
                        <span class="sta-bar-pct">{pct}%</span>
                    </div>
                    <div class="sta-bar-track">
                        <div class="sta-bar-fill" style="width:{pct}%"></div>
                    </div>
                </div>"""
            st.markdown(bars_html, unsafe_allow_html=True)

        # --- Öğrenme Önerisi (Stitch chip) ---
        st.markdown(
            '<hr style="border:none;height:1px;background:linear-gradient(90deg,transparent,#474464,transparent);margin:.8rem 0;">',
            unsafe_allow_html=True,
        )
        if interaction_count > 0:
            suggestion = st.session_state.drl_policy.select_next_topic(mastery)
            action = suggestion["action"]
            topic_sug = suggestion["topic"]
            reason = suggestion["reason"]
            chip_icon = "🔁" if action == "review" else "🚀"
            chip_label = "Tekrar Önerisi" if action == "review" else "Sonraki Konu"
            chip_text = topic_sug["name"] if action == "review" else "İleri seviyeye geçebilirsin!"
            st.markdown(
                f"""
                <div class="sta-chip">
                    <p class="sta-chip-label">✨ {chip_label}</p>
                    <p class="sta-chip-text">{chip_icon} {chip_text}</p>
                </div>
                <p style="font-size:.68rem;color:#757294;margin:.4rem .2rem 0;">{reason}</p>
                """,
                unsafe_allow_html=True,
            )

        # --- Çıkış ---
        st.markdown(
            '<hr style="border:none;height:1px;background:linear-gradient(90deg,transparent,#474464,transparent);margin:.8rem 0;">',
            unsafe_allow_html=True,
        )
        _AUTHENTICATOR.logout(button_name="🚪 Çıkış Yap", location="sidebar")


def render_student_chat(username: str):
    """Öğrenci sohbet arayüzü (mevcut render_chat mantığı)."""
    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:.4rem 0 1.4rem;border-bottom:1px solid rgba(255,255,255,.05);
                    margin-bottom:1.2rem;">
            <div style="display:flex;align-items:center;gap:.7rem;">
                <div style="width:34px;height:34px;border-radius:50%;flex-shrink:0;
                            background:linear-gradient(135deg,#667eea,#f093fb);
                            display:flex;align-items:center;justify-content:center;font-size:1rem;">🎓</div>
                <span style="font-size:.68rem;font-weight:900;letter-spacing:.14em;
                             text-transform:uppercase;color:#aca7cc;">Sanal Öğretmen</span>
            </div>
            <div style="display:flex;align-items:center;gap:.45rem;">
                <span class="sta-pulse-dot"></span>
                <span style="font-size:.72rem;color:#aca7cc;font-weight:500;">Aktif Öğrenme</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.awaiting_feedback:
        st.markdown("**Bu cevabı anladın mı?**")
        col1, col2, col3 = st.columns([1, 1, 8])
        with col1:
            if st.button("👍 Anladım", key="feedback_yes"):
                _record_feedback(correct=True)
        with col2:
            if st.button("👎 Anlamadım", key="feedback_no"):
                _record_feedback(correct=False)

    if prompt := st.chat_input("Python ile ilgili sorunuzu sorun..."):
        if st.session_state.awaiting_feedback:
            _record_feedback(correct=True)

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Sistem logu
        append_chat_log(username, "user", prompt)

        if is_understood(prompt):
            response = "Harika! Anlayışın için sevindim. 😊 Başka merak ettiğin bir konu var mı?"
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            append_chat_log(username, "assistant", response)
            st.session_state.awaiting_feedback = False
            if st.session_state.pending_topic_id is not None:
                _record_feedback(correct=True)
            else:
                st.rerun()

        if is_curriculum_query(prompt):
            response = build_curriculum_response(st.session_state.current_topic)
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            append_chat_log(username, "assistant", response)
            st.session_state.awaiting_feedback = False
            st.rerun()

        simplify_mode = is_simplify_request(prompt)
        if simplify_mode:
            current_topic_id = st.session_state.current_topic
            current_topic_name = next(
                (t["name"] for t in CURRICULUM if t["id"] == current_topic_id), None
            ) if current_topic_id else None
            rag_query = f"{current_topic_name} nedir? Tek cümleyle basit tanım." if current_topic_name else prompt
            topic_id = current_topic_id
            socratic_suffix = ""
            full_suffix = (
                f"Öğrenci anlamadığını belirtti. Bağlamdaki döngü/akümülatör örneklerini KULLANMA. "
                f"Sadece '{current_topic_name} nedir?' sorusunu yanıtla: "
                f"(1) tek cümle tanım, (2) günlük hayattan bir benzetme, (3) tek satır kod örneği. "
                f"Başka hiçbir şey ekleme."
            ) if current_topic_name else ""
        else:
            rag_query = prompt
            topic_id = detect_topic(prompt)
            st.session_state.pending_topic_id = topic_id

            prev_topic = st.session_state.current_topic
            if topic_id is not None and topic_id != prev_topic:
                if prev_topic is not None:
                    prev_name = next((t["name"] for t in CURRICULUM if t["id"] == prev_topic), None)
                    if prev_name:
                        st.session_state.socratic_manager.reset_attempts(prev_name)
                st.session_state.current_topic = topic_id

            topic_name = next((t["name"] for t in CURRICULUM if t["id"] == topic_id), None) if topic_id else None
            socratic_suffix = st.session_state.socratic_manager.get_socratic_prompt_suffix(topic_name) if topic_name else ""

            level_context = get_level_context(
                st.session_state.interaction_history,
                st.session_state.student_mastery,
            )
            full_suffix = f"{socratic_suffix}\n{level_context}".strip() if socratic_suffix else level_context

        with st.chat_message("assistant"):
            if st.session_state.rag_chain is not None:
                with st.spinner("Düşünüyorum..."):
                    try:
                        from modules.rag import ask
                        result = ask(st.session_state.rag_chain, rag_query, socratic_suffix=full_suffix)
                        response = result["answer"]
                    except Exception as e:
                        response = f"⚠️ Bir hata oluştu: {e}"
            else:
                response = (
                    "📚 Henüz ders notu yüklenmedi. "
                    "Öğretmeninizin ders notlarını sisteme yüklemesini bekleyin."
                )

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            append_chat_log(username, "assistant", response)

        st.session_state.awaiting_feedback = topic_id is not None
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# ÖĞRETMEN PANELİ
# ═══════════════════════════════════════════════════════════════════════════════

def render_teacher_sidebar(full_name: str):
    """Öğretmen yan paneli: Stitch nav tasarımı."""
    with st.sidebar:
        # Logo + subtitle
        st.markdown(
            """
            <div style="padding:.5rem 0 1.8rem;">
                <p style="font-size:1.15rem;font-weight:900;margin:0;letter-spacing:-.3px;
                          background:linear-gradient(135deg,#667eea,#f093fb);
                          -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                          background-clip:text;">Sanal Öğretmen</p>
                <p style="font-size:.58rem;font-weight:800;letter-spacing:.15em;
                          text-transform:uppercase;color:#757294;margin:.2rem 0 0;">Eğitmen Paneli</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Nav items (görsel — Streamlit sekmeleri zaten ana alanda)
        st.markdown(
            """
            <nav style="margin-bottom:1.2rem;">
                <div style="display:flex;align-items:center;gap:.7rem;padding:.65rem .8rem;
                            border-left:3px solid #667eea;margin-bottom:3px;
                            background:linear-gradient(90deg,rgba(102,126,234,.18),transparent);
                            border-radius:0 10px 10px 0;">
                    <span>📊</span>
                    <span style="font-size:.85rem;font-weight:700;color:#97a9ff;">Genel Bakış</span>
                </div>
                <div style="display:flex;align-items:center;gap:.7rem;padding:.65rem .8rem;
                            border-left:3px solid transparent;margin-bottom:3px;opacity:.55;
                            border-radius:0 10px 10px 0;">
                    <span>👥</span>
                    <span style="font-size:.85rem;font-weight:500;">Öğrenciler</span>
                </div>
                <div style="display:flex;align-items:center;gap:.7rem;padding:.65rem .8rem;
                            border-left:3px solid transparent;margin-bottom:3px;opacity:.55;
                            border-radius:0 10px 10px 0;">
                    <span>📈</span>
                    <span style="font-size:.85rem;font-weight:500;">Raporlar</span>
                </div>
                <div style="display:flex;align-items:center;gap:.7rem;padding:.65rem .8rem;
                            border-left:3px solid transparent;opacity:.55;
                            border-radius:0 10px 10px 0;">
                    <span>⚙️</span>
                    <span style="font-size:.85rem;font-weight:500;">Ayarlar</span>
                </div>
            </nav>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<hr style="border:none;height:1px;background:rgba(255,255,255,.06);margin:.5rem 0 1rem;">',
            unsafe_allow_html=True,
        )

        # PDF yükleme kartı (Stitch dashed card)
        st.markdown(
            '<p style="font-size:.62rem;font-weight:800;letter-spacing:.12em;'
            'text-transform:uppercase;color:#aca7cc;margin-bottom:.6rem;">📄 Müfredat PDF Yükle</p>',
            unsafe_allow_html=True,
        )
        uploaded_files = st.file_uploader(
            "PDF ders notlarını yükleyin",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded_files:
            if st.button("📥 İşle", type="primary", use_container_width=True):
                with st.spinner("İşleniyor..."):
                    if "rag_chain" not in st.session_state:
                        st.session_state.rag_chain = None
                    process_uploaded_pdfs(uploaded_files)

        st.markdown(
            f'<hr style="border:none;height:1px;background:rgba(255,255,255,.06);margin:1.2rem 0 .6rem;">'
            f'<p style="font-size:.72rem;color:#757294;margin:0 0 .5rem;">👤 {full_name}</p>',
            unsafe_allow_html=True,
        )
        _AUTHENTICATOR.logout(button_name="↪ Çıkış Yap", location="sidebar")


def render_teacher_panel():
    """Öğretmen ana paneli: Stitch tasarımı."""
    full_name = st.session_state.get("name", "Eğitmen")

    # ── Hoş Geldiniz başlığı ──────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="sta-teacher-header">
            <h1>Hoş Geldiniz,
                <span style="background:linear-gradient(135deg,#667eea,#f093fb);
                             -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                             background-clip:text;">{full_name}</span>
            </h1>
            <p>Python rehberiniz ve öğrenci gelişim takip merkeziniz.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_analytics, tab_logs, tab_curriculum = st.tabs([
        "📊 Öğrenci Analitiği",
        "🗂️ Sistem Logları",
        "📚 Müfredat",
    ])

    # ── Öğrenci Analitiği ──────────────────────────────────────────────────
    with tab_analytics:
        all_students = load_all_students()

        if not all_students:
            st.info("Henüz kayıtlı öğrenci verisi yok.")
        else:
            # Konu bazında sınıf ortalaması — Stitch metric kartları
            topic_icons = ["🔣", "➗", "🔀", "🔁", "📋", "📚", "⚙️", "📂", "⚠️", "🏛️"]
            avg_data = []
            for i, topic in enumerate(CURRICULUM):
                scores = [
                    data.get("student_mastery", {}).get(topic["name"], 0.0)
                    for data in all_students.values()
                ]
                avg = sum(scores) / len(scores) if scores else 0.0
                avg_data.append((topic, avg, topic_icons[i % len(topic_icons)]))

            # 4'lü grid (ilk 4 konu ön plana)
            cols = st.columns(4)
            for ci, (topic, avg, icon) in enumerate(avg_data[:4]):
                pct = int(avg * 100)
                delta_html = (
                    f'<span class="sta-metric-delta-up">↑ iyi</span>'
                    if avg >= 0.7 else
                    f'<span class="sta-metric-delta-down">↓ çalış</span>'
                )
                with cols[ci]:
                    st.markdown(
                        f"""
                        <div class="sta-metric-card">
                            <div class="sta-metric-card-icon">{icon}</div>
                            <p class="sta-metric-label">{topic['name'][:16]}</p>
                            <p class="sta-metric-value">%{pct} {delta_html}</p>
                            <p class="sta-metric-sub">Ortalama Başarı Oranı</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("<br>", unsafe_allow_html=True)

            # Öğrenci tablosu — Stitch HTML
            rows_html = ""
            for uname, data in all_students.items():
                mastery   = data.get("student_mastery", {})
                ints      = data.get("interaction_history", [])
                correct   = sum(1 for x in ints if x.get("correct"))
                total     = len(ints)
                rate      = correct / total if total else 0.0
                avg_m     = sum(mastery.values()) / len(mastery) if mastery else 0.0
                pct       = int(avg_m * 100)
                score     = round(rate * 10, 1)
                badge_cls = "sta-score-green" if score >= 7 else ("sta-score-yellow" if score >= 5 else "sta-score-red")
                init      = uname[0].upper()
                rows_html += f"""
                <div class="sta-student-row">
                    <div class="sta-avatar">{init}</div>
                    <div style="flex:1;min-width:0;">
                        <p class="sta-student-name">{uname}</p>
                        <p class="sta-student-sub">{total} etkileşim</p>
                    </div>
                    <div style="text-align:right;min-width:130px;">
                        <div class="sta-mini-bar-track" style="margin-left:auto;">
                            <div class="sta-mini-bar-fill" style="width:{pct}%"></div>
                        </div>
                        <p style="font-size:.65rem;font-weight:700;color:#97a9ff;margin:.3rem 0 0;">{pct}% Tamamlandı</p>
                    </div>
                    <div style="width:50px;text-align:center;">
                        <span class="sta-score-badge {badge_cls}">{score}</span>
                    </div>
                </div>"""

            st.markdown(
                f"""
                <div class="sta-table-wrap">
                    <div class="sta-table-header">
                        <p class="sta-table-title">Öğrenci Gelişim Tablosu</p>
                        <span style="font-size:.75rem;color:#aca7cc;">{len(all_students)} öğrenci</span>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr 160px 60px;
                                padding:.5rem 1.4rem;gap:1rem;">
                        <span style="font-size:.6rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#757294;">Öğrenci Adı</span>
                        <span style="font-size:.6rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#757294;">Etkileşim</span>
                        <span style="font-size:.6rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#757294;">Genel İlerleme</span>
                        <span style="font-size:.6rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#757294;">Skor</span>
                    </div>
                    {rows_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Sistem Logları ─────────────────────────────────────────────────────
    with tab_logs:
        logs = load_chat_log(last_n=200)
        if not logs:
            st.info("Henüz sohbet kaydı yok.")
        else:
            col_f1, col_f2 = st.columns([2, 2])
            with col_f1:
                student_filter = st.selectbox(
                    "Öğrenci filtresi",
                    options=["Tümü"] + sorted({l["username"] for l in logs}),
                )
            with col_f2:
                role_filter = st.selectbox(
                    "Mesaj türü", options=["Tümü", "user", "assistant"],
                )

            filtered = logs
            if student_filter != "Tümü":
                filtered = [l for l in filtered if l["username"] == student_filter]
            if role_filter != "Tümü":
                filtered = [l for l in filtered if l["role"] == role_filter]

            for entry in filtered[:100]:
                is_user = entry["role"] == "user"
                icon    = "💬" if is_user else "🤖"
                cls     = "" if is_user else "assistant"
                st.markdown(
                    f"""
                    <div class="sta-log-entry {cls}">
                        <span style="font-size:1.1rem;flex-shrink:0;">{icon}</span>
                        <div style="flex:1;min-width:0;">
                            <p class="sta-log-user">{entry['username']}
                                <span class="sta-log-ts">{entry['ts']}</span>
                            </p>
                            <p class="sta-log-text">{entry['content'][:200]}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── Müfredat ──────────────────────────────────────────────────────────
    with tab_curriculum:
        st.markdown(
            '<p style="font-size:.7rem;font-weight:800;letter-spacing:.12em;'
            'text-transform:uppercase;color:#aca7cc;margin-bottom:1rem;">📚 Python Müfredatı (10 Konu)</p>',
            unsafe_allow_html=True,
        )
        for topic in CURRICULUM:
            stars = "⭐" * topic["difficulty"]
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;justify-content:space-between;
                            padding:.7rem 1rem;margin-bottom:.4rem;
                            background:rgba(102,126,234,.06);border-radius:12px;
                            border:1px solid rgba(151,169,255,.08);">
                    <div style="display:flex;align-items:center;gap:.7rem;">
                        <span style="font-size:.7rem;font-weight:800;color:#97a9ff;
                                     min-width:1.5rem;text-align:right;">{topic['id']}.</span>
                        <span style="font-size:.88rem;font-weight:600;color:#e7e2ff;">{topic['name']}</span>
                    </div>
                    <span style="font-size:.75rem;">{stars}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# GİRİŞ EKRANI
# ═══════════════════════════════════════════════════════════════════════════════

def render_login():
    """Giriş ekranı — Stitch tasarımı ile."""
    # Arka plan glow'lar + sol alt kod dekorasyonu (fixed, z-index 0)
    st.markdown(
        """
        <div class="sta-glow sta-glow-1"></div>
        <div class="sta-glow sta-glow-2"></div>
        <div class="sta-glow sta-glow-3"></div>

        <!-- Sol alt kod dekorasyonu -->
        <div class="sta-code-deco">
            <div class="sta-code-back">
                <div class="sta-code-back-dots">
                    <span style="background:#ff6e84"></span>
                    <span style="background:#f59e0b"></span>
                    <span style="background:#4ade80"></span>
                </div>
                <div style="display:flex;flex-direction:column;gap:6px;">
                    <div style="height:7px;width:75%;background:rgba(151,169,255,.2);border-radius:4px;"></div>
                    <div style="height:7px;width:100%;background:rgba(151,169,255,.1);border-radius:4px;"></div>
                    <div style="height:7px;width:50%;background:rgba(248,172,255,.2);border-radius:4px;"></div>
                    <div style="height:7px;width:65%;background:rgba(151,169,255,.1);border-radius:4px;"></div>
                </div>
            </div>
            <div class="sta-code-front">
                <span style="color:#e589f0;">def </span><span style="color:#97a9ff;">ogrenci_giris</span>(kod):<br>
                &nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#aca7cc;">print</span>(<span style="color:#dab4ff;">"Hoşgeldiniz!"</span>)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#e589f0;">return </span><span style="color:#8197ff;">True</span>
            </div>
        </div>

        <!-- Footer -->
        <p style="position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%);
                  font-size:.72rem;color:rgba(172,167,204,.5);z-index:1;white-space:nowrap;">
            © 2024 Sanal Öğretmen. Tüm hakları saklıdır.
        </p>
        """,
        unsafe_allow_html=True,
    )

    _, col_m, _ = st.columns([1, 2, 1])
    with col_m:
        # Logo + başlık (Streamlit widget değil — sadece HTML)
        st.markdown(
            """
            <div style="text-align:center;padding:.5rem 0 .8rem;">
                <div class="sta-logo-wrap">🎓</div>
                <p class="sta-title">Sanal Öğretmen Asistanı</p>
                <p class="sta-sub">Yapay Zeka Destekli Python Öğrenim Rehberi</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Authenticator formu — CSS ile [data-testid="stForm"] kart olarak stilize edildi
        _AUTHENTICATOR.login(location="main", fields={
            "Form name": "Giriş Yap",
            "Username": "Kullanıcı Adı",
            "Password": "Şifre",
            "Login": "Giriş Yap",
        })

        auth_status = st.session_state.get("authentication_status")
        if auth_status is False:
            st.error("❌ Kullanıcı adı veya şifre hatalı.")
        elif auth_status is None:
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin:.8rem 0 .5rem;">
                    <div style="height:1px;flex:1;background:linear-gradient(90deg,transparent,rgba(71,68,100,.5));"></div>
                    <span style="font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;
                                 color:#757294;white-space:nowrap;">Erişim Bilgileri</span>
                    <div style="height:1px;flex:1;background:linear-gradient(90deg,rgba(71,68,100,.5),transparent);"></div>
                </div>
                <div class="sta-demo">
                    <span style="font-size:.65rem;font-weight:800;color:rgba(227,196,255,.6);
                                 text-transform:uppercase;letter-spacing:.08em;">Kullanıcı:</span>
                    <code>ali</code>
                    <div class="sta-sep"></div>
                    <span style="font-size:.65rem;font-weight:800;color:rgba(227,196,255,.6);
                                 text-transform:uppercase;letter-spacing:.08em;">Şifre:</span>
                    <code>ogrenci123</code>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# ANA AKIŞ
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    _inject_css()
    auth_status = st.session_state.get("authentication_status")

    if not auth_status:
        render_login()
        st.stop()

    # Giriş başarılı — kullanıcı bilgilerini al
    username  = st.session_state.get("username", "")
    full_name = st.session_state.get("name", username)
    role = _AUTH_CONFIG["credentials"]["usernames"].get(username, {}).get("role", "student")

    if role == "teacher":
        render_teacher_sidebar(full_name)
        render_teacher_panel()
    else:
        init_student_session(username)
        render_student_sidebar(full_name)
        render_student_chat(username)


if __name__ == "__main__":
    main()
