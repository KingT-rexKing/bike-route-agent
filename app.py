# =============================================
# app.py  ―  フロントエンド（UI）
# =============================================

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

# ── カスタムCSS（道路・バイクテーマ） ────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;600;700&family=Noto+Sans+JP:wght@400;700&display=swap');

/* ── 道路アニメーション背景 ── */
@keyframes road-scroll {
    0%   { background-position: center 0%; }
    100% { background-position: center 100%; }
}
@keyframes lane-scroll {
    0%   { transform: translateY(-100%); }
    100% { transform: translateY(100vh); }
}
@keyframes fade-in {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 20px rgba(255,107,0,0.4); }
    50%       { box-shadow: 0 0 40px rgba(255,107,0,0.8), 0 0 60px rgba(255,107,0,0.3); }
}
@keyframes slide-indicator {
    0%   { left: -100%; }
    50%  { left: 100%; }
    100% { left: 100%; }
}

/* ── 全体背景（アスファルト道路） ── */
.stApp {
    background:
        repeating-linear-gradient(
            180deg,
            transparent 0px,
            transparent 60px,
            rgba(255,255,255,0.03) 60px,
            rgba(255,255,255,0.03) 62px
        ),
        linear-gradient(180deg,
            #0d0d0d 0%,
            #1a1a1a 30%,
            #222222 60%,
            #1a1a1a 100%
        );
    background-size: 100% 120px, 100% 100%;
    animation: road-scroll 8s linear infinite;
    min-height: 100vh;
}

/* ── サイドバー ── */
[data-testid="stSidebar"] {
    background: rgba(10, 10, 10, 0.92) !important;
    border-right: 1px solid rgba(255,107,0,0.3) !important;
    backdrop-filter: blur(20px);
}
[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}

/* ── メインコンテンツ ── */
.main .block-container {
    padding-top: 1rem;
    max-width: 1200px;
}

/* ── ヒーローヘッダー ── */
.hero-header {
    text-align: center;
    padding: 2.5rem 1rem 2rem;
    animation: fade-in 0.8s ease-out;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg,
        rgba(255,107,0,0.08) 0%,
        transparent 50%,
        rgba(255,107,0,0.05) 100%);
    border-radius: 16px;
    pointer-events: none;
}
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    letter-spacing: 0.08em;
    background: linear-gradient(135deg, #FF6B00 0%, #FFB347 50%, #FF6B00 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: none;
    margin: 0;
    line-height: 1;
}
.hero-sub {
    font-family: 'Rajdhani', 'Noto Sans JP', sans-serif;
    font-size: 1rem;
    color: rgba(255,255,255,0.55);
    letter-spacing: 0.2em;
    margin-top: 0.5rem;
    text-transform: uppercase;
}
.hero-divider {
    width: 80px;
    height: 3px;
    background: linear-gradient(90deg, transparent, #FF6B00, transparent);
    margin: 1rem auto 0;
    border-radius: 2px;
}

/* ── 道路ラインデコレーション ── */
.road-lines {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin: 0.8rem 0;
}
.road-line {
    width: 40px;
    height: 4px;
    background: #FF6B00;
    border-radius: 2px;
    opacity: 0.7;
}
.road-line:nth-child(2) { opacity: 0.4; width: 20px; }
.road-line:nth-child(3) { opacity: 0.2; width: 10px; }

/* ── サイドバーセクションタイトル ── */
.sidebar-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.25em;
    color: #FF6B00;
    text-transform: uppercase;
    margin: 1.2rem 0 0.4rem;
    padding-left: 2px;
}

/* ── 入力フィールド ── */
[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,107,0,0.25) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-family: 'Noto Sans JP', sans-serif !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stTextInput"] input:focus {
    border-color: rgba(255,107,0,0.7) !important;
    box-shadow: 0 0 0 2px rgba(255,107,0,0.15) !important;
}
[data-testid="stTextInput"] label {
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.85rem !important;
}

/* ── ラジオボタン ── */
[data-testid="stRadio"] label {
    color: rgba(255,255,255,0.8) !important;
}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    color: rgba(255,255,255,0.8) !important;
}

/* ── チェックボックス ── */
[data-testid="stCheckbox"] label {
    color: rgba(255,255,255,0.8) !important;
}

/* ── 生成ボタン ── */
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #FF6B00, #e55a00) !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    color: #ffffff !important;
    animation: pulse-glow 2.5s ease-in-out infinite;
    transition: transform 0.1s;
}
[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-2px);
    background: linear-gradient(135deg, #FF7F00, #FF6B00) !important;
}
[data-testid="stBaseButton-primary"]:active {
    transform: translateY(0);
}

/* ── KPIカード ── */
.kpi-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,107,0,0.2);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    transition: border-color 0.2s, transform 0.2s;
    animation: fade-in 0.6s ease-out;
}
.kpi-card:hover {
    border-color: rgba(255,107,0,0.5);
    transform: translateY(-3px);
}
.kpi-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    color: rgba(255,255,255,0.45);
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.kpi-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem;
    color: #FF6B00;
    line-height: 1;
}
.kpi-unit {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.85rem;
    color: rgba(255,255,255,0.4);
    margin-top: 0.2rem;
}

/* ── タブ ── */
[data-testid="stTabs"] [role="tab"] {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    color: rgba(255,255,255,0.55) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #FF6B00 !important;
    border-bottom-color: #FF6B00 !important;
}

/* ── プランテキストエリア ── */
[data-testid="stMarkdownContainer"] {
    color: rgba(255,255,255,0.85) !important;
}
[data-testid="stMarkdownContainer"] h2 {
    color: #FF6B00 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.4rem !important;
    border-bottom: 1px solid rgba(255,107,0,0.2);
    padding-bottom: 0.3rem;
    margin-top: 1.5rem !important;
}
[data-testid="stMarkdownContainer"] table {
    background: rgba(255,255,255,0.03) !important;
    border-collapse: collapse !important;
    width: 100% !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
[data-testid="stMarkdownContainer"] th {
    background: rgba(255,107,0,0.15) !important;
    color: #FF6B00 !important;
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 0.05em !important;
    padding: 0.7rem 1rem !important;
    border: 1px solid rgba(255,107,0,0.15) !important;
}
[data-testid="stMarkdownContainer"] td {
    padding: 0.6rem 1rem !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    color: rgba(255,255,255,0.8) !important;
}
[data-testid="stMarkdownContainer"] tr:hover td {
    background: rgba(255,107,0,0.05) !important;
}

/* ── 進捗ログ ── */
[data-testid="stAlert"] {
    background: rgba(255,107,0,0.08) !important;
    border: 1px solid rgba(255,107,0,0.25) !important;
    border-radius: 10px !important;
    color: rgba(255,255,255,0.8) !important;
}

/* ── ダウンロードボタン ── */
[data-testid="stBaseButton-secondary"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,107,0,0.3) !important;
    border-radius: 8px !important;
    color: rgba(255,255,255,0.8) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    transition: background 0.2s, border-color 0.2s;
}
[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(255,107,0,0.12) !important;
    border-color: rgba(255,107,0,0.6) !important;
}

/* ── メトリクスカード（Streamlit標準） ── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,107,0,0.15);
    border-radius: 12px;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] {
    color: rgba(255,255,255,0.5) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: #FF6B00 !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 2rem !important;
}

/* ── フィーチャーカード（トップ3枚） ── */
.feature-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.5rem;
    height: 100%;
    transition: border-color 0.25s, transform 0.25s;
    animation: fade-in 0.8s ease-out;
}
.feature-card:hover {
    border-color: rgba(255,107,0,0.4);
    transform: translateY(-4px);
}
.feature-icon {
    font-size: 2rem;
    margin-bottom: 0.7rem;
}
.feature-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #FF6B00;
    margin-bottom: 0.4rem;
    letter-spacing: 0.05em;
}
.feature-desc {
    font-family: 'Noto Sans JP', sans-serif;
    font-size: 0.82rem;
    color: rgba(255,255,255,0.5);
    line-height: 1.6;
}

/* ── スクロールバー ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb {
    background: rgba(255,107,0,0.4);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255,107,0,0.7);
}

/* ── セパレーター ── */
hr {
    border-color: rgba(255,107,0,0.15) !important;
    margin: 1.5rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── ヒーローヘッダー ────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="hero-title">🏍 BIKE ROUTE AI</div>
    <div class="road-lines">
        <div class="road-line"></div>
        <div class="road-line"></div>
        <div class="road-line"></div>
    </div>
    <div class="hero-sub">125cc / 50cc ✦ 下道専用 ✦ AI ツーリングプランナー</div>
    <div class="hero-divider"></div>
</div>
""", unsafe_allow_html=True)

# ── サイドバー ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">📍 出発地 / 目的地</div>', unsafe_allow_html=True)
    origin      = st.text_input("出発地", value="東京都新宿区", label_visibility="collapsed", placeholder="例: 東京都新宿区")
    destination = st.text_input("目的地", value="箱根町",     label_visibility="collapsed", placeholder="例: 箱根町")

    st.markdown('<div class="sidebar-title">🕐 出発 / 帰着</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.text_input("出発", value="08:00", label_visibility="collapsed")
    with col2:
        end_time = st.text_input("帰着", value="17:00", label_visibility="collapsed")

    st.markdown('<div class="sidebar-title">🔧 排量</div>', unsafe_allow_html=True)
    engine_cc = st.radio(
        "排量",
        options=["125cc", "50cc"],
        label_visibility="collapsed",
        horizontal=True,
        help="50cc = 原付一種（30km/h制限）\n125cc = 原付二種（60km/h制限）",
    )

    st.markdown('<div class="sidebar-title">⚙️ オプション</div>', unsafe_allow_html=True)
    want_meal = st.checkbox("🍜 飲食店をおすすめする", value=True)
    want_gas  = st.checkbox("⛽ ガソリンスタンドをおすすめする", value=True)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("✦ プランを生成する", type="primary", use_container_width=True)

# ── メインエリア ──────────────────────────────────────────────────
if run_btn:
    # 入力チェック
    if not origin or not destination:
        st.error("出発地と目的地を入力してください")
        st.stop()

    # 進捗ログ
    status_area  = st.empty()
    log_messages = []

    def show_status(msg):
        log_messages.append(msg)
        status_area.info("\n\n".join(log_messages[-4:]))

    with st.spinner(""):
        st.markdown("""
        <div style="text-align:center; padding:1rem; color:rgba(255,107,0,0.8);
                    font-family:'Rajdhani',sans-serif; font-size:1.1rem; letter-spacing:0.1em;">
            ⚡ AI がルートを解析中...
        </div>
        """, unsafe_allow_html=True)

        try:
            result = run_agent(
                origin=origin,
                destination=destination,
                start_time=start_time,
                end_time=end_time,
                engine_cc=engine_cc,
                want_meal=want_meal,
                want_gas=want_gas,
                status_cb=show_status,
            )
        except Exception as e:
            st.error(f"エラー: {e}")
            st.stop()

    status_area.empty()

    route    = result.get("route") or {}
    budget   = result.get("time_budget") or {}
    timeline = result.get("timeline") or []
    geometry = result.get("geometry") or []
    spots    = result.get("spots_for_map") or []

    # ── KPIカード ──
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "DISTANCE",   f"{route.get('distance_km', '—')}",  "km"),
        (c2, "RIDING TIME", f"{budget.get('riding_min', '—')}",  "分"),
        (c3, "SPOTS",       f"{budget.get('n_spots', 0)}",       "箇所"),
        (c4, "MEALS",       f"{budget.get('n_meals', 0)}",       "回"),
    ]
    for col, label, value, unit in cards:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-unit">{unit}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── タブ ──
    tab_plan, tab_map = st.tabs(["📋 タイムラインプラン", "🗺️ ルート地図"])

    with tab_plan:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(result.get("plan_text", "プランの生成に失敗しました"))

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Markdownでダウンロード",
            data=result.get("plan_text", ""),
            file_name="touring_plan.md",
            mime="text/markdown",
        )

    with tab_map:
        st.markdown("<br>", unsafe_allow_html=True)
        if geometry:
            center_lat = sum(c[1] for c in geometry) / len(geometry)
            center_lon = sum(c[0] for c in geometry) / len(geometry)
        else:
            center_lat, center_lon = 35.68, 139.76

        # ダークテーマの地図
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles="CartoDB dark_matter",
        )

        # ルートライン（オレンジ）
        if geometry:
            route_coords = [[c[1], c[0]] for c in geometry]
            folium.PolyLine(
                route_coords,
                color="#FF6B00",
                weight=4,
                opacity=0.85,
                tooltip="下道ルート",
            ).add_to(m)

            # 出発地マーカー
            folium.Marker(
                route_coords[0],
                popup=folium.Popup(f"🚩 <b>{origin}</b>", max_width=200),
                icon=folium.Icon(color="green", icon="play", prefix="fa"),
            ).add_to(m)

            # 目的地マーカー
            folium.Marker(
                route_coords[-1],
                popup=folium.Popup(f"🏁 <b>{destination}</b>", max_width=200),
                icon=folium.Icon(color="red", icon="flag", prefix="fa"),
            ).add_to(m)

        # スポットマーカー
        COLOR_MAP = {
            "restaurant":  "orange",
            "gas_station": "lightgray",
            "museum":      "blue",
            "viewpoint":   "purple",
            "castle":      "darkblue",
        }
        for i, spot in enumerate(spots):
            color = COLOR_MAP.get(spot.get("category"), "cadetblue")
            folium.CircleMarker(
                [spot["lat"], spot["lon"]],
                radius=8,
                color="#FF6B00",
                fill=True,
                fill_color={"restaurant": "#FFB347", "gas_station": "#888"}.get(spot.get("category"), "#FF6B00"),
                fill_opacity=0.9,
                popup=folium.Popup(
                    f"<b>{spot['name']}</b><br>{spot.get('category','')}", max_width=200
                ),
                tooltip=f"{'⛽' if spot.get('category')=='gas_station' else '🍜' if spot.get('category')=='restaurant' else '🏯'} {spot['name']}",
            ).add_to(m)

        st_folium(m, width="100%", height=520, returned_objects=[])
        st.markdown("""
        <div style="display:flex; gap:1.5rem; justify-content:center; margin-top:0.8rem;
                    font-family:'Rajdhani',sans-serif; font-size:0.85rem;
                    color:rgba(255,255,255,0.5);">
            <span>🟢 出発地</span>
            <span>🔴 目的地</span>
            <span><span style="color:#FF6B00">●</span> 景点</span>
            <span><span style="color:#FFB347">●</span> 飲食店</span>
            <span><span style="color:#888">●</span> 給油</span>
        </div>
        """, unsafe_allow_html=True)

else:
    # ── デフォルト画面（フィーチャーカード） ──
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    features = [
        (c1, "🛣️", "下道限定ルート",
         "高速・自動車専用道を完全回避。OSRM の cycling プロファイルで50cc/125cc どちらにも対応した安全ルートを生成。"),
        (c2, "⏱️", "スマート時間配分",
         "移動時間・バッファ・食事を差し引き、余った時間で何箇所立ち寄れるかをアルゴリズムで自動計算。"),
        (c3, "🏯", "沿道POI 自動発見",
         "OpenStreetMap から景点・飲食店・ガソリンスタンドをルート沿い自動検索。APIキー不要・完全無料。"),
    ]
    for col, icon, title, desc in features:
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
    <div style="text-align:center; padding:1.5rem;
                background:rgba(255,107,0,0.06); border:1px solid rgba(255,107,0,0.2);
                border-radius:14px; animation: fade-in 1s ease-out;">
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.1rem;
                    color:rgba(255,255,255,0.6); letter-spacing:0.1em;">
            👈 &nbsp; 左のサイドバーで条件を設定して
            <span style="color:#FF6B00; font-weight:700;">✦ プランを生成する</span>
            を押してください
        </div>
    </div>
    """, unsafe_allow_html=True)
