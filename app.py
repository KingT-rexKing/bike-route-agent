# =============================================
# app.py  ―  フロントエンド（UI）
# =============================================

import urllib.parse
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from agent import run_agent

st.set_page_config(
    page_title="バイクルートAI",
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
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@500;600;700&family=Noto+Sans+JP:wght@400;700&display=swap');

/* Streamlit chrome 非表示 */
#MainMenu,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],footer{visibility:hidden!important;height:0!important}
h1 a,h2 a,h3 a{display:none!important}

/* デザイントークン */
:root{
  --bg:#050508;
  --surface:#0c0c12;
  --surface-hi:#131319;
  --accent:#E85000;
  --accent-dim:rgba(232,80,0,0.15);
  --accent-glow:rgba(232,80,0,0.22);
  --text:#ebebeb;
  --text-muted:rgba(235,235,235,0.45);
  --text-dim:rgba(235,235,235,0.22);
  --border:rgba(232,80,0,0.18);
  --border-sub:rgba(255,255,255,0.05);
}

body{background:var(--bg)!important;margin:0}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"],
section.main,.main{background:transparent!important;background-color:transparent!important}

/* サイドバー */
[data-testid="stSidebar"]{
  background:rgba(5,5,10,0.96)!important;
  border-right:1px solid var(--border)!important;
}
[data-testid="stSidebar"]>div{padding-top:1rem}

/* アニメーション */
@keyframes fade-up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@keyframes moto-ride{0%{left:-8%}100%{left:108%}}
@keyframes dash-flow{0%{background-position:0 0}100%{background-position:54px 0}}
@keyframes subtle-pulse{0%,100%{opacity:.45}50%{opacity:.75}}

/* レイアウト */
.main .block-container{padding-top:0.5rem;max-width:1200px}

/* ヒーロー */
.hero-wrap{padding:2.2rem 0 1.6rem;animation:fade-up 0.7s ease-out}
.hero-title{
  font-family:'Bebas Neue',sans-serif;
  font-size:clamp(3rem,7vw,5rem);
  letter-spacing:0.05em;line-height:1;
  color:var(--text);margin:0;
}
.hero-title .hero-accent{color:var(--accent)}
.hero-sub{
  font-family:'Rajdhani',sans-serif;
  font-size:0.92rem;color:var(--text-muted);
  margin-top:0.55rem;letter-spacing:0.14em;
}

/* サイドバーラベル */
.sb-label{
  font-family:'Rajdhani',sans-serif;
  font-size:0.66rem;letter-spacing:0.28em;
  color:rgba(232,80,0,0.58);
  text-transform:uppercase;
  margin:1.2rem 0 0.3rem;
}

/* 入力フィールド */
[data-testid="stTextInput"] input{
  background:rgba(255,255,255,0.04)!important;
  border:1px solid var(--border)!important;
  border-radius:6px!important;
  color:var(--text)!important;
  font-family:'Noto Sans JP',sans-serif!important;
  transition:border-color 0.2s,box-shadow 0.2s;
}
[data-testid="stTextInput"] input:focus{
  border-color:rgba(232,80,0,0.5)!important;
  box-shadow:0 0 0 3px rgba(232,80,0,0.1)!important;
  outline:none!important;
}
[data-testid="stTextInput"] label{color:var(--text-muted)!important;font-size:0.8rem!important}
[data-testid="stRadio"] label,[data-testid="stCheckbox"] label{
  color:rgba(235,235,235,0.72)!important;
}

/* ボタン（hover時のみエフェクト） */
[data-testid="stBaseButton-primary"]{
  background:#E85000!important;
  border:none!important;border-radius:7px!important;
  font-family:'Rajdhani',sans-serif!important;
  font-size:1rem!important;font-weight:700!important;
  letter-spacing:0.1em!important;color:#fff!important;
  padding:0.6rem 1rem!important;
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

/* 統計ストリップ（KPIカードの代わり） */
.stats-strip{
  display:flex;
  border:1px solid var(--border);border-radius:10px;
  overflow:hidden;
  animation:fade-up 0.5s ease-out;
  margin-bottom:1.4rem;
}
.stat-item{
  flex:1;padding:1.1rem 0.8rem 0.9rem;
  text-align:center;
  border-right:1px solid var(--border-sub);
}
.stat-item:last-child{border-right:none}
.stat-num{
  font-family:'Bebas Neue',sans-serif;
  font-size:2.1rem;color:var(--accent);line-height:1;
}
.stat-unit{
  font-family:'Rajdhani',sans-serif;
  font-size:0.78rem;color:var(--text-muted);margin-left:2px;
}
.stat-label{
  font-family:'Rajdhani',sans-serif;
  font-size:0.6rem;letter-spacing:0.22em;
  color:var(--text-dim);text-transform:uppercase;
  margin-top:0.22rem;
}

/* タブ */
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
[data-testid="stTabs"] [role="tab"]:hover{
  color:var(--text)!important;background:rgba(232,80,0,0.05)!important
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{
  color:var(--accent)!important;background:rgba(232,80,0,0.07)!important
}

/* Markdown */
[data-testid="stMarkdownContainer"]{color:rgba(235,235,235,0.8)!important}
[data-testid="stMarkdownContainer"] h2{
  font-family:'Rajdhani',sans-serif!important;font-size:1.2rem!important;
  color:var(--accent)!important;letter-spacing:0.04em!important;
  border-bottom:1px solid var(--border);
  padding-bottom:0.3rem;margin-top:1.5rem!important;
}
[data-testid="stMarkdownContainer"] table{width:100%!important;border-collapse:collapse!important}
[data-testid="stMarkdownContainer"] th{
  background:rgba(232,80,0,0.09)!important;color:var(--accent)!important;
  font-family:'Rajdhani',sans-serif!important;letter-spacing:0.05em!important;
  padding:0.6rem 0.8rem!important;border:1px solid var(--border)!important;
}
[data-testid="stMarkdownContainer"] td{
  padding:0.55rem 0.8rem!important;border:1px solid var(--border-sub)!important;
  color:rgba(235,235,235,0.75)!important;
}
[data-testid="stMarkdownContainer"] tr:hover td{background:rgba(232,80,0,0.04)!important}

/* ローディングバー */
.moto-loader{
  position:relative;width:100%;height:76px;overflow:hidden;
  background:var(--surface);border-radius:10px;
  border:1px solid var(--border);margin:1rem 0;
}
.moto-label{
  position:absolute;top:10px;left:0;right:0;text-align:center;
  font-family:'Rajdhani',sans-serif;font-size:0.84rem;letter-spacing:0.12em;
  color:var(--text-muted);
}
.moto-track{
  position:absolute;bottom:23px;left:0;right:0;height:2px;
  background:repeating-linear-gradient(
    90deg,rgba(232,80,0,0.55) 0,rgba(232,80,0,0.55) 16px,transparent 16px,transparent 32px
  );
  animation:dash-flow .3s linear infinite;
}
.moto-bike{
  position:absolute;bottom:15px;font-size:1.6rem;line-height:1;
  filter:drop-shadow(0 0 7px rgba(232,80,0,0.85));
  animation:moto-ride 2.4s linear infinite;
}

/* スポットテーブル */
.spot-table{width:100%;border-collapse:collapse}
.spot-table th{
  background:rgba(232,80,0,0.09);color:var(--accent);
  font-family:'Rajdhani',sans-serif;letter-spacing:0.07em;
  padding:0.6rem 0.8rem;border-bottom:1px solid var(--border);
  font-size:0.8rem;text-align:left;white-space:nowrap;
}
.spot-table td{
  padding:0.65rem 0.8rem;border-bottom:1px solid var(--border-sub);
  vertical-align:middle;
}
.spot-table tr:hover td{background:rgba(232,80,0,0.04)}
.spot-time{font-family:'Bebas Neue',sans-serif;font-size:1rem;color:#F09060;white-space:nowrap}
.spot-link{color:var(--accent)!important;text-decoration:none;font-weight:600;font-size:0.88rem}
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
.spot-stay{font-family:'Rajdhani',sans-serif;color:var(--accent);font-weight:700;font-size:0.9rem}

/* ベントーグリッド（機能紹介） */
.bento-grid{
  display:grid;
  grid-template-columns:1.55fr 1fr;
  grid-template-rows:1fr 1fr;
  gap:0.7rem;
  margin-top:0.5rem;
}
.bento-main{
  grid-row:span 2;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:14px;padding:2rem 1.8rem;
  position:relative;overflow:hidden;
  animation:fade-up 0.6s ease-out;
}
.bento-main::after{
  content:'';position:absolute;
  bottom:-40px;right:-40px;
  width:200px;height:200px;
  background:radial-gradient(circle,rgba(232,80,0,0.1) 0%,transparent 70%);
  pointer-events:none;
}
.bento-b{
  background:var(--surface-hi);
  border:1px solid var(--border-sub);
  border-radius:14px;padding:1.4rem 1.3rem;
  animation:fade-up 0.75s ease-out;
}
.bento-tag{
  font-family:'Bebas Neue',sans-serif;font-size:0.85rem;
  letter-spacing:0.12em;color:var(--accent);
  margin-bottom:0.6rem;display:block;
}
.bento-title{
  font-family:'Rajdhani',sans-serif;font-size:1.15rem;
  font-weight:700;color:var(--text);margin-bottom:0.5rem;
}
.bento-desc{
  font-family:'Noto Sans JP',sans-serif;font-size:0.79rem;
  color:var(--text-muted);line-height:1.8;
}
.bento-metric{
  font-family:'Bebas Neue',sans-serif;font-size:3.2rem;
  color:var(--accent);line-height:1;margin-bottom:0.4rem;
}
.bento-metric-label{
  font-family:'Rajdhani',sans-serif;font-size:0.72rem;
  color:var(--text-dim);letter-spacing:0.18em;text-transform:uppercase;
}

/* ベントーステップリスト */
.bento-step{display:flex;align-items:center;gap:0.65rem}
.bento-step-n{
  font-family:'Bebas Neue',sans-serif;font-size:0.88rem;
  color:var(--accent);letter-spacing:0.08em;
  min-width:22px;
}
.bento-step-t{
  font-family:'Noto Sans JP',sans-serif;font-size:0.77rem;
  color:var(--text-muted);
}

/* CTAヒント */
.cta-hint{
  margin-top:1.1rem;
  padding:1rem 1.3rem;
  border:1px solid var(--border-sub);
  border-radius:9px;
  display:flex;align-items:center;gap:0.6rem;
}
.cta-arrow{font-size:1.1rem}
.cta-text{
  font-family:'Rajdhani',sans-serif;
  font-size:0.9rem;letter-spacing:0.06em;
  color:var(--text-muted);
}
.cta-strong{color:var(--text);font-weight:700}

/* スクロールバー */
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(232,80,0,0.28);border-radius:2px}
::-webkit-scrollbar-thumb:hover{background:rgba(232,80,0,0.52)}
hr{border-color:var(--border-sub)!important;margin:1.4rem 0!important}

/* Streamlit info/警告メッセージ */
[data-testid="stAlert"]{
  background:var(--surface)!important;border:1px solid var(--border-sub)!important;
  border-radius:8px!important;
}
</style>
""", unsafe_allow_html=True)


# ── 背景SVG（道路シーン） ──────────────────────────────────────
st.markdown("""
<svg id="bg-svg"
     xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1920 1080"
     preserveAspectRatio="xMidYMid slice"
     style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:-2;pointer-events:none;">
  <defs>
    <linearGradient id="sky-g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#020205"/>
      <stop offset="50%"  stop-color="#08041a"/>
      <stop offset="100%" stop-color="#100600"/>
    </linearGradient>
    <radialGradient id="hz-glow" cx="50%" cy="56%" r="42%">
      <stop offset="0%"  stop-color="#E85000" stop-opacity="0.16"/>
      <stop offset="60%" stop-color="#E85000" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="road-glow" cx="50%" cy="100%" r="50%">
      <stop offset="0%"  stop-color="#E85000" stop-opacity="0.1"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
    <filter id="sf"><feGaussianBlur stdDeviation="0.7"/></filter>
  </defs>

  <rect width="1920" height="1080" fill="url(#sky-g)"/>
  <rect width="1920" height="1080" fill="url(#hz-glow)"/>

  <!-- 星 -->
  <g filter="url(#sf)" opacity="0.65">
    <circle cx="110"  cy="75"  r="1.1" fill="white" opacity="0.75"/>
    <circle cx="330"  cy="42"  r="0.9" fill="white" opacity="0.55"/>
    <circle cx="570"  cy="105" r="1.3" fill="white" opacity="0.85"/>
    <circle cx="810"  cy="58"  r="0.8" fill="white" opacity="0.5"/>
    <circle cx="1040" cy="88"  r="1.0" fill="white" opacity="0.7"/>
    <circle cx="1280" cy="38"  r="1.2" fill="white" opacity="0.8"/>
    <circle cx="1490" cy="115" r="0.9" fill="white" opacity="0.5"/>
    <circle cx="1730" cy="65"  r="1.1" fill="white" opacity="0.7"/>
    <circle cx="190"  cy="175" r="0.7" fill="white" opacity="0.4"/>
    <circle cx="450"  cy="215" r="0.9" fill="white" opacity="0.55"/>
    <circle cx="690"  cy="155" r="0.8" fill="white" opacity="0.45"/>
    <circle cx="950"  cy="195" r="1.1" fill="#FFB060" opacity="0.4"/>
    <circle cx="1170" cy="165" r="0.8" fill="white" opacity="0.6"/>
    <circle cx="1410" cy="205" r="1.0" fill="white" opacity="0.65"/>
    <circle cx="1650" cy="145" r="0.7" fill="white" opacity="0.45"/>
  </g>

  <!-- 遠景山脈 -->
  <polygon fill="#0a0a1c" opacity="0.9"
    points="0,488 130,385 255,415 385,342 515,378 655,314 795,358 930,292 1065,338 1205,278 1345,322 1475,268 1605,308 1735,252 1865,288 1920,264 1920,588 0,588"/>

  <!-- 近景山脈 -->
  <polygon fill="#070710"
    points="0,545 95,482 195,508 318,458 445,490 575,448 698,474 818,430 938,464 1065,420 1195,458 1335,410 1462,448 1592,402 1724,438 1845,398 1920,418 1920,588 0,588"/>

  <!-- 地平線 -->
  <rect y="582" width="1920" height="6" fill="#E85000" opacity="0.05"/>
  <rect y="586" width="1920" height="2" fill="#CC4400" opacity="0.1"/>

  <!-- 地面 -->
  <rect y="588" width="1920" height="492" fill="#040404"/>
  <rect y="588" width="1920" height="492" fill="url(#road-glow)"/>

  <!-- 道路（パース） -->
  <polygon fill="#0d0d0d"
    points="728,1080 855,588 1065,588 1192,1080"/>
  <line x1="855"  y1="588" x2="728"  y2="1080" stroke="rgba(255,255,255,0.08)" stroke-width="2"/>
  <line x1="1065" y1="588" x2="1192" y2="1080" stroke="rgba(255,255,255,0.08)" stroke-width="2"/>

  <!-- センターライン -->
  <line x1="960" y1="590" x2="960" y2="1080"
        stroke="#E85000" stroke-width="4"
        stroke-dasharray="50,35" opacity="0.38"/>
</svg>

<div style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;
            background:rgba(0,0,0,0.48);pointer-events:none;"></div>
""", unsafe_allow_html=True)


# ── ヒーロー ──────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
  <div class="hero-title">BIKE ROUTE <span class="hero-accent">AI</span></div>
  <div class="hero-sub">125cc / 50cc &nbsp;·&nbsp; 下道専用 &nbsp;·&nbsp; Japan Touring Planner</div>
</div>
""", unsafe_allow_html=True)


# ── サイドバー ────────────────────────────────────────────────────
with st.sidebar:
    origin      = st.text_input("出発地", value="東京都新宿区", placeholder="例: 東京都新宿区")
    destination = st.text_input("目的地", value="箱根町",       placeholder="例: 箱根町")

    c1, c2 = st.columns(2)
    with c1: start_time = st.text_input("出発時刻", value="08:00")
    with c2: end_time   = st.text_input("帰着目標", value="17:00")

    st.markdown('<p class="sb-label">旅のスタイル</p>', unsafe_allow_html=True)
    engine_cc = st.radio("排量", ["125cc","50cc"], label_visibility="collapsed", horizontal=True)
    travel_style = st.radio(
        "スタイル", ["お任せ","風景","人文"], label_visibility="collapsed", horizontal=True,
        help="風景=自然・絶景 / 人文=博物館・史跡 / お任せ=バランス",
    )

    st.markdown('<p class="sb-label">オプション</p>', unsafe_allow_html=True)
    want_meal = st.checkbox("飲食店をおすすめする", value=True)
    want_gas  = st.checkbox("ガソリンスタンドをおすすめする", value=True)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("プランを生成する", type="primary", use_container_width=True)


# ── メインエリア ──────────────────────────────────────────────────
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

    # ── 統計ストリップ ──
    st.markdown(f"""
    <div class="stats-strip">
      <div class="stat-item">
        <div class="stat-num">{route.get("distance_km","--")}<span class="stat-unit">km</span></div>
        <div class="stat-label">走行距離</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{budget.get("riding_min","--")}<span class="stat-unit">分</span></div>
        <div class="stat-label">移動時間</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{budget.get("n_spots",0)}<span class="stat-unit">箇所</span></div>
        <div class="stat-label">観光スポット</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{budget.get("n_meals",0)}<span class="stat-unit">回</span></div>
        <div class="stat-label">食事</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

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
            dist_km  = entry.get("dist_km",0)
            cum_km  += dist_km
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
                <td style="color:var(--text-muted);font-size:.83rem">{dist_km} km</td>
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
        # タイムラインセクションはHTMLテーブルで表示済みなので除外
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
                    font-family:'Rajdhani',sans-serif;font-size:.83rem;color:var(--text-dim);">
            <span style="color:rgba(235,235,235,0.5)">● 出発地</span>
            <span style="color:rgba(235,235,235,0.5)">● 目的地</span>
            <span><span style="color:#E85000">●</span> 景点</span>
            <span><span style="color:#F0A050">●</span> 飲食店</span>
            <span><span style="color:#888">●</span> 給油</span>
        </div>""", unsafe_allow_html=True)

else:
    # ── デフォルト画面（機能説明ベントー） ──
    st.markdown("""
    <div class="bento-grid">
        <div class="bento-main">
            <div class="bento-title" style="font-size:1.3rem;margin-bottom:0.7rem">
                AI が自動生成する下道ツーリングプラン
            </div>
            <div class="bento-desc" style="margin-bottom:1.6rem">
                高速道路・自動車専用道を完全回避。OSRM cycling プロファイルで
                50cc・125cc どちらにも対応した安全なルートを算出し、
                沿道の観光スポット・飲食店・給油場所を自動でタイムラインに組み込みます。
            </div>
            <div style="display:flex;flex-direction:column;gap:0.55rem">
                <div class="bento-step"><span class="bento-step-n">01</span><span class="bento-step-t">地名 → GPS座標（Nominatim）</span></div>
                <div class="bento-step"><span class="bento-step-n">02</span><span class="bento-step-t">下道ルート計算（OSRM）</span></div>
                <div class="bento-step"><span class="bento-step-n">03</span><span class="bento-step-t">時間配分・スポット数計算</span></div>
                <div class="bento-step"><span class="bento-step-n">04</span><span class="bento-step-t">沿道POI検索（OpenStreetMap）</span></div>
                <div class="bento-step"><span class="bento-step-n">05</span><span class="bento-step-t">AI プラン文書生成（Claude）</span></div>
            </div>
        </div>
        <div class="bento-b">
            <span class="bento-tag">旅のスタイル</span>
            <div class="bento-title">風景 / 人文 / お任せ</div>
            <div class="bento-desc">自然・絶景スポット優先か、博物館・史跡優先か。好みに合わせてスポット選定を変更します。</div>
        </div>
        <div class="bento-b">
            <span class="bento-tag">写真 + リンク付き</span>
            <div class="bento-title">Wikipedia 画像 & 公式サイト</div>
            <div class="bento-desc">タイムライン各スポットにサムネイルとリンクを自動取得。そのままナビ代わりに。</div>
        </div>
    </div>
    <div class="cta-hint">
        <span class="cta-arrow">←</span>
        <span class="cta-text">左のサイドバーで条件を設定して
        <span class="cta-strong">「プランを生成する」</span>
        を押してください</span>
    </div>
    """, unsafe_allow_html=True)
