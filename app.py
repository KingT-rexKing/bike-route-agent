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


# ── CSS（レイアウト・スタイル） ─────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;600;700&family=Noto+Sans+JP:wght@400;700&display=swap');

/* ── Streamlitの余計なUI要素を非表示 ── */
#MainMenu, [data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
footer { visibility: hidden !important; height: 0 !important; }

/* ── 見出しのアンカーリンクを非表示 ── */
h1 a, h2 a, h3 a,
[data-testid="stMarkdownContainer"] h2 a { display: none !important; }

/* ── 背景スライドショー（CSSアニメーション） ── */
@keyframes fade-slide {
    0%, 100% { opacity: 0; }
    8%, 20%  { opacity: 1; }
    25%      { opacity: 0; }
}
.bg-slide {
    position: fixed !important;
    top: 0; left: 0; right: 0; bottom: 0;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    opacity: 0;
    z-index: -2;
    pointer-events: none;
    animation: fade-slide 24s infinite both;
}
.bg-slide:nth-child(1) { animation-delay:  0s; }
.bg-slide:nth-child(2) { animation-delay:  6s; }
.bg-slide:nth-child(3) { animation-delay: 12s; }
.bg-slide:nth-child(4) { animation-delay: 18s; }
.bg-overlay {
    position: fixed !important;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.62);
    z-index: -1;
    pointer-events: none;
}

/* ── 全体背景を透明に（スライドショーを見せる） ── */
body { background: #0a0a0a !important; }
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
section.main, .main {
    background: transparent !important;
    background-color: transparent !important;
}
[data-testid="stSidebar"] {
    background: rgba(8,8,8,0.90) !important;
    border-right: 1px solid rgba(255,107,0,0.3) !important;
    backdrop-filter: blur(16px);
}

/* ── アニメーション ── */
@keyframes fade-in {
    from { opacity:0; transform:translateY(14px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes pulse-glow {
    0%,100% { box-shadow:0 0 18px rgba(255,107,0,0.4); }
    50%      { box-shadow:0 0 40px rgba(255,107,0,0.9),0 0 60px rgba(255,107,0,0.3); }
}
@keyframes moto-ride {
    0%   { left: -6%; }
    100% { left: 104%; }
}
@keyframes road-dash {
    0%   { background-position:0 0; }
    100% { background-position:80px 0; }
}

/* ── レイアウト ── */
.main .block-container { padding-top:1rem; max-width:1200px; }

/* ── ヒーローヘッダー ── */
.hero-header { text-align:center; padding:2.2rem 1rem 1.8rem; animation:fade-in .8s ease-out; }
.hero-title {
    font-family:'Bebas Neue',sans-serif;
    font-size:clamp(2.8rem,7vw,5rem); letter-spacing:.08em;
    background:linear-gradient(135deg,#FF6B00,#FFB347,#FF6B00);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; margin:0; line-height:1;
}
.hero-sub {
    font-family:'Rajdhani','Noto Sans JP',sans-serif;
    font-size:.95rem; color:rgba(255,255,255,.55);
    letter-spacing:.2em; margin-top:.5rem; text-transform:uppercase;
}
.hero-divider {
    width:80px; height:3px;
    background:linear-gradient(90deg,transparent,#FF6B00,transparent);
    margin:.8rem auto 0; border-radius:2px;
}
.road-lines { display:flex; justify-content:center; gap:8px; margin:.6rem 0; }
.road-line  { width:40px; height:4px; background:#FF6B00; border-radius:2px; opacity:.7; }
.road-line:nth-child(2) { opacity:.4; width:22px; }
.road-line:nth-child(3) { opacity:.2; width:10px; }

/* ── サイドバーラベル ── */
.sidebar-title {
    font-family:'Rajdhani',sans-serif; font-size:.68rem;
    letter-spacing:.25em; color:#FF6B00; text-transform:uppercase; margin:1.2rem 0 .4rem;
}

/* ── 入力・ラジオ・チェック ── */
[data-testid="stTextInput"] input {
    background:rgba(255,255,255,.06) !important;
    border:1px solid rgba(255,107,0,.25) !important;
    border-radius:8px !important; color:#fff !important;
}
[data-testid="stTextInput"] input:focus {
    border-color:rgba(255,107,0,.7) !important;
    box-shadow:0 0 0 2px rgba(255,107,0,.15) !important;
}
[data-testid="stTextInput"] label { color:rgba(255,255,255,.65) !important; }
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label { color:rgba(255,255,255,.8) !important; }

/* ── ボタン ── */
[data-testid="stBaseButton-primary"] {
    background:linear-gradient(135deg,#FF6B00,#e55a00) !important;
    border:none !important; border-radius:10px !important;
    font-family:'Rajdhani',sans-serif !important;
    font-size:1.1rem !important; font-weight:700 !important;
    letter-spacing:.1em !important; color:#fff !important;
    animation:pulse-glow 2.5s ease-in-out infinite;
}
[data-testid="stBaseButton-secondary"] {
    background:rgba(255,255,255,.06) !important;
    border:1px solid rgba(255,107,0,.3) !important;
    border-radius:8px !important; color:rgba(255,255,255,.8) !important;
    font-family:'Rajdhani',sans-serif !important; font-weight:600 !important;
}

/* ── KPIカード ── */
.kpi-card {
    background:rgba(0,0,0,.55); border:1px solid rgba(255,107,0,.22);
    border-radius:12px; padding:1.2rem 1.5rem; text-align:center;
    backdrop-filter:blur(8px); transition:border-color .2s,transform .2s;
    animation:fade-in .6s ease-out;
}
.kpi-card:hover { border-color:rgba(255,107,0,.5); transform:translateY(-3px); }
.kpi-label { font-family:'Rajdhani',sans-serif; font-size:.68rem; letter-spacing:.2em; color:rgba(255,255,255,.45); text-transform:uppercase; margin-bottom:.3rem; }
.kpi-value { font-family:'Bebas Neue',sans-serif; font-size:2.2rem; color:#FF6B00; line-height:1; }
.kpi-unit  { font-family:'Rajdhani',sans-serif; font-size:.85rem; color:rgba(255,255,255,.4); margin-top:.2rem; }

/* ── タブ ── */
[data-testid="stTabs"] [role="tab"] {
    font-family:'Rajdhani',sans-serif !important; font-size:1rem !important;
    font-weight:600 !important; color:rgba(255,255,255,.55) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color:#FF6B00 !important; border-bottom-color:#FF6B00 !important;
}

/* ── AIテキスト（Markdown） ── */
[data-testid="stMarkdownContainer"] { color:rgba(255,255,255,.85) !important; }
[data-testid="stMarkdownContainer"] h2 {
    color:#FF6B00 !important; font-family:'Rajdhani',sans-serif !important;
    font-size:1.35rem !important; border-bottom:1px solid rgba(255,107,0,.2);
    padding-bottom:.3rem; margin-top:1.5rem !important;
}
[data-testid="stMarkdownContainer"] table { background:rgba(255,255,255,.03) !important; border-collapse:collapse !important; width:100% !important; }
[data-testid="stMarkdownContainer"] th { background:rgba(255,107,0,.15) !important; color:#FF6B00 !important; font-family:'Rajdhani',sans-serif !important; padding:.7rem 1rem !important; border:1px solid rgba(255,107,0,.15) !important; }
[data-testid="stMarkdownContainer"] td { padding:.6rem 1rem !important; border:1px solid rgba(255,255,255,.06) !important; color:rgba(255,255,255,.8) !important; }
[data-testid="stMarkdownContainer"] tr:hover td { background:rgba(255,107,0,.05) !important; }

/* ── バイク走行ローダー ── */
.moto-loader {
    position:relative; width:100%; height:92px; overflow:hidden;
    background:rgba(0,0,0,.5); border-radius:14px;
    border:1px solid rgba(255,107,0,.2); backdrop-filter:blur(8px); margin:1rem 0;
}
.moto-label {
    position:absolute; top:13px; left:0; right:0; text-align:center;
    font-family:'Rajdhani',sans-serif; font-size:.92rem; letter-spacing:.15em;
    color:rgba(255,255,255,.65);
}
.moto-track {
    position:absolute; bottom:28px; left:0; right:0; height:3px;
    background:repeating-linear-gradient(90deg,rgba(255,107,0,.7) 0px,rgba(255,107,0,.7) 24px,transparent 24px,transparent 48px);
    animation:road-dash .35s linear infinite;
}
.moto-bike {
    position:absolute; bottom:20px; font-size:2rem; line-height:1;
    filter:drop-shadow(0 0 10px rgba(255,107,0,.9));
    animation:moto-ride 2.8s linear infinite;
}

/* ── 写真付きタイムラインテーブル ── */
.spot-table { width:100%; border-collapse:collapse; }
.spot-table th {
    background:rgba(255,107,0,.18); color:#FF6B00;
    font-family:'Rajdhani',sans-serif; letter-spacing:.08em;
    padding:.7rem .9rem; border-bottom:1px solid rgba(255,107,0,.2);
    font-size:.9rem; text-align:left;
}
.spot-table td {
    padding:.65rem .9rem; border-bottom:1px solid rgba(255,255,255,.06);
    color:rgba(255,255,255,.82); vertical-align:middle;
}
.spot-table tr:hover td { background:rgba(255,107,0,.05); }
.spot-time { font-family:'Bebas Neue',sans-serif; font-size:1.05rem; color:#FFB347; white-space:nowrap; }
.spot-link {
    color:#FF6B00 !important; text-decoration:none; font-weight:700;
    font-family:'Noto Sans JP',sans-serif; font-size:.9rem;
}
.spot-link:hover { text-decoration:underline; color:#FFB347 !important; }
.spot-thumb { width:80px; height:56px; object-fit:cover; border-radius:6px; border:1px solid rgba(255,107,0,.3); display:block; }
.spot-no-img {
    width:80px; height:56px; border-radius:6px;
    border:1px dashed rgba(255,107,0,.25);
    background:rgba(255,107,0,.05); display:flex;
    align-items:center; justify-content:center;
    font-size:1.4rem;
}
.spot-cat  { font-size:.72rem; color:rgba(255,255,255,.4); margin-top:2px; }
.spot-stay { font-family:'Rajdhani',sans-serif; color:#FF6B00; font-weight:600; }

/* ── フィーチャーカード ── */
.feature-card {
    background:rgba(0,0,0,.55); border:1px solid rgba(255,255,255,.08);
    border-radius:14px; padding:1.5rem; backdrop-filter:blur(8px);
    transition:border-color .25s,transform .25s; animation:fade-in .8s ease-out;
}
.feature-card:hover { border-color:rgba(255,107,0,.4); transform:translateY(-4px); }
.feature-icon  { font-size:2rem; margin-bottom:.7rem; }
.feature-title { font-family:'Rajdhani',sans-serif; font-size:1.1rem; font-weight:700; color:#FF6B00; margin-bottom:.4rem; }
.feature-desc  { font-family:'Noto Sans JP',sans-serif; font-size:.82rem; color:rgba(255,255,255,.5); line-height:1.6; }

/* ── スクロールバー ── */
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:#111; }
::-webkit-scrollbar-thumb { background:rgba(255,107,0,.4); border-radius:3px; }
hr { border-color:rgba(255,107,0,.15) !important; margin:1.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── 背景スライドショー（静的HTML + CSSアニメーション） ──────────
# Streamlitはst.markdownのscriptタグを実行しないため、JSではなくCSSで実装
st.markdown("""
<div class="bg-slide" style="background-image:url('https://source.unsplash.com/1920x1080/?motorcycle,japan,road')"></div>
<div class="bg-slide" style="background-image:url('https://source.unsplash.com/1920x1080/?mountain,road,japan,scenic')"></div>
<div class="bg-slide" style="background-image:url('https://source.unsplash.com/1920x1080/?coastal,highway,japan')"></div>
<div class="bg-slide" style="background-image:url('https://source.unsplash.com/1920x1080/?motorcycle,touring,sunset')"></div>
<div class="bg-overlay"></div>
""", unsafe_allow_html=True)


# ── ヒーローヘッダー ────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="hero-title">🏍 BIKE ROUTE AI</div>
    <div class="road-lines">
        <div class="road-line"></div><div class="road-line"></div><div class="road-line"></div>
    </div>
    <div class="hero-sub">125cc / 50cc ✦ 下道専用 ✦ AI ツーリングプランナー</div>
    <div class="hero-divider"></div>
</div>
""", unsafe_allow_html=True)


# ── サイドバー ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">📍 出発地 / 目的地</div>', unsafe_allow_html=True)
    origin      = st.text_input("出発地", value="東京都新宿区", label_visibility="collapsed", placeholder="例: 東京都新宿区")
    destination = st.text_input("目的地", value="箱根町",       label_visibility="collapsed", placeholder="例: 箱根町")

    st.markdown('<div class="sidebar-title">🕐 出発 / 帰着</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: start_time = st.text_input("出発", value="08:00", label_visibility="collapsed")
    with c2: end_time   = st.text_input("帰着", value="17:00", label_visibility="collapsed")

    st.markdown('<div class="sidebar-title">🔧 排量</div>', unsafe_allow_html=True)
    engine_cc = st.radio("排量", ["125cc","50cc"], label_visibility="collapsed", horizontal=True)

    st.markdown('<div class="sidebar-title">🎯 旅のスタイル</div>', unsafe_allow_html=True)
    travel_style = st.radio(
        "旅のスタイル",
        ["お任せ","風景","人文"],
        label_visibility="collapsed",
        horizontal=True,
        help="風景=自然・絶景優先 / 人文=博物館・史跡優先 / お任せ=バランス型",
    )

    st.markdown('<div class="sidebar-title">⚙️ オプション</div>', unsafe_allow_html=True)
    want_meal = st.checkbox("🍜 飲食店をおすすめする", value=True)
    want_gas  = st.checkbox("⛽ ガソリンスタンドをおすすめする", value=True)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("✦ プランを生成する", type="primary", use_container_width=True)


# ── メインエリア ──────────────────────────────────────────────────
if run_btn:
    if not origin or not destination:
        st.error("出発地と目的地を入力してください")
        st.stop()

    # バイク走行ローダー
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
    kpi_items = [
        ("DISTANCE",    route.get("distance_km","—"), "km"),
        ("RIDING TIME", budget.get("riding_min","—"), "分"),
        ("SPOTS",       budget.get("n_spots",0),      "箇所"),
        ("MEALS",       budget.get("n_meals",0),      "回"),
    ]
    for col, (label_txt, val, unit_txt) in zip(cols, kpi_items):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label_txt}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-unit">{unit_txt}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── タブ ──
    tab_tl, tab_map = st.tabs(["📋 タイムライン", "🗺️ ルート地図"])

    # ─── タイムラインタブ ───
    with tab_tl:
        st.markdown("<br>", unsafe_allow_html=True)

        # スポット名 → データの辞書
        spot_lookup = {s["name"]: s for s in spots}

        # WikipediaサムネイルをまとめてAPIで取得
        with st.spinner("📡 スポット画像を取得中..."):
            thumbs = {}
            for s in spots:
                if s.get("category") not in ("gas_station", "restaurant"):
                    thumbs[s["name"]] = fetch_wiki_thumb(s["name"])

        # カテゴリ別アイコン
        CAT_ICON = {
            "museum":"🏛️","viewpoint":"🌄","historic":"🏯","castle":"🏯",
            "ruins":"🏚️","monument":"🗿","natural":"🌲","peak":"⛰️",
            "waterfall":"💧","hot_spring":"♨️","beach":"🏖️","park":"🌿",
            "restaurant":"🍜","cafe":"☕","gas_station":"⛽",
            "attraction":"⭐","artwork":"🎨",
        }

        # HTMLテーブルを構築
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

            # 写真セル
            thumb = thumbs.get(name)
            if thumb:
                img_cell = f'<img class="spot-thumb" src="{thumb}" alt="{name}">'
            else:
                icon = CAT_ICON.get(category, "📍")
                img_cell = f'<div class="spot-no-img">{icon}</div>'

            # リンクURL（公式 > Google検索）
            website = spot_data.get("website","")
            link_url = website if website else \
                "https://www.google.com/search?q=" + urllib.parse.quote(name)

            cat_icon = CAT_ICON.get(category,"📍")

            rows += f"""
            <tr>
                <td><div class="spot-time">{arrive}</div></td>
                <td>{img_cell}</td>
                <td>
                    <a class="spot-link" href="{link_url}" target="_blank"
                       rel="noopener noreferrer">{name}</a>
                    <div class="spot-cat">{cat_icon} {category}</div>
                </td>
                <td style="color:rgba(255,255,255,.6)">{dist_km} km</td>
                <td class="spot-stay">{stay_min} 分</td>
                <td style="color:rgba(255,255,255,.5)">{round(cum_km,1)} km</td>
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
        <p style="margin-top:.7rem;font-size:.72rem;color:rgba(255,255,255,.3);
                  font-family:'Noto Sans JP',sans-serif;">
            ※ 写真はWikipedia日本語版から取得。名前クリックで公式サイト or Google検索へ。
        </p>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # AI生成の概要・注意事項テキスト
        plan_text = result.get("plan_text","")
        # タイムラインテーブル部分は省略し、概要と注意事項だけ表示
        sections = []
        for line in plan_text.split("\n"):
            if line.startswith("## タイムライン"):
                break
            sections.append(line)
        overview = "\n".join(sections).strip()
        if overview:
            st.markdown(overview)

        # 注意事項だけ抽出
        notes_lines = []
        in_notes = False
        for line in plan_text.split("\n"):
            if line.startswith("## 注意事項"):
                in_notes = True
            if in_notes:
                notes_lines.append(line)
        if notes_lines:
            st.markdown("\n".join(notes_lines))

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Markdownでダウンロード",
            data=plan_text,
            file_name="touring_plan.md",
            mime="text/markdown",
        )

    # ─── 地図タブ ───
    with tab_map:
        st.markdown("<br>", unsafe_allow_html=True)
        if geometry:
            center_lat = sum(c[1] for c in geometry) / len(geometry)
            center_lon = sum(c[0] for c in geometry) / len(geometry)
        else:
            center_lat, center_lon = 35.68, 139.76

        m = folium.Map(location=[center_lat, center_lon], zoom_start=10,
                       tiles="CartoDB dark_matter")
        if geometry:
            route_coords = [[c[1],c[0]] for c in geometry]
            folium.PolyLine(route_coords, color="#FF6B00", weight=4,
                            opacity=.85, tooltip="下道ルート").add_to(m)
            folium.Marker(route_coords[0],
                popup=folium.Popup(f"🚩 <b>{origin}</b>", max_width=200),
                icon=folium.Icon(color="green",icon="play",prefix="fa")).add_to(m)
            folium.Marker(route_coords[-1],
                popup=folium.Popup(f"🏁 <b>{destination}</b>", max_width=200),
                icon=folium.Icon(color="red",icon="flag",prefix="fa")).add_to(m)

        for spot in spots:
            fill = {"restaurant":"#FFB347","gas_station":"#888"}.get(spot.get("category"),"#FF6B00")
            folium.CircleMarker(
                [spot["lat"],spot["lon"]], radius=8,
                color="#FF6B00", fill=True, fill_color=fill, fill_opacity=.9,
                popup=folium.Popup(f"<b>{spot['name']}</b><br>{spot.get('category','')}", max_width=200),
                tooltip=spot["name"],
            ).add_to(m)

        st_folium(m, width="100%", height=520, returned_objects=[])
        st.markdown("""
        <div style="display:flex;gap:1.5rem;justify-content:center;margin-top:.8rem;
                    font-family:'Rajdhani',sans-serif;font-size:.85rem;color:rgba(255,255,255,.5);">
            <span>🟢 出発地</span><span>🔴 目的地</span>
            <span><span style="color:#FF6B00">●</span> 景点</span>
            <span><span style="color:#FFB347">●</span> 飲食店</span>
            <span><span style="color:#888">●</span> 給油</span>
        </div>
        """, unsafe_allow_html=True)


else:
    # ── デフォルト画面 ──
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc in [
        (c1,"🛣️","下道限定ルート","高速・自動車専用道を完全回避。OSRM cycling プロファイルで50cc/125cc どちらにも対応。"),
        (c2,"🎯","スタイル別おすすめ","風景派（自然・絶景）か人文派（博物館・史跡）か好みに合わせてスポットを自動選定。"),
        (c3,"📸","写真＆リンク付き","Wikipedia画像と公式サイトリンクをタイムラインに自動取得。ナビ代わりに使える。"),
    ]:
        with col:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;padding:1.5rem;background:rgba(0,0,0,.55);
                border:1px solid rgba(255,107,0,.2);border-radius:14px;
                backdrop-filter:blur(8px);animation:fade-in 1s ease-out;">
        <div style="font-family:'Rajdhani',sans-serif;font-size:1.1rem;
                    color:rgba(255,255,255,.6);letter-spacing:.1em;">
            👈 &nbsp;左のサイドバーで条件を設定して
            <span style="color:#FF6B00;font-weight:700;">✦ プランを生成する</span>
            を押してください
        </div>
    </div>
    """, unsafe_allow_html=True)
