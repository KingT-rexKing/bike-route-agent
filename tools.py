# =============================================
# tools.py  ―  外部APIを叩く関数をまとめたファイル
# =============================================
# このファイルの関数は「AgentがAIに渡せる道具」
# AIが「この道具を使いたい」と言ったら、ここの関数が動く

import math
import time
import requests
import config

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def _overpass_query(query, timeout=35):
    """
    Overpass APIにクエリを投げる。失敗したら2秒待ってリトライ（最大3回）。
    """
    headers = {"User-Agent": "BikeRouteAgent/1.0 (portfolio project)"}
    for attempt in range(3):
        try:
            r = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=timeout)
            if r.status_code == 200 and r.text.strip().startswith("{"):
                return r.json().get("elements", [])
        except Exception:
            pass
        if attempt < 2:
            time.sleep(3)  # リトライ前に3秒待つ（レート制限対策）
    return []


# -----------------------------------------------
# ユーティリティ（内部で使うだけの関数）
# -----------------------------------------------

def _distance_km(lat1, lon1, lat2, lon2):
    """2点間の距離をkm単位で返す（ハーバーサイン公式）"""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _grid_points(geometry, interval_km):
    """
    ルートの座標列から、interval_km おきにサンプリングした点を返す
    → Overpass APIの検索ポイントに使う
    """
    points = []
    distance_accum = 0.0
    prev = None
    for lon, lat in geometry:
        if prev is not None:
            distance_accum += _distance_km(prev[1], prev[0], lat, lon)
        if prev is None or distance_accum >= interval_km:
            points.append((lat, lon))
            distance_accum = 0.0
        prev = (lon, lat)
    # 終点も必ず追加
    if geometry:
        last = geometry[-1]
        points.append((last[1], last[0]))
    return points


def _spot_score(tags):
    """
    OSMのタグ情報からスポットの「おすすめ度」を0〜1で計算する
    スコアが高い順に景点を並べるために使う
    """
    score = 0.3  # ベーススコア
    if tags.get("tourism") in ("attraction", "museum", "viewpoint"):
        score += 0.4
    if tags.get("historic") in ("castle", "ruins", "monument"):
        score += 0.35
    if tags.get("natural") in ("peak", "waterfall", "hot_spring"):
        score += 0.3
    if tags.get("wikipedia") or tags.get("wikidata"):
        score += 0.15  # Wikipediaに載ってるなら有名スポット
    return min(score, 1.0)


# -----------------------------------------------
# Tool 1: 地名 → 緯度経度
# -----------------------------------------------

def geocode_location(place_name):
    """
    地名をGPS座標（緯度・経度）に変換する
    例: "東京駅" → {"lat": 35.68, "lon": 139.76}
    使うAPI: OpenStreetMap の Nominatim（無料）
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1,
        "countrycodes": "jp",  # 日本国内に限定
    }
    headers = {"User-Agent": "BikeRouteAgent/1.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if not data:
            return {"error": f"'{place_name}' が見つかりませんでした"}
        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "display_name": data[0]["display_name"],
        }
    except Exception as e:
        return {"error": str(e)}


# -----------------------------------------------
# Tool 2: ルート取得（下道限定）
# -----------------------------------------------

def get_route(origin_lat, origin_lon, dest_lat, dest_lon, engine_cc):
    """
    OSRMのcyclingプロファイルで下道限定ルートを取得する。
    cyclingプロファイルは高速道路・自動車専用道を自動的に回避するため、
    50cc/125ccどちらにも適した下道ルートになる。
    （パブリックOSRMはexcludeパラメータ非対応のためプロファイルで対応）
    """
    profile = config.OSRM_PROFILE[engine_cc]
    coords  = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    url     = f"https://router.project-osrm.org/route/v1/{profile}/{coords}"
    params  = {
        "overview": "full",
        "geometries": "geojson",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        if data.get("code") != "Ok":
            return {"error": "ルートが見つかりませんでした"}

        route = data["routes"][0]
        return {
            "distance_km": round(route["distance"] / 1000, 1),
            "geometry": route["geometry"]["coordinates"],  # [[lon,lat], ...]
        }
    except Exception as e:
        return {"error": str(e)}


# -----------------------------------------------
# Tool 3: 観光スポット検索
# -----------------------------------------------

def search_spots(geometry, n_spots):
    """
    ルート沿いの観光スポットを検索する
    使うAPI: Overpass API（OpenStreetMapのデータを検索できる無料API）

    やり方:
      1. ルートを15kmおきに分割してグリッド点を作る
      2. 各グリッド点から半径3km以内のスポットを検索
      3. スコアが高い順に並べて上位n_spots件を返す
    """
    grid = _grid_points(geometry, config.GRID_INTERVAL_KM)
    radius = config.SEARCH_RADIUS_M

    # Overpass QL（Overpass API専用のクエリ言語）を組み立てる
    search_blocks = []
    for lat, lon in grid:
        search_blocks.append(f'node["tourism"](around:{radius},{lat},{lon});')
        search_blocks.append(f'node["historic"](around:{radius},{lat},{lon});')
        search_blocks.append(f'node["natural"~"peak|waterfall|hot_spring"](around:{radius},{lat},{lon});')

    query = f'[out:json][timeout:30];({"".join(search_blocks)});out;'
    elements = _overpass_query(query, timeout=35)

    # 重複を除いてスポット一覧を作る
    seen_names = set()
    spots = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:ja")
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        lat = el.get("lat")
        lon = el.get("lon")
        if not lat or not lon:
            continue

        category = (
            tags.get("tourism")
            or tags.get("historic")
            or tags.get("natural")
            or "スポット"
        )

        spots.append({
            "name": name,
            "category": category,
            "lat": lat,
            "lon": lon,
            "score": _spot_score(tags),
            "website": tags.get("website", ""),
            "opening_hours": tags.get("opening_hours", ""),
        })

    # スコアが高い順に並べて上位n件を返す
    spots.sort(key=lambda x: x["score"], reverse=True)
    return {"spots": spots[:n_spots]}


# -----------------------------------------------
# Tool 4: 飲食店検索
# -----------------------------------------------

def search_restaurants(geometry, n_meals):
    """ルート沿いの飲食店を検索する"""
    grid = _grid_points(geometry, config.GRID_INTERVAL_KM * 2)
    radius = config.SEARCH_RADIUS_M

    search_blocks = [
        f'node["amenity"~"restaurant|cafe|ramen_shop"](around:{radius},{lat},{lon});'
        for lat, lon in grid
    ]
    query = f'[out:json][timeout:25];({"".join(search_blocks)});out;'
    elements = _overpass_query(query, timeout=30)

    seen_names = set()
    restaurants = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:ja")
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        lat, lon = el.get("lat"), el.get("lon")
        if not lat or not lon:
            continue

        restaurants.append({
            "name": name,
            "category": "restaurant",
            "lat": lat,
            "lon": lon,
            "cuisine": tags.get("cuisine", ""),
            "score": 0.5,
        })

    # 前半・後半から1軒ずつ選ぶ（食事を分散させるため）
    if len(restaurants) >= 2 and n_meals >= 2:
        mid = len(restaurants) // 2
        selected = [restaurants[0], restaurants[mid]]
    else:
        selected = restaurants[:n_meals]

    return {"restaurants": selected}


# -----------------------------------------------
# Tool 5: ガソリンスタンド検索
# -----------------------------------------------

def search_gas_stations(geometry):
    """ルート中間付近のガソリンスタンドを1件検索する"""
    grid = _grid_points(geometry, config.GRID_INTERVAL_KM * 3)
    radius = config.SEARCH_RADIUS_M

    search_blocks = [
        f'node["amenity"="fuel"](around:{radius},{lat},{lon});'
        for lat, lon in grid
    ]
    query = f'[out:json][timeout:20];({"".join(search_blocks)});out;'
    elements = _overpass_query(query, timeout=25)

    seen_names = set()
    gas_stations = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("brand") or "ガソリンスタンド"
        if name in seen_names:
            continue
        seen_names.add(name)

        lat, lon = el.get("lat"), el.get("lon")
        if not lat or not lon:
            continue

        gas_stations.append({
            "name": name,
            "category": "gas_station",
            "lat": lat,
            "lon": lon,
            "brand": tags.get("brand", ""),
            "score": 0.4,
        })

    # ルートの中間付近を1件返す
    mid = len(gas_stations) // 2
    return {"gas_stations": gas_stations[mid: mid + 1]}


# -----------------------------------------------
# ClaudeにToolを登録する定義（これがないとAIが道具を使えない）
# -----------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "geocode_location",
        "description": "地名・住所を緯度経度に変換する",
        "input_schema": {
            "type": "object",
            "properties": {
                "place_name": {"type": "string", "description": "変換したい地名（例: 東京駅、箱根町）"},
            },
            "required": ["place_name"],
        },
    },
    {
        "name": "get_route",
        "description": "出発地から目的地まで、高速を使わない下道ルートを取得する",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin_lat":  {"type": "number", "description": "出発地の緯度"},
                "origin_lon":  {"type": "number", "description": "出発地の経度"},
                "dest_lat":    {"type": "number", "description": "目的地の緯度"},
                "dest_lon":    {"type": "number", "description": "目的地の経度"},
                "engine_cc":   {"type": "string", "enum": ["50cc", "125cc"]},
            },
            "required": ["origin_lat", "origin_lon", "dest_lat", "dest_lon", "engine_cc"],
        },
    },
    {
        "name": "search_spots",
        "description": "ルート沿いの観光スポットを検索する",
        "input_schema": {
            "type": "object",
            "properties": {
                "geometry": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}},
                    "description": "get_routeで取得したgeometry（[[lon,lat],...]）",
                },
                "n_spots": {"type": "integer", "description": "取得したいスポット数"},
            },
            "required": ["geometry", "n_spots"],
        },
    },
    {
        "name": "search_restaurants",
        "description": "ルート沿いの飲食店を検索する",
        "input_schema": {
            "type": "object",
            "properties": {
                "geometry": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}},
                },
                "n_meals": {"type": "integer"},
            },
            "required": ["geometry", "n_meals"],
        },
    },
    {
        "name": "search_gas_stations",
        "description": "ルート沿いのガソリンスタンドを検索する",
        "input_schema": {
            "type": "object",
            "properties": {
                "geometry": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}},
                },
            },
            "required": ["geometry"],
        },
    },
]
