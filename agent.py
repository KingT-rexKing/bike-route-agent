# =============================================
# agent.py  ―  AIエージェントのメインロジック
# =============================================
#
# 【設計思想】
#   「確実に順番通りに実行すべき処理」はPythonで直接呼ぶ
#   「AIに判断させたい処理」だけAIのツールループに任せる
#
#   Step1: geocode（地名→座標）       → Python直接呼び出し
#   Step2: get_route（ルート取得）     → Python直接呼び出し
#   Step3: 時間配分計算               → Pythonの数式
#   Step4: POI検索（スポット等）       → AIのツールループ
#   Step5: タイムライン文書生成        → AIが文章を書く

import json
import os
import math
import anthropic
from dotenv import load_dotenv

import config
import tools

load_dotenv()


# -----------------------------------------------
# Step 3: 時間配分アルゴリズム
# -----------------------------------------------

def calc_time_budget(start_time, end_time, distance_km, engine_cc, want_meal, want_gas):
    """
    ルートの距離と出発/帰着時刻から「何箇所スポットに寄れるか」を計算する

    計算式:
      総時間  = 帰着 - 出発
      移動時間 = 距離 ÷ 平均速度
      自由時間 = 総時間 - 移動時間
      バッファ = 総時間 × 10%
      使える時間 = 自由時間 - バッファ - 食事 - 給油
      景点数   = 使える時間 ÷ 景点1件の平均時間
    """
    def to_min(t):
        h, m = map(int, t.split(":"))
        return h * 60 + m

    total_min  = to_min(end_time) - to_min(start_time)
    speed      = config.AVG_SPEED_KMH[engine_cc]
    riding_min = int(distance_km / speed * 60)
    free_min   = total_min - riding_min
    buffer_min = int(total_min * config.BUFFER_RATIO)

    n_meals = 0
    meal_min = 0
    if want_meal:
        n_meals  = 2 if total_min >= 360 else 1
        meal_min = config.MEAL_TIME_MIN * n_meals

    n_gas   = 1 if want_gas else 0
    gas_min = config.GAS_TIME_MIN * n_gas

    available_min = free_min - buffer_min - meal_min - gas_min
    avg_stay  = (config.MIN_STAY_MIN + config.MAX_STAY_MIN) // 2
    n_spots   = max(0, min(available_min // avg_stay, config.MAX_SPOTS))

    return {
        "total_min":   total_min,
        "riding_min":  riding_min,
        "free_min":    free_min,
        "n_spots":     n_spots,
        "n_meals":     n_meals,
        "n_gas":       n_gas,
    }


def assign_stay_times(spots, available_min):
    """スコアの比率で各スポットの滞在時間を配分する"""
    if not spots:
        return spots
    total_score = sum(s.get("score", 0.5) for s in spots) or 1.0
    for spot in spots:
        stay = int((spot.get("score", 0.5) / total_score) * available_min)
        stay = max(config.MIN_STAY_MIN, min(config.MAX_STAY_MIN, stay))
        spot["stay_min"] = stay
    return spots


def build_timeline(start_time, stops, geometry):
    """ストップをルート順に並べて到着・出発時刻を計算する"""
    def to_min(t):
        h, m = map(int, t.split(":"))
        return h * 60 + m

    def to_str(minutes):
        return f"{max(0, minutes) // 60:02d}:{max(0, minutes) % 60:02d}"

    def route_pos(lat, lon):
        """このスポットがルート上のどの位置か（0=出発 〜 1=目的地）"""
        best_i, min_d = 0, float("inf")
        for i, (glon, glat) in enumerate(geometry):
            d = (lat - glat) ** 2 + (lon - glon) ** 2
            if d < min_d:
                min_d, best_i = d, i
        return best_i / max(len(geometry) - 1, 1)

    stops.sort(key=lambda s: route_pos(s["lat"], s["lon"]))

    timeline = []
    cursor   = to_min(start_time)
    prev_lat = geometry[0][1]
    prev_lon = geometry[0][0]

    for i, stop in enumerate(stops):
        dist_km = math.sqrt((stop["lat"] - prev_lat) ** 2 + (stop["lon"] - prev_lon) ** 2) * 111
        leg_min = max(1, int(dist_km / config.AVG_SPEED_KMH.get("125cc", 45) * 60))

        cursor += leg_min
        arrive  = to_str(cursor)
        stay    = stop.get("stay_min", config.MIN_STAY_MIN)
        cursor += stay
        depart  = to_str(cursor)

        timeline.append({
            "order":    i + 1,
            "name":     stop["name"],
            "category": stop["category"],
            "arrive":   arrive,
            "depart":   depart,
            "stay_min": stay,
            "dist_km":  round(dist_km, 1),
        })
        prev_lat, prev_lon = stop["lat"], stop["lon"]

    return timeline


# -----------------------------------------------
# Step 4: AIツールループ（POI検索のみ担当）
# -----------------------------------------------

def search_pois_direct(geometry, budget, want_meal, want_gas, log):
    """
    Pythonで直接POI検索APIを呼ぶ。
    AIのツールループを使わずに確実に実行する。
    （AIにgeometryを渡してツール呼び出しさせると
      座標が切り詰められてうまく動かないため直接呼び出しに変更）
    """
    all_stops = []

    if budget["n_spots"] > 0:
        log("🏯 観光スポットを検索中...")
        result = tools.search_spots(geometry, budget["n_spots"])
        spots = result.get("spots", [])
        all_stops.extend(spots)
        log(f"   → {len(spots)} 件発見")

    if want_meal and budget["n_meals"] > 0:
        log("🍜 飲食店を検索中...")
        result = tools.search_restaurants(geometry, budget["n_meals"])
        restaurants = result.get("restaurants", [])
        all_stops.extend(restaurants)
        log(f"   → {len(restaurants)} 件発見")

    if want_gas and budget["n_gas"] > 0:
        log("⛽ ガソリンスタンドを検索中...")
        result = tools.search_gas_stations(geometry)
        gas = result.get("gas_stations", [])
        all_stops.extend(gas)
        log(f"   → {len(gas)} 件発見")

    return all_stops


# -----------------------------------------------
# メインのAgent関数
# -----------------------------------------------

def run_agent(origin, destination, start_time, end_time,
              engine_cc, want_meal, want_gas, status_cb=None):
    """全体を動かすメイン関数"""

    def log(msg):
        if status_cb:
            status_cb(msg)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # =============================================
    # Step 1: 地名 → 座標（Python直接呼び出し）
    # =============================================
    log("📍 Step1: 座標を取得中...")

    origin_geo = tools.geocode_location(origin)
    if "error" in origin_geo:
        raise ValueError(f"出発地が見つかりません: {origin_geo['error']}")

    dest_geo = tools.geocode_location(destination)
    if "error" in dest_geo:
        raise ValueError(f"目的地が見つかりません: {dest_geo['error']}")

    log(f"   出発: {origin_geo['display_name'][:30]}")
    log(f"   目的地: {dest_geo['display_name'][:30]}")

    # =============================================
    # Step 2: ルート取得（Python直接呼び出し）
    # =============================================
    log("🛣️ Step2: 下道ルートを計算中...")

    route = tools.get_route(
        origin_lat=origin_geo["lat"],
        origin_lon=origin_geo["lon"],
        dest_lat=dest_geo["lat"],
        dest_lon=dest_geo["lon"],
        engine_cc=engine_cc,
    )
    if "error" in route:
        raise ValueError(f"ルート取得失敗: {route['error']}")

    log(f"✅ ルート: {route['distance_km']}km")

    # =============================================
    # Step 3: 時間配分計算（Python数式）
    # =============================================
    log("⏱️ Step3: 時間を配分中...")

    budget = calc_time_budget(
        start_time, end_time,
        route["distance_km"], engine_cc,
        want_meal, want_gas,
    )
    log(f"   景点:{budget['n_spots']} 食事:{budget['n_meals']} GS:{budget['n_gas']}")

    # =============================================
    # Step 4: POI検索（AIツールループ）
    # =============================================
    log("🔍 Step4: 沿道スポットを検索中...")

    all_stops = search_pois_direct(
        route["geometry"], budget, want_meal, want_gas, log
    )
    log(f"   合計 {len(all_stops)} 件のスポットを収集")

    # 上位スポットに絞って停留時間を配分
    n_total   = budget["n_spots"] + budget["n_meals"] + budget["n_gas"]
    top_stops = sorted(all_stops, key=lambda x: x.get("score", 0.5), reverse=True)[:n_total]

    spots_time = (
        budget["free_min"]
        - int(budget["total_min"] * config.BUFFER_RATIO)
        - budget["n_meals"] * config.MEAL_TIME_MIN
        - budget["n_gas"]   * config.GAS_TIME_MIN
    )
    top_stops = assign_stay_times(top_stops, max(spots_time, 0))

    # タイムラインを構築
    timeline = build_timeline(start_time, top_stops, route["geometry"]) if top_stops else []

    # =============================================
    # Step 5: AI がMarkdownプランを生成
    # =============================================
    log("📋 Step5: プランを生成中...")

    plan_prompt = f"""
以下のデータを使ってツーリングプランをMarkdown形式で書いてください。

【条件】
- 出発地: {origin}  → 目的地: {destination}
- 出発: {start_time}  帰着目標: {end_time}
- 排量: {engine_cc}（高速道路は走れない）
- 総距離: {route['distance_km']} km
- 純移動時間: {budget['riding_min']} 分

【タイムラインデータ】
```json
{json.dumps(timeline, ensure_ascii=False, indent=2)}
```

【出力フォーマット】
## ツーリング概要
（総距離・移動時間・景点数などを箇条書き）

## タイムライン
（Markdownテーブル: 時刻 | 場所 | カテゴリ | 滞在 | メモ）

## 注意事項
（道路規制・{engine_cc}の制限・給油タイミングなど）
"""

    final = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system="あなたはバイクツーリングの専門家です。実用的で具体的なプランを書いてください。",
        messages=[{"role": "user", "content": plan_prompt}],
    )

    plan_text = "".join(
        block.text for block in final.content if hasattr(block, "text")
    )

    return {
        "plan_text":     plan_text,
        "route":         route,
        "time_budget":   budget,
        "timeline":      timeline,
        "geometry":      route["geometry"],
        "spots_for_map": top_stops,
    }
