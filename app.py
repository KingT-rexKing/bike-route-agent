# =============================================
# app.py  ―  フロントエンド（UI）
# =============================================

import urllib.parse
import requests
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
from agent import run_agent

st.set_page_config(
    page_title="バイクルートAI",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Wikipedia サムネイル ─────────────────────────────────────────
_THUMB_CACHE: dict = {}

def fetch_wiki_thumb(name: str):
    if name in _THUMB_CACHE:
        return _THUMB_CACHE[name]
    try:
        r = requests.get(
            "https://ja.wikipedia.org/w/api.php",
            params={"action":"query","titles":name,"prop":"pageimages",
                    "format":"json","pithumbsize":160},
            headers={"User-Agent":"BikeRouteAgent/1.0"},
            timeout=4,
        )
        pages = r.json().get("query",{}).get("pages",{})
        for p in pages.values():
            src = p.get("thumbnail",{}).get("source")
            if src:
                _THUMB_CACHE[name] = src
                return src
    except Exception:
        pass
    _THUMB_CACHE[name] = None
    return None


# ── グローバルCSS（Streamlit UIのテーマ） ─────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@500;600;700&family=Noto+Sans+JP:wght@400;700&display=swap');

#MainMenu,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],footer{visibility:hidden!important;height:0!important}
h1 a,h2 a,h3 a{display:none!important}

:root{
  --bg:#050508;
  --surface:#0c0c12;
  --surface-hi:#131319;
  --accent:#E85000;
  --text:#ebebeb;
  --text-muted:rgba(235,235,235,0.45);
  --text-dim:rgba(235,235,235,0.22);
  --border:rgba(232,80,0,0.18);
  --border-sub:rgba(255,255,255,0.05);
}

body{background:var(--bg)!important;margin:0}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"],
section.main,.main{background:var(--bg)!important}

/* ── サイドバー ── */
[data-testid="stSidebar"]{
  background:rgba(5,5,10,0.97)!important;
  border-right:1px solid var(--border)!important;
}
[data-testid="stSidebar"]>div{padding-top:1.2rem}

/* ── 入力 ── */
[data-testid="stTextInput"] input{
  background:rgba(255,255,255,0.04)!important;
  border:1px solid var(--border)!important;
  border-radius:6px!important;
  color:var(--text)!important;
  font-family:'Noto Sans JP',sans-serif!important;
  transition:border-color 0.2s,box-shadow 0.2s;
}
[data-testid="stTextInput"] input:focus{
  border-color:rgba(232,80,0,0.55)!important;
  box-shadow:0 0 0 3px rgba(232,80,0,0.1)!important;
  outline:none!important;
}
[data-testid="stTextInput"] label{color:var(--text-muted)!important;font-size:0.8rem!important}
[data-testid="stRadio"] label,[data-testid="stCheckbox"] label{
  color:rgba(235,235,235,0.72)!important;
}

/* ── ボタン ── */
[data-testid="stBaseButton-primary"]{
  background:#E85000!important;
  border:none!important;border-radius:7px!important;
  font-family:'Rajdhani',sans-serif!important;
  font-size:1rem!important;font-weight:700!important;
  letter-spacing:0.1em!important;color:#fff!important;
  transition:transform 0.15s,box-shadow 0.15s!important;
}
[data-testid="stBaseButton-primary"]:hover{
  transform:translateY(-2px)!important;
  box-shadow:0 6px 22px rgba(232,80,0,0.42)!important;
}
[data-testid="stBaseButton-primary"]:active{transform:translateY(0)!important}
[data-testid="stBaseButton-secondary"]{
  background:rgba(255,255,255,0.04)!important;
  border:1px solid var(--border)!important;border-radius:6px!important;
  color:rgba(235,235,235,0.7)!important;
  font-family:'Rajdhani',sans-serif!important;font-weight:600!important;
}

/* ── サイドバーラベル ── */
.sb-label{
  font-family:'Rajdhani',sans-serif;
  font-size:0.66rem;letter-spacing:0.28em;
  color:rgba(232,80,0,0.58);
  text-transform:uppercase;
  margin:1.2rem 0 0.3rem;
}

/* ── タブ ── */
[data-testid="stTabs"] [role="tablist"]{
  border-bottom:1px solid var(--border-sub)!important;gap:0.2rem
}
[data-testid="stTabs"] [role="tab"]{
  font-family:'Rajdhani',sans-serif!important;font-size:0.95rem!important;
  font-weight:600!important;color:var(--text-muted)!important;
  letter-spacing:0.04em!important;padding:0.5rem 1.1rem!important;
  border-radius:6px 6px 0 0!important;
  transition:color 0.2s,background 0.2s!important;
}
[data-testid="stTabs"] [role="tab"]:hover{color:var(--text)!important;background:rgba(232,80,0,0.05)!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#E85000!important;background:rgba(232,80,0,0.07)!important}

/* ── Markdown/テーブル ── */
[data-testid="stMarkdownContainer"]{color:rgba(235,235,235,0.8)!important}
[data-testid="stMarkdownContainer"] h2{
  font-family:'Rajdhani',sans-serif!important;font-size:1.2rem!important;
  color:#E85000!important;letter-spacing:0.04em!important;
  border-bottom:1px solid var(--border);
  padding-bottom:0.3rem;margin-top:1.5rem!important;
}
[data-testid="stMarkdownContainer"] table{width:100%!important;border-collapse:collapse!important}
[data-testid="stMarkdownContainer"] th{
  background:rgba(232,80,0,0.09)!important;color:#E85000!important;
  font-family:'Rajdhani',sans-serif!important;letter-spacing:0.05em!important;
  padding:0.6rem 0.8rem!important;border:1px solid var(--border)!important;
}
[data-testid="stMarkdownContainer"] td{
  padding:0.55rem 0.8rem!important;border:1px solid var(--border-sub)!important;
  color:rgba(235,235,235,0.75)!important;
}
[data-testid="stMarkdownContainer"] tr:hover td{background:rgba(232,80,0,0.04)!important}

/* ── スポットテーブル ── */
.spot-table{width:100%;border-collapse:collapse}
.spot-table th{
  background:rgba(232,80,0,0.09);color:#E85000;
  font-family:'Rajdhani',sans-serif;letter-spacing:0.07em;
  padding:0.6rem 0.8rem;border-bottom:1px solid var(--border);
  font-size:0.8rem;text-align:left;white-space:nowrap;
}
.spot-table td{padding:0.65rem 0.8rem;border-bottom:1px solid var(--border-sub);vertical-align:middle}
.spot-table tr:hover td{background:rgba(232,80,0,0.04)}
.spot-time{font-family:'Bebas Neue',sans-serif;font-size:1rem;color:#F09060;white-space:nowrap}
.spot-link{color:#E85000!important;text-decoration:none;font-weight:600;font-size:0.88rem}
.spot-link:hover{color:#ff7030!important;text-decoration:underline}
.spot-thumb{width:70px;height:48px;object-fit:cover;border-radius:5px;border:1px solid var(--border);display:block}
.spot-no-img{
  width:70px;height:48px;border-radius:5px;
  border:1px solid var(--border-sub);
  background:var(--surface-hi);
  display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;color:var(--text-dim);
}
.spot-cat{font-size:0.67rem;color:var(--text-dim);margin-top:2px}
.spot-stay{font-family:'Rajdhani',sans-serif;color:#E85000;font-weight:700;font-size:0.9rem}

/* ── ローダー ── */
@keyframes moto-ride{0%{left:-8%}100%{left:108%}}
@keyframes dash-flow{0%{background-position:0 0}100%{background-position:54px 0}}
.moto-loader{
  position:relative;width:100%;height:72px;overflow:hidden;
  background:var(--surface);border-radius:10px;
  border:1px solid var(--border);margin:1rem 0;
}
.moto-label{
  position:absolute;top:10px;left:0;right:0;text-align:center;
  font-family:'Rajdhani',sans-serif;font-size:0.84rem;letter-spacing:0.12em;
  color:var(--text-muted);
}
.moto-track{
  position:absolute;bottom:22px;left:0;right:0;height:2px;
  background:repeating-linear-gradient(90deg,rgba(232,80,0,0.55) 0,rgba(232,80,0,0.55) 16px,transparent 16px,transparent 32px);
  animation:dash-flow .3s linear infinite;
}
.moto-bike{
  position:absolute;bottom:14px;font-size:1.6rem;line-height:1;
  filter:drop-shadow(0 0 7px rgba(232,80,0,0.9));
  animation:moto-ride 2.4s linear infinite;
}

/* ── 統計ストリップ ── */
@keyframes count-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.stats-strip{
  display:flex;
  border:1px solid var(--border);border-radius:10px;
  overflow:hidden;margin-bottom:1.4rem;
  animation:count-in 0.5s ease-out;
}
.stat-item{flex:1;padding:1.1rem 0.8rem 0.9rem;text-align:center;border-right:1px solid var(--border-sub)}
.stat-item:last-child{border-right:none}
.stat-num{font-family:'Bebas Neue',sans-serif;font-size:2.1rem;color:#E85000;line-height:1}
.stat-unit{font-family:'Rajdhani',sans-serif;font-size:0.78rem;color:var(--text-muted);margin-left:2px}
.stat-label{font-family:'Rajdhani',sans-serif;font-size:0.6rem;letter-spacing:0.22em;color:var(--text-dim);text-transform:uppercase;margin-top:0.22rem}

/* ── メインエリア ── */
.main .block-container,
.stMainBlockContainer,
[data-testid="stMainBlockContainer"]{
  padding-top:0!important;padding-bottom:0!important;
  max-width:100%!important;padding-left:1rem;padding-right:1rem
}
[data-testid="stVerticalBlock"]{gap:0!important}
.element-container{margin-bottom:0!important}
hr{border-color:var(--border-sub)!important;margin:1.4rem 0!important}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(232,80,0,0.28);border-radius:2px}

/* ── iframe の隙間・ボーダーを除去 ── */
iframe{border:none!important;display:block}
[data-testid="stIFrame"]{margin:0!important;padding:0!important}
.element-container:has(iframe){margin-bottom:0!important;padding:0!important}
.stMainBlockContainer > div > div > div > .element-container{margin-bottom:0!important}
</style>
""", unsafe_allow_html=True)


# ── ヒーロー（Canvas アニメーション + JavaScript） ──────────────
# st.components.v1.html() は独立した iframe でレンダリングされるため
# JavaScript が完全に実行される（st.markdown では不可）
components.html("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;overflow:hidden;background:#050508}
canvas{position:absolute;inset:0;width:100%;height:100%}
.overlay{
  position:absolute;inset:0;
  display:flex;flex-direction:column;
  justify-content:center;padding:0 7%;
  z-index:10;pointer-events:none;
}
h1{
  font-family:'Bebas Neue',sans-serif;
  font-size:clamp(3.5rem,8.5vw,7.5rem);
  line-height:0.95;letter-spacing:0.03em;
  color:#ebebeb;
  opacity:0;animation:up 0.9s 0.2s cubic-bezier(0.16,1,0.3,1) forwards;
}
h1 .ac{color:#E85000}
.sub{
  font-family:'Rajdhani',sans-serif;
  font-size:clamp(0.8rem,1.4vw,1rem);
  letter-spacing:0.18em;
  color:rgba(235,235,235,0.42);
  margin-top:0.7rem;
  opacity:0;animation:up 0.9s 0.45s cubic-bezier(0.16,1,0.3,1) forwards;
}
.hint{
  font-family:'Rajdhani',sans-serif;
  font-size:clamp(0.72rem,1.1vw,0.85rem);
  letter-spacing:0.12em;
  color:rgba(232,80,0,0.55);
  margin-top:1.6rem;
  opacity:0;animation:up 0.9s 0.7s cubic-bezier(0.16,1,0.3,1) forwards;
  display:flex;align-items:center;gap:0.5rem;
}
.hint-arrow{
  display:inline-block;
  animation:arrow-pulse 1.8s ease-in-out infinite;
}
@keyframes arrow-pulse{0%,100%{transform:translateX(0);opacity:0.55}50%{transform:translateX(5px);opacity:1}}
@keyframes up{
  from{opacity:0;transform:translateY(22px)}
  to{opacity:1;transform:translateY(0)}
}
@media(prefers-reduced-motion:reduce){
  h1,.sub,.hint{animation:none;opacity:1}
  .hint-arrow{animation:none}
}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div class="overlay">
  <h1>BIKE ROUTE<br><span class="ac">AI</span></h1>
  <div class="sub">125cc / 50cc &nbsp;&nbsp;·&nbsp;&nbsp; 下道専用 &nbsp;&nbsp;·&nbsp;&nbsp; Japan Touring Planner</div>
  <div class="hint">
    <span class="hint-arrow">←</span>
    <span>左のサイドバーで条件を入力してプランを生成する</span>
  </div>
</div>

<script>
const c = document.getElementById('c');
const cx = c.getContext('2d');
let W, H, hz;

function resize() {
  const rect = c.parentElement.getBoundingClientRect();
  W = c.width = rect.width || window.innerWidth;
  H = c.height = rect.height || window.innerHeight;
  hz = H * 0.5;
}
resize();
window.addEventListener('resize', resize);

// Center dashes (road perspective)
const N = 16;
const dashes = Array.from({length: N}, (_, i) => ({ t: i / N }));

// Stars
const stars = Array.from({length: 90}, () => ({
  x: Math.random(),
  y: Math.random(),
  r: Math.random() * 1.3 + 0.3,
  a: Math.random() * 0.6 + 0.2,
  twinkle: Math.random() * Math.PI * 2,
}));

// Mountain profile (generated once)
const mts = [];
for (let x = 0; x <= 60; x++) {
  mts.push(0.35 + Math.sin(x * 0.18) * 0.06 + Math.sin(x * 0.43) * 0.04 + Math.sin(x * 0.9) * 0.02);
}

// Mouse position for parallax
let mx = 0.5, my = 0.5;
document.addEventListener('mousemove', e => {
  mx = e.clientX / W;
  my = e.clientY / H;
});

let glowPhase = 0;
let frame = 0;

function lerp(a, b, t) { return a + (b - a) * t; }

function draw() {
  frame++;
  glowPhase += 0.012;
  cx.clearRect(0, 0, W, H);

  // ── Sky ──
  const sky = cx.createLinearGradient(0, 0, 0, hz + 20);
  sky.addColorStop(0,   '#020205');
  sky.addColorStop(0.55,'#080418');
  sky.addColorStop(1,   '#130700');
  cx.fillStyle = sky;
  cx.fillRect(0, 0, W, hz + 20);

  // ── Stars (parallax + twinkle) ──
  const px = (mx - 0.5) * 20;
  const py = (my - 0.5) * 10;
  stars.forEach(s => {
    s.twinkle += 0.02;
    const a = s.a * (0.7 + 0.3 * Math.sin(s.twinkle));
    const sx = s.x * W + px * (s.r * 0.4);
    const sy = s.y * hz + py * (s.r * 0.2);
    cx.beginPath();
    cx.arc(sx, sy, s.r, 0, Math.PI * 2);
    cx.fillStyle = `rgba(255,255,255,${a})`;
    cx.fill();
  });

  // ── Mountains (2 layers) ──
  const drawMtn = (color, opacity, scale, yBase) => {
    cx.beginPath();
    cx.moveTo(0, hz + 10);
    for (let i = 0; i <= 60; i++) {
      const x = (i / 60) * W;
      const y = hz - (mts[i] * H * scale) + (mx - 0.5) * 8;
      i === 0 ? cx.moveTo(x, y) : cx.lineTo(x, y);
    }
    cx.lineTo(W, hz + 10);
    cx.lineTo(0, hz + 10);
    cx.closePath();
    cx.fillStyle = color;
    cx.globalAlpha = opacity;
    cx.fill();
    cx.globalAlpha = 1;
  };
  drawMtn('#0a0a1e', 0.95, 0.48, 0.52);
  drawMtn('#060610', 1.0,  0.34, 0.54);

  // ── Horizon glow (pulsing) ──
  const glowA = 0.14 + Math.sin(glowPhase) * 0.05;
  const hg = cx.createRadialGradient(W/2, hz, 0, W/2, hz, W * 0.4);
  hg.addColorStop(0,   `rgba(232,80,0,${glowA})`);
  hg.addColorStop(0.45,`rgba(200,50,0,${glowA * 0.25})`);
  hg.addColorStop(1,   'rgba(0,0,0,0)');
  cx.fillStyle = hg;
  cx.fillRect(0, hz - H * 0.25, W, H * 0.5);

  // ── Ground ──
  const gnd = cx.createLinearGradient(0, hz, 0, H);
  gnd.addColorStop(0, '#060606');
  gnd.addColorStop(1, '#030303');
  cx.fillStyle = gnd;
  cx.fillRect(0, hz, W, H - hz);

  // ── Road (perspective trapezoid) ──
  const rl  = W * 0.35, rr  = W * 0.65;
  const rfl = W * 0.474, rfr = W * 0.526;
  cx.beginPath();
  cx.moveTo(rfl, hz);
  cx.lineTo(rfr, hz);
  cx.lineTo(rr, H);
  cx.lineTo(rl, H);
  cx.closePath();
  const rdg = cx.createLinearGradient(0, hz, 0, H);
  rdg.addColorStop(0, '#0a0a0a');
  rdg.addColorStop(1, '#131313');
  cx.fillStyle = rdg;
  cx.fill();

  // Road edge lines
  cx.strokeStyle = 'rgba(255,255,255,0.06)';
  cx.lineWidth = 1.5;
  cx.beginPath(); cx.moveTo(rfl, hz); cx.lineTo(rl, H); cx.stroke();
  cx.beginPath(); cx.moveTo(rfr, hz); cx.lineTo(rr, H); cx.stroke();

  // ── Animated center dashes ──
  const spd = 0.006;
  dashes.forEach(d => {
    d.t = (d.t + spd) % 1;
    const t0 = d.t;
    const t1 = Math.min(d.t + 0.05, 1);
    // Ease-in-quad for natural perspective acceleration
    const e0 = t0 * t0;
    const e1 = t1 * t1;
    const y0 = hz + (H - hz) * e0;
    const y1 = hz + (H - hz) * e1;
    // Width grows with depth
    const w0 = lerp(0.5, 9, e0);
    const w1 = lerp(0.5, 9, e1);
    const alpha = lerp(0.04, 0.55, e0);
    cx.beginPath();
    cx.moveTo(W/2 - w0/2, y0);
    cx.lineTo(W/2 + w0/2, y0);
    cx.lineTo(W/2 + w1/2, y1);
    cx.lineTo(W/2 - w1/2, y1);
    cx.closePath();
    cx.fillStyle = `rgba(232,80,0,${alpha})`;
    cx.fill();
  });

  // Road center glow
  const rcg = cx.createRadialGradient(W/2, H, 0, W/2, H, W * 0.22);
  rcg.addColorStop(0,   'rgba(232,80,0,0.08)');
  rcg.addColorStop(1,   'rgba(0,0,0,0)');
  cx.fillStyle = rcg;
  cx.fillRect(0, hz, W, H - hz);

  // ── Horizon line ──
  cx.strokeStyle = `rgba(232,80,0,${0.08 + Math.sin(glowPhase) * 0.03})`;
  cx.lineWidth = 1;
  cx.beginPath();
  cx.moveTo(0, hz);
  cx.lineTo(W, hz);
  cx.stroke();

  requestAnimationFrame(draw);
}
requestAnimationFrame(draw);
</script>
</body>
</html>
""", height=400, scrolling=False)


# ── 機能紹介（3D ホバーカード、JavaScript） ─────────────────────
components.html("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@500;600;700&family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{
  background:#050508;
  font-family:'Rajdhani',sans-serif;
  color:#ebebeb;
  height:100%;overflow:hidden;
  padding:1rem 1.2rem 0.8rem;
}
.grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:0.75rem;
  height:calc(100% - 0.2rem);
}
.card{
  background:#0c0c12;
  border:1px solid rgba(232,80,0,0.16);
  border-radius:14px;
  padding:1.4rem 1.3rem;
  position:relative;overflow:hidden;
  cursor:default;
  transform-style:preserve-3d;
  transition:border-color 0.3s;
  will-change:transform;
}
.card::before{
  content:'';
  position:absolute;inset:0;border-radius:14px;
  background:radial-gradient(circle at var(--mx,50%) var(--my,50%),
    rgba(232,80,0,0.12) 0%, transparent 65%);
  opacity:0;transition:opacity 0.3s;pointer-events:none;
}
.card:hover{border-color:rgba(232,80,0,0.45)}
.card:hover::before{opacity:1}
.card-num{
  font-family:'Bebas Neue',sans-serif;
  font-size:0.8rem;letter-spacing:0.15em;
  color:rgba(232,80,0,0.6);
  margin-bottom:0.6rem;display:block;
}
.card-title{
  font-size:1.1rem;font-weight:700;
  color:#ebebeb;margin-bottom:0.5rem;
  letter-spacing:0.02em;
}
.card-desc{
  font-family:'Noto Sans JP',sans-serif;
  font-size:0.75rem;
  color:rgba(235,235,235,0.45);
  line-height:1.8;
}
.card-glyph{
  position:absolute;bottom:1rem;right:1.2rem;
  font-family:'Bebas Neue',sans-serif;
  font-size:3.5rem;
  color:rgba(232,80,0,0.06);
  line-height:1;letter-spacing:-0.02em;
  pointer-events:none;user-select:none;
}
/* entry animation */
.card{opacity:0;transform:translateY(16px);animation:card-in 0.6s ease-out forwards}
.card:nth-child(1){animation-delay:0.05s}
.card:nth-child(2){animation-delay:0.15s}
.card:nth-child(3){animation-delay:0.25s}
@keyframes card-in{to{opacity:1;transform:translateY(0)}}
@media(prefers-reduced-motion:reduce){.card{animation:none;opacity:1;transform:none}}
</style>
</head>
<body>
<div class="grid">
  <div class="card" id="c1">
    <span class="card-num">ROUTE ENGINE</span>
    <div class="card-title">下道専用ルート計算</div>
    <div class="card-desc">高速・自動車専用道を完全回避。OSRM cycling プロファイルで 50cc / 125cc どちらにも対応した安全ルートを自動生成します。</div>
    <div class="card-glyph">RT</div>
  </div>
  <div class="card" id="c2">
    <span class="card-num">STYLE SELECT</span>
    <div class="card-title">旅のスタイル選択</div>
    <div class="card-desc">風景派（自然・絶景）か人文派（博物館・史跡）か。好みに合わせて OpenStreetMap でスポットを自動選定します。</div>
    <div class="card-glyph">ST</div>
  </div>
  <div class="card" id="c3">
    <span class="card-num">TIMELINE</span>
    <div class="card-title">写真付きタイムライン</div>
    <div class="card-desc">Wikipedia 画像と公式サイトリンクをスポットごとに自動取得。滞在時間・累積距離もまとめて計算して出力します。</div>
    <div class="card-glyph">TL</div>
  </div>
</div>

<script>
// 3D tilt on mouse move
document.querySelectorAll('.card').forEach(card => {
  card.addEventListener('mousemove', e => {
    const r = card.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width;
    const y = (e.clientY - r.top) / r.height;
    const rotX = (y - 0.5) * -10;
    const rotY = (x - 0.5) * 12;
    card.style.transform = `perspective(600px) rotateX(${rotX}deg) rotateY(${rotY}deg) translateZ(4px)`;
    card.style.setProperty('--mx', `${x * 100}%`);
    card.style.setProperty('--my', `${y * 100}%`);
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = 'perspective(600px) rotateX(0) rotateY(0) translateZ(0)';
    card.style.transition = 'transform 0.5s cubic-bezier(0.16,1,0.3,1), border-color 0.3s';
  });
  card.addEventListener('mouseenter', () => {
    card.style.transition = 'transform 0.1s ease, border-color 0.3s';
  });
});
</script>
</body>
</html>
""", height=240, scrolling=False)


# ── サイドバー ─────────────────────────────────────────────────
with st.sidebar:
    origin      = st.text_input("出発地", value="東京都新宿区", placeholder="例: 東京都新宿区")
    destination = st.text_input("目的地", value="箱根町",       placeholder="例: 箱根町")

    c1, c2 = st.columns(2)
    with c1: start_time = st.text_input("出発", value="08:00")
    with c2: end_time   = st.text_input("帰着", value="17:00")

    st.markdown('<p class="sb-label">旅のスタイル</p>', unsafe_allow_html=True)
    engine_cc    = st.radio("排量",   ["125cc","50cc"],        label_visibility="collapsed", horizontal=True)
    travel_style = st.radio(
        "スタイル", ["お任せ","風景","人文"],
        label_visibility="collapsed", horizontal=True,
        help="風景=自然・絶景 / 人文=博物館・史跡 / お任せ=バランス",
    )

    st.markdown('<p class="sb-label">オプション</p>', unsafe_allow_html=True)
    want_meal = st.checkbox("飲食店をおすすめする", value=True)
    want_gas  = st.checkbox("ガソリンスタンドをおすすめする", value=True)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("プランを生成する", type="primary", use_container_width=True)


# ── 生成後の結果エリア ─────────────────────────────────────────
if run_btn:
    if not origin or not destination:
        st.error("出発地と目的地を入力してください")
        st.stop()

    loader_ph = st.empty()
    loader_ph.markdown("""
    <div class="moto-loader">
        <div class="moto-label">AI がルートを解析中... しばらくお待ちください</div>
        <div class="moto-track"></div>
        <div class="moto-bike">🏍️</div>
    </div>
    """, unsafe_allow_html=True)

    status_ph    = st.empty()
    log_messages = []
    def show_status(msg):
        log_messages.append(msg)
        status_ph.info("\n\n".join(log_messages[-4:]))

    try:
        result = run_agent(
            origin=origin, destination=destination,
            start_time=start_time, end_time=end_time,
            engine_cc=engine_cc, want_meal=want_meal, want_gas=want_gas,
            travel_style=travel_style, status_cb=show_status,
        )
    except Exception as e:
        loader_ph.empty(); status_ph.empty()
        st.error(f"エラー: {e}")
        st.stop()

    loader_ph.empty(); status_ph.empty()

    route    = result.get("route")         or {}
    budget   = result.get("time_budget")   or {}
    timeline = result.get("timeline")      or []
    geometry = result.get("geometry")      or []
    spots    = result.get("spots_for_map") or []

    # 結果ヘッダー
    dist_km  = route.get("distance_km","--")
    ride_min = budget.get("riding_min","--")
    n_spots  = budget.get("n_spots", 0)
    n_meals  = budget.get("n_meals", 0)

    # カウントアップ付き統計（JavaScript）
    components.html(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#050508;font-family:'Rajdhani',sans-serif;padding:0.5rem 0}}
.strip{{
  display:flex;
  border:1px solid rgba(232,80,0,0.18);
  border-radius:10px;overflow:hidden;
}}
.stat{{
  flex:1;padding:1rem 0.8rem 0.85rem;
  text-align:center;
  border-right:1px solid rgba(255,255,255,0.05);
}}
.stat:last-child{{border-right:none}}
.num{{
  font-family:'Bebas Neue',sans-serif;
  font-size:2.1rem;color:#E85000;line-height:1;
}}
.unit{{font-size:0.78rem;color:rgba(235,235,235,0.45);margin-left:2px}}
.lbl{{
  font-size:0.58rem;letter-spacing:0.22em;
  color:rgba(235,235,235,0.22);text-transform:uppercase;margin-top:0.2rem;
}}
</style>
</head>
<body>
<div class="strip">
  <div class="stat"><div class="num"><span id="n0">0</span><span class="unit">km</span></div><div class="lbl">走行距離</div></div>
  <div class="stat"><div class="num"><span id="n1">0</span><span class="unit">分</span></div><div class="lbl">移動時間</div></div>
  <div class="stat"><div class="num"><span id="n2">0</span><span class="unit">箇所</span></div><div class="lbl">観光スポット</div></div>
  <div class="stat"><div class="num"><span id="n3">0</span><span class="unit">回</span></div><div class="lbl">食事</div></div>
</div>
<script>
const targets = [{dist_km}, {ride_min}, {n_spots}, {n_meals}];
const els = [document.getElementById('n0'),document.getElementById('n1'),
             document.getElementById('n2'),document.getElementById('n3')];
const dur = 900;
const start = performance.now();
function tick(now) {{
  const p = Math.min((now - start) / dur, 1);
  const ease = 1 - Math.pow(1 - p, 3);
  els.forEach((el, i) => {{
    const t = targets[i];
    if (typeof t === 'number') {{
      el.textContent = (t % 1 !== 0) ? (t * ease).toFixed(1) : Math.round(t * ease);
    }} else {{
      el.textContent = t;
    }}
  }});
  if (p < 1) requestAnimationFrame(tick);
}}
requestAnimationFrame(tick);
</script>
</body>
</html>
""", height=90, scrolling=False)

    tab_tl, tab_map = st.tabs(["タイムライン", "ルート地図"])

    # ─── タイムライン ───
    with tab_tl:
        st.markdown("<br>", unsafe_allow_html=True)
        spot_lookup = {s["name"]: s for s in spots}
        CAT_ICON = {
            "museum":"🏛","viewpoint":"🌄","historic":"🏯","castle":"🏯",
            "ruins":"🏚","monument":"🗿","natural":"🌲","peak":"⛰",
            "waterfall":"💧","hot_spring":"♨","beach":"🏖","park":"🌿",
            "restaurant":"🍜","cafe":"☕","gas_station":"⛽",
            "attraction":"⭐","artwork":"🎨",
        }

        with st.spinner("スポット画像を取得中..."):
            thumbs = {}
            for s in spots:
                if s.get("category") not in ("gas_station","restaurant"):
                    thumbs[s["name"]] = fetch_wiki_thumb(s["name"])

        rows = ""
        cum_km = 0.0
        for entry in timeline:
            name     = entry.get("name","")
            arrive   = entry.get("arrive","")
            category = entry.get("category","")
            stay_min = entry.get("stay_min",0)
            dist_km_e = entry.get("dist_km",0)
            cum_km  += dist_km_e
            spot_data = spot_lookup.get(name, {})

            thumb = thumbs.get(name)
            img_cell = (
                f'<img class="spot-thumb" src="{thumb}" alt="{name}">'
                if thumb else
                f'<div class="spot-no-img">{CAT_ICON.get(category,"·")}</div>'
            )
            website  = spot_data.get("website","")
            link_url = website if website else \
                "https://www.google.com/search?q=" + urllib.parse.quote(name)

            rows += f"""
            <tr>
                <td><div class="spot-time">{arrive}</div></td>
                <td>{img_cell}</td>
                <td>
                    <a class="spot-link" href="{link_url}" target="_blank" rel="noopener">{name}</a>
                    <div class="spot-cat">{CAT_ICON.get(category,"")} {category}</div>
                </td>
                <td style="color:var(--text-muted);font-size:.83rem">{dist_km_e} km</td>
                <td class="spot-stay">{stay_min} 分</td>
                <td style="color:var(--text-dim);font-size:.8rem">{round(cum_km,1)} km</td>
            </tr>"""

        st.markdown(f"""
        <table class="spot-table">
            <thead><tr>
                <th>時刻</th><th>写真</th>
                <th>スポット名</th>
                <th>走行距離</th><th>滞在</th><th>累積</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <p style="margin-top:.5rem;font-size:.68rem;color:var(--text-dim);
                  font-family:'Noto Sans JP',sans-serif;">
            写真はWikipedia日本語版から取得。スポット名クリックで公式サイトまたはGoogle検索へ。
        </p>
        """, unsafe_allow_html=True)

        st.markdown("---")

        plan_text = result.get("plan_text","")
        lines, in_tl = [], False
        for line in plan_text.split("\n"):
            if line.startswith("## タイムライン"):
                in_tl = True
            elif line.startswith("## ") and in_tl:
                in_tl = False
            if not in_tl:
                lines.append(line)
        st.markdown("\n".join(lines))

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            "Markdownでダウンロード", plan_text,
            file_name="touring_plan.md", mime="text/markdown",
        )

    # ─── 地図 ───
    with tab_map:
        st.markdown("<br>", unsafe_allow_html=True)
        if geometry:
            clat = sum(c[1] for c in geometry) / len(geometry)
            clon = sum(c[0] for c in geometry) / len(geometry)
        else:
            clat, clon = 35.68, 139.76

        m = folium.Map(location=[clat,clon], zoom_start=10, tiles="CartoDB dark_matter")
        if geometry:
            rc = [[c[1],c[0]] for c in geometry]
            folium.PolyLine(rc, color="#E85000", weight=4, opacity=0.88).add_to(m)
            folium.Marker(rc[0],  popup=folium.Popup(f"<b>{origin}</b>",      max_width=200),
                          icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(m)
            folium.Marker(rc[-1], popup=folium.Popup(f"<b>{destination}</b>", max_width=200),
                          icon=folium.Icon(color="red",   icon="flag", prefix="fa")).add_to(m)
        for s in spots:
            fill = {"restaurant":"#F0A050","gas_station":"#888"}.get(s.get("category"),"#E85000")
            folium.CircleMarker(
                [s["lat"],s["lon"]], radius=8,
                color="#E85000", fill=True, fill_color=fill, fill_opacity=0.9,
                popup=folium.Popup(f"<b>{s['name']}</b>", max_width=200),
                tooltip=s["name"],
            ).add_to(m)

        st_folium(m, width="100%", height=520, returned_objects=[])
        st.markdown("""
        <div style="display:flex;gap:1.4rem;justify-content:center;margin-top:.7rem;
                    font-family:'Rajdhani',sans-serif;font-size:.83rem;color:rgba(235,235,235,0.35);">
            <span>出発地</span>
            <span>目的地</span>
            <span><span style="color:#E85000">●</span> 景点</span>
            <span><span style="color:#F0A050">●</span> 飲食店</span>
            <span><span style="color:#888">●</span> 給油</span>
        </div>""", unsafe_allow_html=True)
