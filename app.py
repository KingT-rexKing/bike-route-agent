# =============================================
# app.py  ―  フロントエンド（UI）  v4 全面最適化
# =============================================

import json
import urllib.parse
from collections import Counter
from datetime import time as dtime, timedelta

import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from agent import run_agent

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

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


# ── カテゴリ定義（共通） ─────────────────────────────────────────
CAT_ICON = {
    "museum":"🏛️","viewpoint":"🌄","historic":"🏯","castle":"🏯",
    "ruins":"🏚️","monument":"🗿","natural":"🌲","peak":"⛰️",
    "waterfall":"💧","hot_spring":"♨️","beach":"🏖️","park":"🌿",
    "restaurant":"🍜","cafe":"☕","gas_station":"⛽",
    "attraction":"⭐","artwork":"🎨",
}
CAT_COLOR = {
    "museum":"#9C27B0","viewpoint":"#2196F3","historic":"#FF9800",
    "castle":"#FF5722","natural":"#4CAF50","peak":"#00BCD4",
    "waterfall":"#03A9F4","hot_spring":"#E91E63","beach":"#00BCD4",
    "park":"#8BC34A","restaurant":"#FF6B00","cafe":"#A0522D",
    "gas_station":"#607D8B","attraction":"#FFC107","artwork":"#E040FB",
}


# ── CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;600;700&family=Noto+Sans+JP:wght@400;700&display=swap');

/* ── Streamlit標準UIを非表示 ── */
#MainMenu,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],footer{visibility:hidden!important;height:0!important}
h1 a,h2 a,h3 a,[data-testid="stMarkdownContainer"] h2 a{display:none!important}

/* ── 全背景透過（JSレイヤーを見せる） ── */
body{background:#0d0d0d!important}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"],
section.main,.main{background:transparent!important;background-color:transparent!important}
[data-testid="stSidebar"]{
    background:rgba(6,6,6,.92)!important;
    border-right:1px solid rgba(255,107,0,.28)!important;
    backdrop-filter:blur(20px);
}
iframe[height="0"],iframe[height="1"]{
    display:block!important;height:0!important;
    min-height:0!important;border:none!important;
}

/* ── キーフレーム ── */
@keyframes fade-in{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@keyframes fade-in-slow{from{opacity:0}to{opacity:1}}
@keyframes pulse-glow{
    0%,100%{box-shadow:0 0 18px rgba(255,107,0,.4)}
    50%{box-shadow:0 0 44px rgba(255,107,0,.95),0 0 80px rgba(255,107,0,.28)}
}
@keyframes moto-ride{0%{left:-6%}100%{left:104%}}
@keyframes road-dash{0%{background-position:0 0}100%{background-position:80px 0}}
@keyframes title-shine{
    0%{background-position:-200% center}100%{background-position:200% center}
}
@keyframes border-flow{
    0%,100%{border-color:rgba(255,107,0,.22)}
    50%{border-color:rgba(255,107,0,.6)}
}
@keyframes ripple{0%{transform:scale(0);opacity:.5}100%{transform:scale(4);opacity:0}}

/* ── レイアウト ── */
.main .block-container{padding-top:1rem;max-width:1240px}

/* ── ヒーローヘッダー ── */
.hero-header{text-align:center;padding:2.2rem 1rem 1.8rem;animation:fade-in .8s ease-out}
.hero-badge{
    display:inline-block;font-family:'Rajdhani',sans-serif;font-size:.65rem;
    letter-spacing:.25em;color:#FF6B00;border:1px solid rgba(255,107,0,.4);
    border-radius:20px;padding:.22rem .9rem;margin-bottom:.7rem;
    text-transform:uppercase;animation:border-flow 3s ease-in-out infinite;
    background:rgba(255,107,0,.06);
}
.hero-title{
    font-family:'Bebas Neue',sans-serif;
    font-size:clamp(2.8rem,7vw,5.2rem);letter-spacing:.08em;
    background:linear-gradient(110deg,#FF6B00 20%,#FFE0B3 50%,#FF6B00 80%);
    background-size:200% auto;
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    background-clip:text;margin:0;line-height:1;
    animation:title-shine 5s linear infinite;
}
.hero-sub{
    font-family:'Rajdhani','Noto Sans JP',sans-serif;
    font-size:.95rem;color:rgba(255,255,255,.5);
    letter-spacing:.22em;margin-top:.5rem;text-transform:uppercase;
}
.hero-divider{
    width:80px;height:3px;
    background:linear-gradient(90deg,transparent,#FF6B00,transparent);
    margin:.8rem auto 0;border-radius:2px;
}
.road-lines{display:flex;justify-content:center;gap:8px;margin:.6rem 0}
.road-line{width:40px;height:4px;background:#FF6B00;border-radius:2px;opacity:.7}
.road-line:nth-child(2){opacity:.4;width:22px}
.road-line:nth-child(3){opacity:.2;width:10px}

/* ── サイドバーラベル ── */
.sidebar-title{
    font-family:'Rajdhani',sans-serif;font-size:.68rem;
    letter-spacing:.25em;color:#FF6B00;text-transform:uppercase;margin:1.2rem 0 .4rem;
}
.sidebar-meta{
    font-family:'Rajdhani',sans-serif;font-size:.78rem;
    color:rgba(255,255,255,.5);padding:.4rem .6rem;
    background:rgba(255,107,0,.06);border-radius:6px;
    border-left:2px solid rgba(255,107,0,.4);margin:.3rem 0;
}

/* ── 入力/ラジオ/チェック ── */
[data-testid="stTextInput"] input{
    background:rgba(255,255,255,.06)!important;
    border:1px solid rgba(255,107,0,.25)!important;
    border-radius:8px!important;color:#fff!important;
    transition:border-color .2s,box-shadow .2s;
}
[data-testid="stTextInput"] input:focus{
    border-color:rgba(255,107,0,.7)!important;
    box-shadow:0 0 0 2px rgba(255,107,0,.15),0 0 18px rgba(255,107,0,.25)!important;
}
[data-testid="stTextInput"] label{color:rgba(255,255,255,.65)!important}
[data-testid="stRadio"] label,[data-testid="stCheckbox"] label{color:rgba(255,255,255,.8)!important}
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"]{
    background:#FF6B00!important;box-shadow:0 0 10px rgba(255,107,0,.7)!important;
}
[data-testid="stSlider"] label{color:rgba(255,255,255,.65)!important}

/* ── ボタン ── */
[data-testid="stBaseButton-primary"]{
    background:linear-gradient(135deg,#FF6B00,#e55a00)!important;
    border:none!important;border-radius:10px!important;
    font-family:'Rajdhani',sans-serif!important;
    font-size:1.1rem!important;font-weight:700!important;
    letter-spacing:.1em!important;color:#fff!important;
    animation:pulse-glow 2.5s ease-in-out infinite;
    transition:transform .15s!important;position:relative;overflow:hidden;
}
[data-testid="stBaseButton-primary"]:hover{transform:scale(1.03)}
[data-testid="stBaseButton-primary"]:active{transform:scale(.97)}
[data-testid="stBaseButton-secondary"]{
    background:rgba(255,255,255,.06)!important;
    border:1px solid rgba(255,107,0,.3)!important;
    border-radius:8px!important;color:rgba(255,255,255,.8)!important;
    font-family:'Rajdhani',sans-serif!important;font-weight:600!important;
    transition:border-color .2s,background .2s,transform .15s!important;
}
[data-testid="stBaseButton-secondary"]:hover{
    border-color:rgba(255,107,0,.7)!important;
    background:rgba(255,107,0,.12)!important;transform:translateY(-2px);
}

/* ── KPIカード ── */
.kpi-row{display:flex;gap:1rem;margin:1rem 0}
.kpi-card{
    flex:1;background:rgba(0,0,0,.55);border:1px solid rgba(255,107,0,.22);
    border-radius:14px;padding:1.2rem 1rem;text-align:center;
    backdrop-filter:blur(10px);
    transition:border-color .25s,transform .25s,box-shadow .25s;
    animation:fade-in .6s ease-out;
}
.kpi-card:hover{
    border-color:rgba(255,107,0,.65);transform:translateY(-5px) scale(1.03);
    box-shadow:0 10px 36px rgba(255,107,0,.2);
}
.kpi-label{
    font-family:'Rajdhani',sans-serif;font-size:.65rem;
    letter-spacing:.22em;color:rgba(255,255,255,.4);text-transform:uppercase;margin-bottom:.4rem;
}
.kpi-value{
    font-family:'Bebas Neue',sans-serif;font-size:2.4rem;
    color:#FF6B00;line-height:1;
}
.kpi-unit{font-family:'Rajdhani',sans-serif;font-size:.8rem;color:rgba(255,255,255,.35);margin-top:.2rem}
.kpi-icon{font-size:1.4rem;margin-bottom:.4rem}

/* ── 難易度バッジ ── */
.diff-badge{
    display:inline-flex;align-items:center;gap:.4rem;
    font-family:'Rajdhani',sans-serif;font-size:.85rem;font-weight:700;
    padding:.35rem 1rem;border-radius:20px;letter-spacing:.1em;
    border:1px solid currentColor;
    animation:fade-in .8s ease-out;
}

/* ── 燃料費表示 ── */
.fuel-card{
    background:rgba(255,107,0,.07);border:1px solid rgba(255,107,0,.2);
    border-radius:10px;padding:.7rem 1rem;margin:.8rem 0;
    font-family:'Rajdhani',sans-serif;animation:fade-in .6s ease-out;
}
.fuel-main{font-size:1.5rem;font-weight:700;color:#FF6B00}
.fuel-sub{font-size:.75rem;color:rgba(255,255,255,.4);margin-top:.2rem}

/* ── タブ ── */
[data-testid="stTabs"] [role="tab"]{
    font-family:'Rajdhani',sans-serif!important;font-size:1rem!important;
    font-weight:600!important;color:rgba(255,255,255,.5)!important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{
    color:#FF6B00!important;border-bottom-color:#FF6B00!important;
}

/* ── AI テキスト ── */
[data-testid="stMarkdownContainer"]{color:rgba(255,255,255,.85)!important}
[data-testid="stMarkdownContainer"] h2{
    color:#FF6B00!important;font-family:'Rajdhani',sans-serif!important;
    font-size:1.35rem!important;border-bottom:1px solid rgba(255,107,0,.2);
    padding-bottom:.3rem;margin-top:1.5rem!important;
}
[data-testid="stMarkdownContainer"] table{background:rgba(255,255,255,.03)!important;border-collapse:collapse!important;width:100%!important}
[data-testid="stMarkdownContainer"] th{background:rgba(255,107,0,.15)!important;color:#FF6B00!important;font-family:'Rajdhani',sans-serif!important;padding:.7rem 1rem!important;border:1px solid rgba(255,107,0,.15)!important}
[data-testid="stMarkdownContainer"] td{padding:.6rem 1rem!important;border:1px solid rgba(255,255,255,.06)!important;color:rgba(255,255,255,.8)!important}
[data-testid="stMarkdownContainer"] tr:hover td{background:rgba(255,107,0,.05)!important}

/* ── バイクローダー ── */
.moto-loader{
    position:relative;width:100%;height:92px;overflow:hidden;
    background:rgba(0,0,0,.5);border-radius:14px;
    border:1px solid rgba(255,107,0,.2);backdrop-filter:blur(8px);margin:1rem 0;
}
.moto-label{
    position:absolute;top:13px;left:0;right:0;text-align:center;
    font-family:'Rajdhani',sans-serif;font-size:.92rem;letter-spacing:.15em;
    color:rgba(255,255,255,.65);
}
.moto-track{
    position:absolute;bottom:28px;left:0;right:0;height:3px;
    background:repeating-linear-gradient(90deg,rgba(255,107,0,.7) 0,rgba(255,107,0,.7) 24px,transparent 24px,transparent 48px);
    animation:road-dash .35s linear infinite;
}
.moto-bike{
    position:absolute;bottom:20px;font-size:2rem;line-height:1;
    filter:drop-shadow(0 0 10px rgba(255,107,0,.9));
    animation:moto-ride 2.8s linear infinite;
}

/* ── タイムライン（縦型カード） ── */
.tl-wrap{position:relative;padding-left:28px;margin:1rem 0}
.tl-wrap::before{
    content:'';position:absolute;left:10px;top:0;bottom:0;
    width:2px;background:linear-gradient(180deg,#FF6B00 0%,rgba(255,107,0,.1) 100%);
}
.tl-card{
    position:relative;margin-bottom:1rem;
    background:rgba(0,0,0,.5);border-radius:12px;
    border:1px solid rgba(255,255,255,.07);
    backdrop-filter:blur(6px);overflow:hidden;
    transition:border-color .25s,transform .2s,box-shadow .25s;
    animation:fade-in .5s ease-out;
}
.tl-card:hover{
    border-color:rgba(255,107,0,.5);transform:translateX(4px);
    box-shadow:0 6px 28px rgba(255,107,0,.12);
}
.tl-card::before{
    content:'';position:absolute;left:0;top:0;bottom:0;width:3px;
}
.tl-node{
    position:absolute;left:-22px;top:18px;
    width:12px;height:12px;border-radius:50%;
    border:2px solid #FF6B00;background:#0d0d0d;
    box-shadow:0 0 8px rgba(255,107,0,.8);
}
.tl-body{display:flex;gap:.8rem;padding:.85rem 1rem;align-items:flex-start}
.tl-thumb{
    width:68px;height:50px;object-fit:cover;border-radius:6px;
    border:1px solid rgba(255,107,0,.25);flex-shrink:0;
    transition:transform .25s;
}
.tl-thumb:hover{transform:scale(1.8)}
.tl-no-img{
    width:68px;height:50px;border-radius:6px;
    border:1px dashed rgba(255,107,0,.2);
    background:rgba(255,107,0,.05);display:flex;
    align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0;
}
.tl-info{flex:1;min-width:0}
.tl-time{
    font-family:'Bebas Neue',sans-serif;font-size:1rem;
    color:#FFB347;margin-bottom:.2rem;
}
.tl-name{
    font-family:'Noto Sans JP',sans-serif;font-weight:700;
    font-size:.9rem;color:#FF6B00;text-decoration:none;
}
.tl-name:hover{color:#FFD580;text-decoration:underline}
.tl-cat{font-size:.7rem;color:rgba(255,255,255,.38);margin-top:.15rem}
.tl-meta{
    display:flex;gap:1rem;margin-top:.4rem;flex-wrap:wrap;
}
.tl-chip{
    font-family:'Rajdhani',sans-serif;font-size:.73rem;
    color:rgba(255,255,255,.5);background:rgba(255,255,255,.06);
    border-radius:4px;padding:.1rem .45rem;
}

/* ── 統計Tab ── */
.stat-row{display:flex;align-items:center;gap:.8rem;margin-bottom:.8rem}
.stat-label{font-family:'Rajdhani',sans-serif;font-size:.82rem;color:rgba(255,255,255,.7);width:110px;white-space:nowrap}
.stat-bar-wrap{flex:1;height:8px;background:rgba(255,255,255,.08);border-radius:4px;overflow:hidden}
.stat-bar{height:100%;border-radius:4px;transition:width 1.2s ease}
.stat-count{font-family:'Bebas Neue',sans-serif;font-size:1.1rem;color:#FF6B00;min-width:24px;text-align:right}

/* ── フィーチャーカード ── */
.feature-card{
    background:rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.08);
    border-radius:14px;padding:1.5rem;backdrop-filter:blur(8px);
    transition:border-color .25s,transform .25s,box-shadow .25s;animation:fade-in .8s ease-out;
}
.feature-card:hover{
    border-color:rgba(255,107,0,.5);transform:translateY(-6px);
    box-shadow:0 14px 40px rgba(255,107,0,.15);
}
.feature-icon{font-size:2rem;margin-bottom:.7rem}
.feature-title{font-family:'Rajdhani',sans-serif;font-size:1.1rem;font-weight:700;color:#FF6B00;margin-bottom:.4rem}
.feature-desc{font-family:'Noto Sans JP',sans-serif;font-size:.82rem;color:rgba(255,255,255,.5);line-height:1.6}

/* ── スクロールバー / HR ── */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:#111}
::-webkit-scrollbar-thumb{background:rgba(255,107,0,.4);border-radius:3px}
hr{border-color:rgba(255,107,0,.15)!important;margin:1.5rem 0!important}

/* ── モバイル対応 ── */
@media(max-width:768px){
    .kpi-card{padding:.9rem .6rem}
    .kpi-value{font-size:1.8rem}
    .tl-body{flex-direction:column;gap:.5rem}
    .tl-thumb,.tl-no-img{width:100%;height:120px}
    .hero-title{font-size:2.6rem}
}

/* ── 印刷スタイル ── */
@media print{
    #fx-bg,#fx-canvas,#fx-glow,#fx-dots,#fx-splash{display:none!important}
    body{background:#fff!important;color:#000!important}
    .stApp,[data-testid="stSidebar"]{background:#fff!important}
    .kpi-card,.tl-card,.feature-card{border:1px solid #ddd!important;background:#f9f9f9!important}
    [data-testid="stTabs"]{display:none!important}
}
</style>
""", unsafe_allow_html=True)


# ── フルスクリーン特効レイヤー ─────────────────────────────────
BG_IMAGES = [
    "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=1920&q=80&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1920&q=80&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=1920&q=80&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1490806843957-31f4c9a91c65?w=1920&q=80&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?w=1920&q=80&auto=format&fit=crop",
]

_inject = st.iframe if hasattr(st, "iframe") else __import__("streamlit.components.v1", fromlist=["html"]).html

_inject(f"""
<script>
(function() {{
  var P = window.parent.document, W = window.parent;
  if (P.getElementById('fx-bg')) return;
  var URLS = {json.dumps(BG_IMAGES)};

  /* ── スタイル注入 ── */
  var css = P.createElement('style');
  css.textContent = `
    @keyframes fx-kb {{ 0% {{ transform:scale(1.05) translate(0,0); }} 100% {{ transform:scale(1.2) translate(-2%,-1.5%); }} }}
    @keyframes fx-gm {{ 0%,100% {{ background-position:0% 50%; }} 50% {{ background-position:100% 50%; }} }}
    @keyframes fx-aurora {{ 0%,100% {{ transform:translate(0,0) scale(1);opacity:.55; }} 33% {{ transform:translate(80px,-40px) scale(1.12);opacity:.7; }} 66% {{ transform:translate(-40px,60px) scale(.9);opacity:.4; }} }}
    @keyframes fx-grid-move {{ 0% {{ transform:perspective(600px) rotateX(40deg) scaleY(2.8) translateY(0); }} 100% {{ transform:perspective(600px) rotateX(40deg) scaleY(2.8) translateY(50px); }} }}
    @keyframes fx-splash-bar {{ 0% {{ width:0; }} 100% {{ width:100%; }} }}
    @keyframes fx-splash-in {{ from {{ opacity:0;transform:scale(.94); }} to {{ opacity:1;transform:scale(1); }} }}
    @keyframes fx-splash-road {{ 0% {{ background-position:0 0; }} 100% {{ background-position:80px 0; }} }}

    #fx-bg {{ position:fixed;inset:0;z-index:-2;overflow:hidden;pointer-events:none; }}
    #fx-fall {{
      position:absolute;inset:0;
      background:linear-gradient(-45deg,#180900,#0d0d0d,#200e04,#0d0d0d);
      background-size:400% 400%;animation:fx-gm 18s ease infinite;
    }}
    .fx-aurora {{
      position:absolute;border-radius:50%;filter:blur(90px);will-change:transform;
      pointer-events:none;
    }}
    #fx-grid {{
      position:absolute;inset:-20%;
      background-image:
        linear-gradient(rgba(255,107,0,.07) 1px,transparent 1px),
        linear-gradient(90deg,rgba(255,107,0,.07) 1px,transparent 1px);
      background-size:55px 55px;
      transform:perspective(600px) rotateX(40deg) scaleY(2.8) translateY(0);
      transform-origin:bottom center;opacity:.55;
      animation:fx-grid-move 4s linear infinite;
    }}
    .fx-slide {{
      position:absolute;inset:-5%;background-size:cover;background-position:center;
      opacity:0;transition:opacity 2.6s ease-in-out;will-change:transform,opacity;
    }}
    .fx-slide.on {{ opacity:1;animation:fx-kb 12s ease-out forwards; }}
    #fx-overlay {{
      position:absolute;inset:0;
      background:
        radial-gradient(ellipse at center,rgba(0,0,0,.3) 0%,rgba(0,0,0,.82) 100%),
        linear-gradient(180deg,rgba(13,13,13,.6),rgba(13,13,13,.3) 40%,rgba(13,13,13,.75));
    }}
    #fx-canvas {{ position:fixed;inset:0;z-index:-1;pointer-events:none; }}
    #fx-glow {{
      position:fixed;width:560px;height:560px;border-radius:50%;
      background:radial-gradient(circle,rgba(255,107,0,.13) 0%,transparent 65%);
      pointer-events:none;z-index:-1;transform:translate(-50%,-50%);
      will-change:left,top;transition:left .08s,top .08s;
    }}
    #fx-dots {{
      position:fixed;right:18px;bottom:16px;z-index:999990;
      display:flex;gap:8px;align-items:center;
    }}
    .fx-dot {{
      width:9px;height:9px;border-radius:50%;cursor:pointer;
      background:rgba(255,255,255,.25);border:1px solid rgba(255,107,0,.4);
      transition:all .3s;pointer-events:auto;
    }}
    .fx-dot:hover {{ transform:scale(1.55); }}
    .fx-dot.on {{ background:#FF6B00;box-shadow:0 0 12px rgba(255,107,0,.95);width:24px;border-radius:5px; }}

    /* ── スプラッシュ ── */
    #fx-splash {{
      position:fixed;inset:0;z-index:9999999;background:#0d0d0d;
      display:flex;align-items:center;justify-content:center;flex-direction:column;
      transition:opacity .9s ease;
    }}
    #fx-splash-title {{
      font-family:'Bebas Neue',Impact,'Arial Black',sans-serif;font-size:4.8rem;letter-spacing:.1em;
      color:#FF6B00;
      text-shadow:0 0 40px rgba(255,107,0,.7),0 0 80px rgba(255,107,0,.3);
      animation:fx-splash-in .6s ease-out;
    }}
    #fx-splash-sub {{
      font-family:Rajdhani,sans-serif;letter-spacing:.35em;
      color:rgba(255,255,255,.35);font-size:.85rem;margin-top:.4rem;
    }}
    #fx-splash-bar-wrap {{
      width:220px;height:2px;background:rgba(255,107,0,.18);
      border-radius:1px;margin-top:1.6rem;overflow:hidden;
    }}
    #fx-splash-prog {{
      height:100%;width:0;background:#FF6B00;
      animation:fx-splash-bar 2.2s ease-out .2s forwards;
    }}
    #fx-splash-road {{
      width:220px;height:3px;margin-top:.6rem;
      background:repeating-linear-gradient(90deg,rgba(255,107,0,.6) 0,rgba(255,107,0,.6) 20px,transparent 20px,transparent 40px);
      animation:fx-splash-road .4s linear infinite;
    }}
  `;
  P.head.appendChild(css);

  /* ── スプラッシュ（セッション初回のみ） ── */
  if (!W.sessionStorage.getItem('fx-splashed')) {{
    W.sessionStorage.setItem('fx-splashed','1');
    var sp = P.createElement('div'); sp.id='fx-splash';
    sp.innerHTML = '<div id="fx-splash-title">🏍 BIKE ROUTE AI</div>' +
      '<div id="fx-splash-sub">AI TOURING PLANNER</div>' +
      '<div id="fx-splash-bar-wrap"><div id="fx-splash-prog"></div></div>' +
      '<div id="fx-splash-road"></div>';
    P.body.appendChild(sp);
    W.setTimeout(function() {{
      sp.style.opacity='0';
      W.setTimeout(function() {{ sp.remove(); }}, 950);
    }}, 2700);
  }}

  /* ── 背景ラッパー ── */
  var wrap = P.createElement('div'); wrap.id='fx-bg';
  P.body.insertBefore(wrap, P.body.firstChild);

  var fall = P.createElement('div'); fall.id='fx-fall'; wrap.appendChild(fall);

  /* ── Aurora ブロブ ── */
  [
    ['rgba(255,80,0,.32)','550px','550px','-80px','15%','20s'],
    ['rgba(255,160,0,.18)','380px','380px','auto','8%','25s','bottom:-60px'],
    ['rgba(180,30,0,.22)','280px','280px','35%','2%','16s'],
    ['rgba(255,100,0,.14)','200px','200px','20%','auto','19s','right:5%'],
  ].forEach(function(p) {{
    var b = P.createElement('div'); b.className='fx-aurora';
    b.style.cssText =
      'width:'+p[2]+';height:'+p[2]+';' +
      'background:radial-gradient(circle,'+p[0]+',transparent 65%);' +
      'top:'+p[3]+';left:'+p[4]+';' +
      (p[6] ? p[6]+';' : '') +
      'animation:fx-aurora '+p[5]+' ease-in-out infinite '+(Math.random()*8)+'s;';
    fall.appendChild(b);
  }});

  /* ── 透視グリッド ── */
  var grid = P.createElement('div'); grid.id='fx-grid'; wrap.appendChild(grid);

  var inner = P.createElement('div');
  inner.style.cssText='position:absolute;inset:0;will-change:transform;';
  wrap.appendChild(inner);

  var overlay = P.createElement('div'); overlay.id='fx-overlay'; wrap.appendChild(overlay);

  /* ── フォト スライドショー ── */
  var slides=[], idx=0, timer=null;
  var dots = P.createElement('div'); dots.id='fx-dots'; P.body.appendChild(dots);

  function show(i) {{
    slides.forEach(function(s,k) {{
      s.el.classList.toggle('on', k===i);
      s.dot.classList.toggle('on', k===i);
    }});
    idx=i;
  }}
  function next() {{ if(slides.length>1) show((idx+1)%slides.length); }}
  function restartTimer() {{ if(timer) W.clearInterval(timer); timer=W.setInterval(next,9000); }}

  URLS.forEach(function(u) {{
    var img=new W.Image();
    img.onload=function() {{
      var d=P.createElement('div'); d.className='fx-slide';
      d.style.backgroundImage='url("'+u+'")'; inner.appendChild(d);
      var dot=P.createElement('div'); dot.className='fx-dot'; dots.appendChild(dot);
      var s={{el:d,dot:dot}}; slides.push(s);
      dot.addEventListener('click', function() {{ show(slides.indexOf(s)); restartTimer(); }});
      if(slides.length===1) {{ show(0); restartTimer(); }}
    }};
    img.src=u;
  }});

  /* ── マウスパララックス & グロー ── */
  var glow=P.createElement('div'); glow.id='fx-glow';
  glow.style.left='50%'; glow.style.top='40%';
  P.body.appendChild(glow);
  var mx=0.5;
  P.addEventListener('mousemove', function(e) {{
    mx=e.clientX/W.innerWidth;
    inner.style.transform=
      'translate('+((mx-.5)*-20)+'px,'+((e.clientY/W.innerHeight-.5)*-13)+'px)';
    glow.style.left=e.clientX+'px'; glow.style.top=e.clientY+'px';
  }});

  /* ── クリックリップル ── */
  P.addEventListener('click', function(e) {{
    var r=P.createElement('div');
    r.style.cssText='position:fixed;width:40px;height:40px;border-radius:50%;pointer-events:none;' +
      'background:rgba(255,107,0,.35);z-index:999998;' +
      'left:'+(e.clientX-20)+'px;top:'+(e.clientY-20)+'px;' +
      'animation:ripple .6s ease-out forwards;';
    P.body.appendChild(r);
    W.setTimeout(function(){{ r.remove(); }}, 650);
  }});

  /* ── Canvas パーティクル（90個 + トレイル） ── */
  var cv=P.createElement('canvas'); cv.id='fx-canvas'; P.body.appendChild(cv);
  var ctx=cv.getContext('2d');
  function resize() {{ cv.width=W.innerWidth; cv.height=W.innerHeight; }} resize();
  W.addEventListener('resize', resize);

  var N=90, parts=[];
  for(var i=0;i<N;i++) {{
    var isLine=Math.random()<.22, isTrail=!isLine&&Math.random()<.2;
    parts.push({{
      x:Math.random()*W.innerWidth, y:Math.random()*W.innerHeight,
      r:Math.random()*2.4+.5,
      vx:-(Math.random()*.9+.2), vy:-(Math.random()*.3+.05),
      a:Math.random()*.55+.12,
      line:isLine, trail:isTrail,
      trail_pts:[],
    }});
  }}

  function tick() {{
    ctx.clearRect(0,0,cv.width,cv.height);
    var speed=1+mx*1.8;
    for(var i=0;i<N;i++) {{
      var p=parts[i];
      p.x+=p.vx*speed; p.y+=p.vy;
      if(p.x<-80||p.y<-20) {{ p.x=cv.width+Math.random()*100; p.y=Math.random()*cv.height; p.trail_pts=[]; }}

      if(p.trail) {{
        p.trail_pts.push([p.x,p.y]);
        if(p.trail_pts.length>18) p.trail_pts.shift();
        for(var j=1;j<p.trail_pts.length;j++) {{
          var a=p.a*(j/p.trail_pts.length)*.5;
          ctx.strokeStyle='rgba(255,160,60,'+a+')';
          ctx.lineWidth=p.r*.5;
          ctx.beginPath();
          ctx.moveTo(p.trail_pts[j-1][0],p.trail_pts[j-1][1]);
          ctx.lineTo(p.trail_pts[j][0],p.trail_pts[j][1]);
          ctx.stroke();
        }}
      }} else if(p.line) {{
        ctx.strokeStyle='rgba(255,140,40,'+p.a*.45+')';
        ctx.lineWidth=p.r*.45;
        ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(p.x+38*speed,p.y+5); ctx.stroke();
      }} else {{
        ctx.fillStyle='rgba(255,170,60,'+p.a+')';
        ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.fill();
      }}
    }}
    W.requestAnimationFrame(tick);
  }}
  tick();

  /* ── KPI カウントアップ（MutationObserver） ── */
  function animCount(el) {{
    if(el.dataset.anim) return;
    var raw=el.textContent.trim(), num=parseFloat(raw);
    if(isNaN(num)||num<=0) return;
    el.dataset.anim='1';
    var t=0,dur=1400,step=16;
    var iv=W.setInterval(function() {{
      t+=step;
      var p=Math.min(t/dur,1), e=1-Math.pow(1-p,3);
      el.textContent=raw.includes('.')?
        (num*e).toFixed(1):Math.round(num*e);
      if(p>=1) {{ el.textContent=raw; W.clearInterval(iv); }}
    }},step);
  }}
  var kpiObs=new MutationObserver(function() {{
    P.querySelectorAll('.kpi-value:not([data-anim])').forEach(animCount);
  }});
  kpiObs.observe(P.body,{{childList:true,subtree:true}});
}})();
</script>
""", height=1)


# ── ヒーローヘッダー ────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="hero-badge">🏍 AI Touring Planner — Japan Edition</div>
    <div class="hero-title">BIKE ROUTE AI</div>
    <div class="road-lines">
        <div class="road-line"></div><div class="road-line"></div><div class="road-line"></div>
    </div>
    <div class="hero-sub">125cc / 50cc ✦ 下道専用 ✦ リアルタイムルート生成</div>
    <div class="hero-divider"></div>
</div>
""", unsafe_allow_html=True)


# ── サイドバー ────────────────────────────────────────────────────
PRESET_DESTS = ["箱根町", "奥多摩", "秩父", "江の島", "日光", "房総半島"]
FUEL_EFF = {"125cc": 50, "50cc": 80}   # km/L
FUEL_PRICE = 175                         # 円/L

def _set_dest(name: str):
    st.session_state["dest_input"] = name

if "dest_input" not in st.session_state:
    st.session_state["dest_input"] = "箱根町"

with st.sidebar:
    st.markdown('<div class="sidebar-title">📍 出発地 / 目的地</div>', unsafe_allow_html=True)
    origin      = st.text_input("出発地", value="東京都新宿区",
                                label_visibility="collapsed", placeholder="例: 東京都新宿区")
    destination = st.text_input("目的地", key="dest_input",
                                label_visibility="collapsed", placeholder="例: 箱根町")

    st.markdown('<div class="sidebar-title">⚡ 人気スポット</div>', unsafe_allow_html=True)
    c3 = st.columns(3)
    for i, name in enumerate(PRESET_DESTS):
        with c3[i % 3]:
            st.button(name, key=f"pre_{i}", use_container_width=True,
                      on_click=_set_dest, args=(name,))

    st.markdown('<div class="sidebar-title">🕐 出発〜帰着</div>', unsafe_allow_html=True)
    time_range = st.slider(
        "time", min_value=dtime(5,0), max_value=dtime(22,0),
        value=(dtime(8,0), dtime(17,0)),
        step=timedelta(minutes=30), format="HH:mm",
        label_visibility="collapsed",
    )
    start_time = time_range[0].strftime("%H:%M")
    end_time   = time_range[1].strftime("%H:%M")
    duration_h = (time_range[1].hour * 60 + time_range[1].minute
                  - time_range[0].hour * 60 - time_range[0].minute) / 60
    st.markdown(f'<div class="sidebar-meta">⏱️ ツーリング時間: <b>{duration_h:.1f}h</b></div>',
                unsafe_allow_html=True)

    st.markdown('<div class="sidebar-title">🔧 排量</div>', unsafe_allow_html=True)
    engine_cc = st.radio("cc", ["125cc","50cc"],
                         label_visibility="collapsed", horizontal=True)

    st.markdown('<div class="sidebar-title">🎯 旅のスタイル</div>', unsafe_allow_html=True)
    travel_style = st.radio(
        "style", ["お任せ","風景","人文"],
        label_visibility="collapsed", horizontal=True,
        help="風景=自然・絶景優先 / 人文=博物館・史跡優先",
    )

    st.markdown('<div class="sidebar-title">⚙️ オプション</div>', unsafe_allow_html=True)
    want_meal = st.checkbox("🍜 飲食店をおすすめする", value=True)
    want_gas  = st.checkbox("⛽ ガソリンスタンドをおすすめする", value=True)

    # 燃費概算
    eff = FUEL_EFF[engine_cc]
    cost100 = int(100 / eff * FUEL_PRICE)
    st.markdown(
        f'<div class="sidebar-meta">⛽ 燃費目安 ({engine_cc}): '
        f'<b>約 ¥{cost100}</b> / 100km</div>',
        unsafe_allow_html=True)

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

    status_box = st.status("🛰️ ルート解析を開始...", expanded=True)
    def show_status(msg):
        status_box.write(msg)
        status_box.update(label=msg)

    try:
        result = run_agent(
            origin=origin, destination=destination,
            start_time=start_time, end_time=end_time,
            engine_cc=engine_cc, want_meal=want_meal, want_gas=want_gas,
            travel_style=travel_style, status_cb=show_status,
        )
    except Exception as e:
        loader_ph.empty()
        status_box.update(label="❌ エラーが発生しました", state="error", expanded=False)
        st.error(f"エラー: {e}")
        st.stop()

    loader_ph.empty()
    status_box.update(label="✅ プラン生成完了！", state="complete", expanded=False)
    st.toast("🏍️ ツーリングプランが完成しました！", icon="🎉")
    st.balloons()

    route    = result.get("route")         or {}
    budget   = result.get("time_budget")   or {}
    timeline = result.get("timeline")      or []
    geometry = result.get("geometry")      or []
    spots    = result.get("spots_for_map") or []

    # ── 難易度バッジ ──
    dist_km  = route.get("distance_km", 0)
    ride_min = budget.get("riding_min", 0)
    if dist_km < 80 or ride_min < 120:
        diff_label, diff_icon, diff_color = "初心者向け", "🟢", "#4CAF50"
    elif dist_km < 200 or ride_min < 300:
        diff_label, diff_icon, diff_color = "中級者向け", "🟡", "#FFC107"
    else:
        diff_label, diff_icon, diff_color = "上級者向け", "🔴", "#FF5722"

    st.markdown(
        f'<div style="text-align:center;margin:.5rem 0">'
        f'<span class="diff-badge" style="color:{diff_color}">'
        f'{diff_icon} {diff_label} — {origin} → {destination}'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    # ── 燃料費 ──
    fuel_cost = int(dist_km / FUEL_EFF[engine_cc] * FUEL_PRICE)

    # ── KPI カード（5枚） ──
    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(5)
    for col, (icon, label, val, unit) in zip(cols, [
        ("🛣️", "DISTANCE",    dist_km,                        "km"),
        ("⏱️", "RIDING TIME", budget.get("riding_min","—"),   "分"),
        ("📍", "SPOTS",       budget.get("n_spots", 0),        "箇所"),
        ("🍜", "MEALS",       budget.get("n_meals", 0),        "回"),
        ("⛽", "FUEL COST",   f"¥{fuel_cost}",                "概算"),
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

    # ── タブ ──
    tab_tl, tab_map, tab_stats = st.tabs(["📋 タイムライン", "🗺️ ルート地図", "📊 統計"])

    # ─── タイムラインタブ（縦型カード） ───
    with tab_tl:
        st.markdown("<br>", unsafe_allow_html=True)
        spot_lookup = {s["name"]: s for s in spots}

        with st.spinner("📡 スポット画像を取得中..."):
            thumbs = {}
            for s in spots:
                if s.get("category") not in ("gas_station", "restaurant"):
                    thumbs[s["name"]] = fetch_wiki_thumb(s["name"])

        cum_km = 0.0
        cards  = ""
        for entry in timeline:
            name     = entry.get("name","")
            arrive   = entry.get("arrive","")
            depart   = entry.get("depart","")
            category = entry.get("category","")
            stay_min = entry.get("stay_min",0)
            dist_km_e= entry.get("dist_km",0)
            cum_km  += dist_km_e

            spot_data = spot_lookup.get(name, {})
            thumb     = thumbs.get(name)
            cat_c     = CAT_COLOR.get(category, "#FF6B00")
            cat_icon  = CAT_ICON.get(category, "📍")
            website   = spot_data.get("website","")
            link_url  = website if website else \
                "https://www.google.com/search?q=" + urllib.parse.quote(name)

            img_cell = (
                f'<img class="tl-thumb" src="{thumb}" alt="{name}">'
                if thumb else
                f'<div class="tl-no-img">{cat_icon}</div>'
            )

            cards += f"""
            <div class="tl-card" style="border-color:{cat_c}22">
                <div class="tl-card" style="position:absolute;left:0;top:0;bottom:0;width:3px;background:{cat_c};border-radius:3px 0 0 3px"></div>
                <div class="tl-node" style="background:#0d0d0d;border-color:{cat_c}"></div>
                <div class="tl-body">
                    {img_cell}
                    <div class="tl-info">
                        <div class="tl-time">{arrive} → {depart}</div>
                        <a class="tl-name" href="{link_url}" target="_blank" rel="noopener">{name}</a>
                        <div class="tl-cat">{cat_icon} {category}</div>
                        <div class="tl-meta">
                            <span class="tl-chip">🚗 +{dist_km_e}km</span>
                            <span class="tl-chip">⏱ {stay_min}分</span>
                            <span class="tl-chip">📍 累計 {round(cum_km,1)}km</span>
                        </div>
                    </div>
                </div>
            </div>"""

        st.markdown(
            f'<div class="tl-wrap">{cards}</div>'
            '<p style="font-size:.7rem;color:rgba(255,255,255,.28);'
            'font-family:\'Noto Sans JP\',sans-serif;margin-top:.4rem">'
            '※ 写真はWikipedia日本語版から取得。名前クリックで公式サイト or Google検索へ。</p>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        plan_text = result.get("plan_text","")
        sections  = []
        for line in plan_text.split("\n"):
            if line.startswith("## タイムライン"):
                break
            sections.append(line)
        overview = "\n".join(sections).strip()
        if overview:
            st.markdown(overview)

        notes_lines, in_notes = [], False
        for line in plan_text.split("\n"):
            if line.startswith("## 注意事項"):
                in_notes = True
            if in_notes:
                notes_lines.append(line)
        if notes_lines:
            st.markdown("\n".join(notes_lines))

        st.markdown("<br>", unsafe_allow_html=True)
        col_dl, col_pr = st.columns(2)
        with col_dl:
            st.download_button("📥 Markdown ダウンロード", data=plan_text,
                               file_name="touring_plan.md", mime="text/markdown",
                               use_container_width=True)
        with col_pr:
            maps_q = urllib.parse.quote(f"{origin} to {destination}")
            st.link_button("🗺️ Google Maps で開く",
                           f"https://www.google.com/maps/dir/{urllib.parse.quote(origin)}/{urllib.parse.quote(destination)}",
                           use_container_width=True)

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
            folium.PolyLine(route_coords, color="#FF6B00", weight=5,
                            opacity=.9, tooltip="下道ルート").add_to(m)
            folium.Marker(route_coords[0],
                popup=folium.Popup(f"🚩 <b>{origin}</b>", max_width=200),
                icon=folium.Icon(color="green",icon="play",prefix="fa")).add_to(m)
            folium.Marker(route_coords[-1],
                popup=folium.Popup(f"🏁 <b>{destination}</b>", max_width=200),
                icon=folium.Icon(color="red",icon="flag",prefix="fa")).add_to(m)

        for spot in spots:
            cat  = spot.get("category","")
            fill = {"restaurant":"#FFB347","gas_station":"#888"}.get(cat, "#FF6B00")
            folium.CircleMarker(
                [spot["lat"],spot["lon"]], radius=9,
                color="#FF6B00", fill=True, fill_color=fill, fill_opacity=.9,
                popup=folium.Popup(
                    f"<b>{spot['name']}</b><br>{CAT_ICON.get(cat,'📍')} {cat}",
                    max_width=220),
                tooltip=spot["name"],
            ).add_to(m)

        from folium.plugins import Fullscreen
        Fullscreen(position="topright").add_to(m)

        st_folium(m, width="100%", height=540, returned_objects=[])
        st.markdown("""
        <div style="display:flex;gap:1.5rem;justify-content:center;margin-top:.8rem;
                    font-family:'Rajdhani',sans-serif;font-size:.85rem;color:rgba(255,255,255,.45);">
            <span>🟢 出発地</span><span>🔴 目的地</span>
            <span><span style="color:#FF6B00">●</span> スポット</span>
            <span><span style="color:#FFB347">●</span> 飲食店</span>
            <span><span style="color:#888">●</span> 給油</span>
        </div>
        """, unsafe_allow_html=True)

    # ─── 統計タブ ───
    with tab_stats:
        st.markdown("<br>", unsafe_allow_html=True)
        if not spots:
            st.info("プランを生成するとここに統計が表示されます。")
        else:
            cat_count = Counter(s.get("category","other") for s in spots)
            max_c = max(cat_count.values(), default=1)

            c_left, c_right = st.columns([1, 1])

            with c_left:
                st.markdown("#### スポット カテゴリ分布")
                if HAS_PLOTLY:
                    labels = [f"{CAT_ICON.get(c,'📍')} {c}" for c in cat_count]
                    vals   = list(cat_count.values())
                    colors = [CAT_COLOR.get(c, "#FF6B00") for c in cat_count]
                    fig = go.Figure(go.Pie(
                        labels=labels, values=vals,
                        marker=dict(colors=colors,
                                    line=dict(color="rgba(0,0,0,.6)", width=1.5)),
                        textinfo="label+percent",
                        textfont=dict(size=11, color="white"),
                        hole=.38,
                    ))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                        legend=dict(font=dict(color="rgba(255,255,255,.6)", size=11)),
                        margin=dict(t=10,b=10,l=10,r=10),
                        height=300,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    bars = ""
                    for cat, cnt in sorted(cat_count.items(), key=lambda x:-x[1]):
                        col = CAT_COLOR.get(cat, "#FF6B00")
                        pct = int(cnt / max_c * 100)
                        bars += f"""
                        <div class="stat-row">
                          <div class="stat-label">{CAT_ICON.get(cat,'📍')} {cat}</div>
                          <div class="stat-bar-wrap">
                            <div class="stat-bar" style="width:{pct}%;background:{col}"></div>
                          </div>
                          <div class="stat-count">{cnt}</div>
                        </div>"""
                    st.markdown(bars, unsafe_allow_html=True)

            with c_right:
                st.markdown("#### ルート サマリー")
                total_stay = sum(e.get("stay_min",0) for e in timeline)
                total_ride = budget.get("riding_min", 0)
                total_time = budget.get("total_min", 0)

                if HAS_PLOTLY:
                    fig2 = go.Figure(go.Bar(
                        x=["移動時間", "観光・食事", "バッファ"],
                        y=[total_ride,
                           total_stay,
                           max(0, total_time - total_ride - total_stay)],
                        marker_color=["#FF6B00","#FFB347","rgba(255,255,255,.2)"],
                        text=[f"{total_ride}分", f"{total_stay}分",
                              f"{max(0,total_time-total_ride-total_stay)}分"],
                        textposition="auto",
                        textfont=dict(color="white"),
                    ))
                    fig2.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                        xaxis=dict(color="rgba(255,255,255,.5)"),
                        yaxis=dict(color="rgba(255,255,255,.5)",
                                   gridcolor="rgba(255,255,255,.08)"),
                        margin=dict(t=10,b=10,l=10,r=10),
                        height=300,
                        bargap=.35,
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                # 数値サマリー
                st.markdown(f"""
                <div style="margin-top:.8rem">
                  <div class="sidebar-meta">🛣️ 総距離: <b>{route.get('distance_km','—')} km</b></div>
                  <div class="sidebar-meta">⏱️ 純移動時間: <b>{total_ride} 分</b></div>
                  <div class="sidebar-meta">🏖️ 総観光時間: <b>{total_stay} 分</b></div>
                  <div class="sidebar-meta">⛽ 概算燃料費: <b>¥{fuel_cost}</b>（{engine_cc} / ¥{FUEL_PRICE}/L）</div>
                  <div class="sidebar-meta">📍 スポット数: <b>{len(spots)} 件</b></div>
                </div>
                """, unsafe_allow_html=True)


else:
    # ── デフォルト画面 ──
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, icon, title, desc in [
        (c1,"🛣️","下道限定ルート","高速・自動車専用道を完全回避。OSRM cycling プロファイルで50cc/125ccどちらも対応。"),
        (c2,"🎯","スタイル別選定","風景派（自然・絶景）か人文派（博物館・史跡）か好みに合わせてスポットを自動選定。"),
        (c3,"📸","写真付きタイムライン","Wikipedia画像と公式サイトリンクを縦型カードで表示。ナビ代わりに使える。"),
        (c4,"📊","詳細統計ビュー","カテゴリ別スポット構成、時間配分、概算燃料費をグラフで確認できる。"),
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
    <div style="text-align:center;padding:1.6rem;background:rgba(0,0,0,.55);
                border:1px solid rgba(255,107,0,.2);border-radius:14px;
                backdrop-filter:blur(8px);animation:fade-in 1s ease-out;">
        <div style="font-family:'Rajdhani',sans-serif;font-size:1.1rem;
                    color:rgba(255,255,255,.55);letter-spacing:.1em;">
            👈 &nbsp;左のサイドバーで条件を設定して
            <span style="color:#FF6B00;font-weight:700;">✦ プランを生成する</span>
            を押してください
        </div>
    </div>
    """, unsafe_allow_html=True)
