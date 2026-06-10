# =============================================
# app.py  ―  画面（UI）を作るファイル
# =============================================
# Streamlit を使うと Pythonだけで Web画面が作れる

import streamlit as st
import folium
from streamlit_folium import st_folium
from agent import run_agent

# ページの基本設定
st.set_page_config(
    page_title="🏍️ バイクルートAI",
    page_icon="🏍️",
    layout="wide",
)

st.title("🏍️ バイクルート AI プランナー")
st.caption("125cc / 50cc 限定・下道専用ツーリングプランを自動生成")

# =============================================
# サイドバー: 入力フォーム
# =============================================
with st.sidebar:
    st.header("⚙️ ツーリング設定")

    origin      = st.text_input("🚩 出発地", value="東京都新宿区")
    destination = st.text_input("🏁 目的地", value="箱根町")

    col1, col2 = st.columns(2)
    with col1:
        start_time = st.text_input("出発時刻", value="08:00")
    with col2:
        end_time = st.text_input("帰着時刻", value="17:00")

    engine_cc = st.radio(
        "🔧 排量",
        options=["125cc", "50cc"],
        help="50cc=原付一種(30km/h制限) / 125cc=原付二種(60km/h制限)",
    )

    st.markdown("---")
    want_meal = st.checkbox("🍜 飲食店もおすすめする", value=True)
    want_gas  = st.checkbox("⛽ ガソリンスタンドもおすすめする", value=True)

    st.markdown("---")
    run_btn = st.button("✨ プランを生成する", type="primary", use_container_width=True)

# =============================================
# メイン画面: 生成ボタンが押されたとき
# =============================================
if run_btn:

    # 簡単な入力チェック
    if not origin or not destination:
        st.error("出発地と目的地を入力してください")
        st.stop()

    # 進捗ログを画面に表示するための仕組み
    status_area = st.empty()
    log_messages = []

    def show_status(msg):
        log_messages.append(msg)
        # 直近4件だけ表示（画面が長くなりすぎないように）
        status_area.info("\n\n".join(log_messages[-4:]))

    # Agentを実行する
    with st.spinner("AIがプランを生成中..."):
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

    status_area.empty()  # 進捗メッセージを消す

    # =============================================
    # 結果を表示する
    # =============================================

    route    = result.get("route") or {}
    budget   = result.get("time_budget") or {}
    timeline = result.get("timeline") or []
    geometry = result.get("geometry") or []

    # KPI カード（数値の概要）
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("総距離",   f"{route.get('distance_km', '—')} km")
    c2.metric("純移動",   f"{budget.get('riding_min', '—')} 分")
    c3.metric("景点数",   f"{budget.get('n_spots', 0)} 箇所")
    c4.metric("食事",     f"{budget.get('n_meals', 0)} 回")

    st.markdown("---")

    # タブで「プラン」と「地図」を切り替える
    tab_plan, tab_map = st.tabs(["📋 タイムラインプラン", "🗺️ 地図"])

    with tab_plan:
        st.markdown(result.get("plan_text", "プランの生成に失敗しました"))

        st.download_button(
            label="📥 Markdownでダウンロード",
            data=result.get("plan_text", ""),
            file_name="touring_plan.md",
            mime="text/markdown",
        )

    with tab_map:
        if geometry:
            # 地図の中心をルートの中間点に設定
            center_lat = sum(c[1] for c in geometry) / len(geometry)
            center_lon = sum(c[0] for c in geometry) / len(geometry)
        else:
            center_lat, center_lon = 35.68, 139.76  # デフォルト: 東京

        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

        # ルートの線を地図に描く
        if geometry:
            route_coords = [[c[1], c[0]] for c in geometry]  # [lat, lon] に変換
            folium.PolyLine(route_coords, color="blue", weight=4, opacity=0.7).add_to(m)

            # 出発地・目的地のマーカー
            folium.Marker(
                route_coords[0],
                popup=f"🚩 {origin}",
                icon=folium.Icon(color="green"),
            ).add_to(m)
            folium.Marker(
                route_coords[-1],
                popup=f"🏁 {destination}",
                icon=folium.Icon(color="red"),
            ).add_to(m)

        # スポットのマーカー
        COLOR_MAP = {
            "restaurant":  "orange",
            "gas_station": "gray",
        }
        for entry in timeline:
            # timelineにlat/lonがないので、all_stopsから取る必要がある
            # → agentからspotsも返すよう修正が必要だが、シンプル化のため省略
            pass

        # agentの結果にspotsを追加して地図に表示
        for spot in result.get("spots_for_map", []):
            color = COLOR_MAP.get(spot.get("category"), "blue")
            folium.Marker(
                [spot["lat"], spot["lon"]],
                popup=spot["name"],
                tooltip=spot["name"],
                icon=folium.Icon(color=color),
            ).add_to(m)

        st_folium(m, width="100%", height=500)
        st.caption("🟢 出発地  🔴 目的地  🔵 景点  🟠 飲食店  ⬜ 給油")

else:
    # ボタンを押す前のデフォルト画面
    st.info("👈 左のサイドバーで条件を入力して「プランを生成する」を押してください")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🛣️ 下道限定ルート")
        st.markdown("高速・自動車専用道を完全回避。50ccの制限も対応。")
    with col2:
        st.markdown("### ⏱️ 時間を自動配分")
        st.markdown("移動時間を引いた残りで、何箇所行けるか自動計算。")
    with col3:
        st.markdown("### 🏯 沿道スポット検索")
        st.markdown("OpenStreetMapから景点・飲食店・GSをルート沿いで自動発見。")
