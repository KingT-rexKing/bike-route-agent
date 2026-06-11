# =============================================
# config.py  ―  設定値をまとめたファイル
# =============================================
# 「なぜ別ファイルにするか」
#   → 数字をここだけ変えればアプリ全体に反映されるから

# --- 道路設定 ---
# OSRMのルーティングプロファイル
# cyclingプロファイルは自動的に高速・自動車専用道を回避する
# → パブリックOSRMはexcludeパラメータ非対応のため、プロファイル切り替えで対応
OSRM_PROFILE = {
    "50cc":  "cycling",  # 自転車ルート = 高速・幹線を自然に回避
    "125cc": "cycling",  # 同上（125ccも下道専用として同じプロファイルを使用）
}

# バイクの実際の平均速度（信号・渋滞込みの現実的な値）
AVG_SPEED_KMH = {
    "50cc":  28,
    "125cc": 45,
}

# --- 時間配分の設定 ---
BUFFER_RATIO   = 0.10   # 総時間の10%をバッファ（道に迷う・休憩など）
MIN_STAY_MIN   = 10     # 景点に最低10分は滞在する
MAX_STAY_MIN   = 60     # 景点に最長60分まで滞在する
MEAL_TIME_MIN  = 45     # 食事に45分
GAS_TIME_MIN   = 10     # 給油に10分

# カテゴリ別の標準滞在時間（分）
# 観景台・自然系は短く、博物館・城は長く設定
STAY_TIME_BY_CATEGORY = {
    "viewpoint":   15,
    "peak":        20,
    "waterfall":   20,
    "hot_spring":  30,
    "beach":       20,
    "park":        20,
    "natural":     20,
    "museum":      50,
    "castle":      50,
    "historic":    40,
    "ruins":       30,
    "monument":    20,
    "attraction":  30,
    "artwork":     20,
    "gallery":     30,
    "restaurant":  40,
    "cafe":        30,
    "gas_station": 10,
}
STAY_TIME_DEFAULT = 25  # カテゴリが不明な場合のデフォルト

# --- POI（観光スポット）検索の設定 ---
SEARCH_RADIUS_M   = 3000   # ルートから左右3km以内を検索
GRID_INTERVAL_KM  = 15     # 15kmおきに検索ポイントを置く
MAX_SPOTS         = 6      # 最大6箇所まで候補を返す
