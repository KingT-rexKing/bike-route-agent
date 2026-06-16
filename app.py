# =============================================
# app.py  ―  フロントエンド（UI）
# =============================================

import urllib.parse
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from agent import run_agent

# ── ページ基本設定 ────────────────────────────────────────────────
st.set_page_config(
    page_title="🏍️ バイクルートAI",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Wikipedia サムネイル取得 ─────────────────────────────────────
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


# ── CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;700&display=swap');

/* ── 余計なStreamlit UI非表示 ── */
#MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], footer { visibility:hidden !important; height:0 !important; }
h1 a, h2 a, h3 a { display:none !important; }

/* ── 全体を透明に ── */
body { background:#04040a !important; margin:0; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
section.main, .main {
    background: transparent !important;
    background-color: transparent !important;
}

/* ── サイドバー ── */
[data-testid="stSidebar"] {
    background: rgba(4,4,16,0.92) !important;
    border-right: 1px solid rgba(255,107,0,0.25) !important;
    backdrop-filter: blur(24px) saturate(1.5);
}
[data-testid="stSidebar"] > div { padding-top: 0.5rem; }

/* ── アニメーション ── */
@keyframes fade-in-up {
    from { opacity:0; transform:translateY(20px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes glow-pulse {
    0%,100% { opacity:0.6; }
    50%     { opacity:1; }
}
@keyframes btn-glow {
    0%,100% { box-shadow: 0 0 20px rgba(255,107,0,0.5), 0 4px 15px rgba(0,0,0,0.4); }
    50%     { box-shadow: 0 0 40px rgba(255,107,0,0.9), 0 4px 20px rgba(255,107,0,0.3); }
}
@keyframes moto-ride {
    0%   { left:-6%; }
    100% { left:106%; }
}
@keyframes road-dash {
    0%   { background-position:0 0; }
    100% { background-position:80px 0; }
}
@keyframes horizon-glow {
    0%,100% { opacity:0.4; }
    50%     { opacity:0.8; }
}

/* ── レイアウト ── */
.main .block-container { padding-top:0.5rem; max-width:1200px; }

/* ── ヒーローエリア ── */
.hero-wrap {
    text-align:center; padding:2.5rem 1rem 2rem;
    animation: fade-in-up 0.9s ease-out;
}
.hero-eyebrow {
    font-family:'Rajdhani',sans-serif;
    font-size:0.72rem; letter-spacing:0.35em; color:rgba(255,107,0,0.7);
    text-transform:uppercase; margin-bottom:0.6rem;
}
.hero-title {
    font-family:'Bebas Neue',sans-serif;
    font-size:clamp(3rem,8vw,5.5rem); letter-spacing:0.06em;
    line-height:1; margin:0;
    background: linear-gradient(160deg, #ffffff 0%, #FFB347 40%, #FF6B00 70%, #cc4400 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;
    filter: drop-shadow(0 0 30px rgba(255,107,0,0.4));
}
.hero-sub {
    font-family:'Rajdhani',sans-serif;
    font-size:1rem; color:rgba(255,255,255,0.45);
    letter-spacing:0.18em; margin-top:0.8rem; text-transform:uppercase;
}
.hero-line {
    width:120px; height:2px; margin:1rem auto 0;
    background:linear-gradient(90deg,transparent,#FF6B00,rgba(255,107,0,0.3),transparent);
    animation: glow-pulse 3s ease-in-out infinite;
}

/* ── サイドバーセクションタイトル ── */
.st-label {
    font-family:'Rajdhani',sans-serif; font-size:0.65rem;
    letter-spacing:0.3em; color:rgba(255,107,0,0.75);
    text-transform:uppercase; margin:1.1rem 0 0.3rem; padding-left:1px;
}

/* ── 入力 ── */
[data-testid="stTextInput"] input {
    background:rgba(255,255,255,0.05) !important;
    border:1px solid rgba(255,107,0,0.2) !important;
    border-radius:8px !important; color:#fff !important;
    font-family:'Noto Sans JP',sans-serif !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stTextInput"] input:focus {
    border-color:rgba(255,107,0,0.6) !important;
    box-shadow:0 0 0 3px rgba(255,107,0,0.12) !important;
    outline:none !important;
}
[data-testid="stTextInput"] label { color:rgba(255,255,255,0.55) !important; font-size:0.8rem !important; }
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label { color:rgba(255,255,255,0.75) !important; }

/* ── 生成ボタン ── */
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #FF6B00 0%, #cc3d00 100%) !important;
    border:none !important; border-radius:10px !important;
    font-family:'Rajdhani',sans-serif !important;
    font-size:1.05rem !important; font-weight:700 !important;
    letter-spacing:0.12em !important; color:#fff !important;
    padding:0.6rem 1rem !important;
    animation: btn-glow 2.5s ease-in-out infinite;
    transition: transform 0.1s !important;
}
[data-testid="stBaseButton-primary"]:hover { transform:translateY(-2px) !important; }
[data-testid="stBaseButton-secondary"] {
    background:rgba(255,255,255,0.05) !important;
    border:1px solid rgba(255,107,0,0.3) !important; border-radius:8px !important;
    color:rgba(255,255,255,0.75) !important;
    font-family:'Rajdhani',sans-serif !important; font-weight:600 !important;
}

/* ── KPIカード ── */
.kpi-card {
    background: linear-gradient(145deg, rgba(255,107,0,0.08), rgba(0,0,0,0.4));
    border:1px solid rgba(255,107,0,0.25);
    border-radius:14px; padding:1.3rem; text-align:center;
    backdrop-filter:blur(12px);
    transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
    animation: fade-in-up 0.5s ease-out;
    position:relative; overflow:hidden;
}
.kpi-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,transparent,#FF6B00,transparent);
}
.kpi-card:hover {
    transform:translateY(-4px);
    border-color:rgba(255,107,0,0.5);
    box-shadow:0 8px 30px rgba(255,107,0,0.15);
}
.kpi-icon  { font-size:1.4rem; margin-bottom:0.4rem; opacity:0.8; }
.kpi-label { font-family:'Rajdhani',sans-serif; font-size:0.65rem; letter-spacing:0.25em; color:rgba(255,255,255,0.4); text-transform:uppercase; margin-bottom:0.3rem; }
.kpi-value { font-family:'Bebas Neue',sans-serif; font-size:2.4rem; color:#FF6B00; line-height:1; }
.kpi-unit  { font-family:'Rajdhani',sans-serif; font-size:0.8rem; color:rgba(255,255,255,0.35); margin-top:0.15rem; }

/* ── タブ ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom:1px solid rgba(255,107,0,0.15) !important;
    gap:0.5rem;
}
[data-testid="stTabs"] [role="tab"] {
    font-family:'Rajdhani',sans-serif !important; font-size:0.95rem !important;
    font-weight:600 !important; color:rgba(255,255,255,0.45) !important;
    letter-spacing:0.05em !important; padding:0.5rem 1rem !important;
    border-radius:6px 6px 0 0 !important;
    transition:color 0.2s, background 0.2s !important;
}
[data-testid="stTabs"] [role="tab"]:hover { color:rgba(255,255,255,0.75) !important; background:rgba(255,107,0,0.06) !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color:#FF6B00 !important; border-bottom-color:#FF6B00 !important;
    background:rgba(255,107,0,0.08) !important;
}

/* ── Markdownコンテンツ ── */
[data-testid="stMarkdownContainer"] { color:rgba(255,255,255,0.82) !important; }
[data-testid="stMarkdownContainer"] h2 {
    font-family:'Rajdhani',sans-serif !important; font-size:1.3rem !important;
    color:#FF6B00 !important; letter-spacing:0.05em !important;
    border-bottom:1px solid rgba(255,107,0,0.2);
    padding-bottom:0.3rem; margin-top:1.5rem !important;
}
[data-testid="stMarkdownContainer"] table { width:100% !important; border-collapse:collapse !important; }
[data-testid="stMarkdownContainer"] th {
    background:rgba(255,107,0,0.12) !important; color:#FF6B00 !important;
    font-family:'Rajdhani',sans-serif !important; letter-spacing:0.05em !important;
    padding:0.6rem 0.8rem !important; border:1px solid rgba(255,107,0,0.15) !important;
}
[data-testid="stMarkdownContainer"] td {
    padding:0.55rem 0.8rem !important; border:1px solid rgba(255,255,255,0.06) !important;
    color:rgba(255,255,255,0.78) !important;
}
[data-testid="stMarkdownContainer"] tr:hover td { background:rgba(255,107,0,0.04) !important; }

/* ── バイク走行ローダー ── */
.moto-loader {
    position:relative; width:100%; height:88px; overflow:hidden;
    background:rgba(0,0,0,0.5); border-radius:14px;
    border:1px solid rgba(255,107,0,0.2);
    backdrop-filter:blur(10px); margin:1rem 0;
}
.moto-label {
    position:absolute; top:12px; left:0; right:0; text-align:center;
    font-family:'Rajdhani',sans-serif; font-size:0.88rem; letter-spacing:0.15em;
    color:rgba(255,255,255,0.6);
}
.moto-track {
    position:absolute; bottom:26px; left:0; right:0; height:3px;
    background:repeating-linear-gradient(90deg,rgba(255,107,0,0.7) 0,rgba(255,107,0,0.7) 22px,transparent 22px,transparent 44px);
    animation:road-dash .3s linear infinite;
}
.moto-bike {
    position:absolute; bottom:18px; font-size:1.9rem; line-height:1;
    filter:drop-shadow(0 0 12px rgba(255,107,0,1));
    animation:moto-ride 2.6s linear infinite;
}

/* ── スポットテーブル ── */
.spot-table { width:100%; border-collapse:collapse; }
.spot-table th {
    background:rgba(255,107,0,0.14); color:#FF6B00;
    font-family:'Rajdhani',sans-serif; letter-spacing:0.08em;
    padding:0.65rem 0.85rem; border-bottom:2px solid rgba(255,107,0,0.25);
    font-size:0.85rem; text-align:left; white-space:nowrap;
}
.spot-table td {
    padding:0.7rem 0.85rem; border-bottom:1px solid rgba(255,255,255,0.05);
    vertical-align:middle;
}
.spot-table tr:hover td { background:rgba(255,107,0,0.04); }
.spot-time { font-family:'Bebas Neue',sans-serif; font-size:1.1rem; color:#FFB347; white-space:nowrap; }
.spot-link { color:#FF6B00 !important; text-decoration:none; font-weight:700; font-family:'Noto Sans JP',sans-serif; font-size:0.88rem; }
.spot-link:hover { color:#FFD700 !important; text-decoration:underline; }
.spot-thumb { width:76px; height:54px; object-fit:cover; border-radius:6px; border:1px solid rgba(255,107,0,0.3); display:block; }
.spot-no-img { width:76px; height:54px; border-radius:6px; border:1px dashed rgba(255,107,0,0.2); background:rgba(255,107,0,0.04); display:flex; align-items:center; justify-content:center; font-size:1.3rem; }
.spot-cat  { font-size:0.7rem; color:rgba(255,255,255,0.38); margin-top:2px; }
.spot-stay { font-family:'Rajdhani',sans-serif; color:#FF6B00; font-weight:700; font-size:0.95rem; }

/* ── フィーチャーカード ── */
.feat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1.2rem; margin-top:0.5rem; }
.feat-card {
    background: linear-gradient(145deg, rgba(255,107,0,0.06), rgba(0,0,0,0.5));
    border:1px solid rgba(255,107,0,0.18);
    border-radius:16px; padding:1.6rem 1.4rem;
    backdrop-filter:blur(16px);
    transition: transform 0.25s, border-color 0.25s, box-shadow 0.25s;
    animation: fade-in-up 0.7s ease-out;
    position:relative; overflow:hidden;
}
.feat-card::after {
    content:''; position:absolute; bottom:0; left:0; right:0; height:1px;
    background:linear-gradient(90deg,transparent,rgba(255,107,0,0.4),transparent);
}
.feat-card:hover {
    transform:translateY(-5px);
    border-color:rgba(255,107,0,0.45);
    box-shadow:0 12px 40px rgba(255,107,0,0.12);
}
.feat-icon  { font-size:2.2rem; margin-bottom:0.8rem; }
.feat-title { font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#FF6B00; margin-bottom:0.5rem; letter-spacing:0.03em; }
.feat-desc  { font-family:'Noto Sans JP',sans-serif; font-size:0.8rem; color:rgba(255,255,255,0.48); line-height:1.7; }

/* ── CTA バナー ── */
.cta-banner {
    text-align:center; padding:1.5rem 2rem;
    background:linear-gradient(135deg,rgba(255,107,0,0.07),rgba(0,0,0,0.6));
    border:1px solid rgba(255,107,0,0.18); border-radius:14px;
    backdrop-filter:blur(12px); margin-top:1.2rem;
    animation: fade-in-up 0.9s ease-out;
}
.cta-text { font-family:'Rajdhani',sans-serif; font-size:1.05rem; color:rgba(255,255,255,0.55); letter-spacing:0.1em; }
.cta-highlight { color:#FF6B00; font-weight:700; }

/* ── スクロールバー ── */
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:rgba(0,0,0,0.3); }
::-webkit-scrollbar-thumb { background:rgba(255,107,0,0.35); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:rgba(255,107,0,0.6); }
hr { border-color:rgba(255,107,0,0.12) !important; margin:1.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── インラインSVG背景（外部リソース不要・常に表示） ────────────
st.markdown("""
<svg id="bg-svg"
     xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1920 1080"
     preserveAspectRatio="xMidYMid slice"
     style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:-2;pointer-events:none;">
  <defs>
    <linearGradient id="sky-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#02020c"/>
      <stop offset="55%"  stop-color="#0a0416"/>
      <stop offset="100%" stop-color="#130800"/>
    </linearGradient>
    <radialGradient id="horizon-glow" cx="50%" cy="57%" r="45%">
      <stop offset="0%"  stop-color="#FF6B00" stop-opacity="0.18"/>
      <stop offset="60%" stop-color="#FF3300" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="road-glow" cx="50%" cy="100%" r="55%">
      <stop offset="0%"  stop-color="#FF6B00" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    <filter id="blur-stars">
      <feGaussianBlur stdDeviation="0.8"/>
    </filter>
  </defs>

  <!-- 空のグラデーション -->
  <rect width="1920" height="1080" fill="url(#sky-grad)"/>

  <!-- ホライズングロー -->
  <rect width="1920" height="1080" fill="url(#horizon-glow)"/>

  <!-- 星々 -->
  <g filter="url(#blur-stars)" opacity="0.7">
    <circle cx="120"  cy="80"  r="1.2" fill="white" opacity="0.8"/>
    <circle cx="340"  cy="45"  r="0.9" fill="white" opacity="0.6"/>
    <circle cx="580"  cy="110" r="1.4" fill="white" opacity="0.9"/>
    <circle cx="820"  cy="60"  r="0.8" fill="white" opacity="0.5"/>
    <circle cx="1050" cy="90"  r="1.1" fill="white" opacity="0.7"/>
    <circle cx="1290" cy="40"  r="1.3" fill="white" opacity="0.85"/>
    <circle cx="1500" cy="120" r="0.9" fill="white" opacity="0.55"/>
    <circle cx="1740" cy="70"  r="1.2" fill="white" opacity="0.75"/>
    <circle cx="200"  cy="180" r="0.7" fill="white" opacity="0.45"/>
    <circle cx="460"  cy="220" r="1.0" fill="white" opacity="0.6"/>
    <circle cx="700"  cy="160" r="0.8" fill="white" opacity="0.5"/>
    <circle cx="960"  cy="200" r="1.2" fill="#FFB347" opacity="0.5"/>
    <circle cx="1180" cy="170" r="0.9" fill="white" opacity="0.65"/>
    <circle cx="1420" cy="210" r="1.1" fill="white" opacity="0.7"/>
    <circle cx="1660" cy="150" r="0.8" fill="white" opacity="0.5"/>
  </g>

  <!-- 遠景山脈 -->
  <polygon fill="#0c0c1e" opacity="0.95"
    points="0,480 120,380 250,410 380,340 510,375 650,310 790,355 920,290 1060,335 1200,275 1340,320 1470,265 1600,305 1730,250 1860,285 1920,260 1920,580 0,580"/>

  <!-- 近景山脈 -->
  <polygon fill="#08080f"
    points="0,540 90,480 190,505 310,455 440,488 570,445 690,472 810,428 930,462 1060,418 1190,455 1330,408 1460,445 1590,400 1720,435 1840,395 1920,415 1920,580 0,580"/>

  <!-- 地平線のグロー -->
  <rect y="574" width="1920" height="8" fill="#FF6B00" opacity="0.06"/>
  <rect y="578" width="1920" height="3" fill="#FF4400" opacity="0.12"/>

  <!-- 地面 -->
  <rect y="580" width="1920" height="500" fill="#050505"/>

  <!-- 道路グロー -->
  <rect y="580" width="1920" height="500" fill="url(#road-glow)"/>

  <!-- 道路面（パースペクティブ） -->
  <polygon fill="#0e0e0e"
    points="720,1080 850,580 1070,580 1200,1080"/>

  <!-- 道路の端ライン（左） -->
  <line x1="850" y1="580" x2="720"  y2="1080" stroke="rgba(255,255,255,0.1)" stroke-width="2.5"/>
  <!-- 道路の端ライン（右） -->
  <line x1="1070" y1="580" x2="1200" y2="1080" stroke="rgba(255,255,255,0.1)" stroke-width="2.5"/>

  <!-- センターライン（オレンジ） -->
  <line x1="960" y1="582" x2="960" y2="1080"
        stroke="#FF6B00" stroke-width="5"
        stroke-dasharray="55,38" opacity="0.45"/>

  <!-- 道路グロー（中央反射） -->
  <polygon fill="none" stroke="#FF6B00" stroke-width="1" opacity="0.08"
    points="940,1080 954,580 966,580 980,1080"/>
</svg>

<!-- 暗いオーバーレイ -->
<div style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;
            background:rgba(0,0,0,0.45);pointer-events:none;"></div>
""", unsafe_allow_html=True)


# ── ヒーローヘッダー ────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
  <div class="hero-eyebrow">🏍 Japan Touring Planner</div>
  <div class="hero-title">BIKE ROUTE AI</div>
  <div class="hero-line"></div>
  <div class="hero-sub">125cc / 50cc &nbsp;✦&nbsp; 下道専用 &nbsp;✦&nbsp; AI ツーリングプランナー</div>
</div>
""", unsafe_allow_html=True)


# ── サイドバー ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="st-label">📍 出発地 / 目的地</p>', unsafe_allow_html=True)
    origin      = st.text_input("出発地", value="東京都新宿区", label_visibility="collapsed", placeholder="例: 東京都新宿区")
    destination = st.text_input("目的地", value="箱根町",       label_visibility="collapsed", placeholder="例: 箱根町")

    st.markdown('<p class="st-label">🕐 出発 / 帰着</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: start_time = st.text_input("出発", value="08:00", label_visibility="collapsed")
    with c2: end_time   = st.text_input("帰着", value="17:00", label_visibility="collapsed")

    st.markdown('<p class="st-label">🔧 排量</p>', unsafe_allow_html=True)
    engine_cc = st.radio("排量", ["125cc","50cc"], label_visibility="collapsed", horizontal=True)

    st.markdown('<p class="st-label">🎯 旅のスタイル</p>', unsafe_allow_html=True)
    travel_style = st.radio(
        "スタイル", ["お任せ","風景","人文"], label_visibility="collapsed", horizontal=True,
        help="風景=自然・絶景 / 人文=博物館・史跡 / お任せ=バランス",
    )

    st.markdown('<p class="st-label">⚙️ オプション</p>', unsafe_allow_html=True)
    want_meal = st.checkbox("🍜 飲食店をおすすめする", value=True)
    want_gas  = st.checkbox("⛽ ガソリンスタンドをおすすめする", value=True)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("✦ プランを生成する", type="primary", use_container_width=True)


# ── メインエリア ──────────────────────────────────────────────────
if run_btn:
    if not origin or not destination:
        st.error("出発地と目的地を入力してください")
        st.stop()

    loader_ph = st.empty()
    loader_ph.markdown("""
    <div class="moto-loader">
        <div class="moto-label">⚡ AI がルートを解析中... しばらくお待ちください</div>
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

    route    = result.get("route")        or {}
    budget   = result.get("time_budget")  or {}
    timeline = result.get("timeline")     or []
    geometry = result.get("geometry")     or []
    spots    = result.get("spots_for_map") or []

    # ── KPIカード ──
    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(4)
    for col, (icon, label, val, unit) in zip(cols, [
        ("🛣️", "DISTANCE",    route.get("distance_km","—"), "km"),
        ("⏱️", "RIDING TIME", budget.get("riding_min","—"), "分"),
        ("🏯", "SPOTS",       budget.get("n_spots",0),      "箇所"),
        ("🍜", "MEALS",       budget.get("n_meals",0),      "回"),
    ]):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-unit">{unit}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_tl, tab_map = st.tabs(["📋 タイムライン", "🗺️ ルート地図"])

    # ─── タイムライン ───
    with tab_tl:
        st.markdown("<br>", unsafe_allow_html=True)
        spot_lookup = {s["name"]: s for s in spots}
        CAT_ICON = {
            "museum":"🏛️","viewpoint":"🌄","historic":"🏯","castle":"🏯",
            "ruins":"🏚️","monument":"🗿","natural":"🌲","peak":"⛰️",
            "waterfall":"💧","hot_spring":"♨️","beach":"🏖️","park":"🌿",
            "restaurant":"🍜","cafe":"☕","gas_station":"⛽",
            "attraction":"⭐","artwork":"🎨",
        }

        with st.spinner("📡 スポット画像を取得中..."):
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
            dist_km  = entry.get("dist_km",0)
            cum_km  += dist_km
            spot_data = spot_lookup.get(name, {})

            thumb = thumbs.get(name)
            img_cell = (f'<img class="spot-thumb" src="{thumb}" alt="{name}">'
                        if thumb else
                        f'<div class="spot-no-img">{CAT_ICON.get(category,"📍")}</div>')

            website  = spot_data.get("website","")
            link_url = website if website else \
                "https://www.google.com/search?q=" + urllib.parse.quote(name)

            rows += f"""
            <tr>
                <td><div class="spot-time">{arrive}</div></td>
                <td>{img_cell}</td>
                <td>
                    <a class="spot-link" href="{link_url}" target="_blank" rel="noopener">{name}</a>
                    <div class="spot-cat">{CAT_ICON.get(category,"📍")} {category}</div>
                </td>
                <td style="color:rgba(255,255,255,.55);font-size:.85rem">{dist_km} km</td>
                <td class="spot-stay">{stay_min} 分</td>
                <td style="color:rgba(255,255,255,.45);font-size:.82rem">{round(cum_km,1)} km</td>
            </tr>"""

        st.markdown(f"""
        <table class="spot-table">
            <thead><tr>
                <th>時刻</th><th>写真</th>
                <th>スポット名（クリックで詳細）</th>
                <th>走行距離</th><th>滞在</th><th>累積</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <p style="margin-top:.6rem;font-size:.7rem;color:rgba(255,255,255,.28);font-family:'Noto Sans JP',sans-serif;">
            ※ 写真はWikipedia日本語版から取得。名前クリックで公式サイトまたはGoogle検索へ。
        </p>
        """, unsafe_allow_html=True)

        st.markdown("---")

        plan_text = result.get("plan_text","")
        # 概要セクションのみ表示（タイムライン部分はHTMLテーブルで代替）
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
        st.download_button("📥 Markdownでダウンロード", plan_text,
                           file_name="touring_plan.md", mime="text/markdown")

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
            folium.PolyLine(rc, color="#FF6B00", weight=4, opacity=.85).add_to(m)
            folium.Marker(rc[0],  popup=folium.Popup(f"🚩 <b>{origin}</b>",      max_width=200), icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(m)
            folium.Marker(rc[-1], popup=folium.Popup(f"🏁 <b>{destination}</b>", max_width=200), icon=folium.Icon(color="red",   icon="flag", prefix="fa")).add_to(m)
        for s in spots:
            fill = {"restaurant":"#FFB347","gas_station":"#888"}.get(s.get("category"),"#FF6B00")
            folium.CircleMarker([s["lat"],s["lon"]], radius=8, color="#FF6B00",
                fill=True, fill_color=fill, fill_opacity=.9,
                popup=folium.Popup(f"<b>{s['name']}</b>", max_width=200),
                tooltip=s["name"]).add_to(m)

        st_folium(m, width="100%", height=520, returned_objects=[])
        st.markdown("""
        <div style="display:flex;gap:1.5rem;justify-content:center;margin-top:.8rem;
                    font-family:'Rajdhani',sans-serif;font-size:.85rem;color:rgba(255,255,255,.45);">
            <span>🟢 出発地</span><span>🔴 目的地</span>
            <span><span style="color:#FF6B00">●</span> 景点</span>
            <span><span style="color:#FFB347">●</span> 飲食店</span>
            <span><span style="color:#888">●</span> 給油</span>
        </div>""", unsafe_allow_html=True)

else:
    # ── デフォルト画面 ──
    st.markdown("""
    <div class="feat-grid">
        <div class="feat-card">
            <div class="feat-icon">🛣️</div>
            <div class="feat-title">下道限定ルート</div>
            <div class="feat-desc">高速・自動車専用道を完全回避。OSRM cycling プロファイルで50cc/125cc どちらにも対応した安全ルートを生成します。</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">🎯</div>
            <div class="feat-title">スタイル別おすすめ</div>
            <div class="feat-desc">風景派（自然・絶景）か人文派（博物館・史跡）か好みに合わせてスポットを自動選定。お任せはバランス型。</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">📸</div>
            <div class="feat-title">写真＆リンク付き</div>
            <div class="feat-desc">Wikipedia画像と公式サイトリンクをタイムラインに自動取得。そのままナビ代わりに使えます。</div>
        </div>
    </div>
    <div class="cta-banner" style="margin-top:1.4rem;">
        <div class="cta-text">
            👈 &nbsp;左のサイドバーで条件を設定して
            <span class="cta-highlight">✦ プランを生成する</span>
            を押してください
        </div>
    </div>
    """, unsafe_allow_html=True)
