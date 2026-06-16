"""
Step 3 コアアルゴリズム: 時間分配エンジン
自由時間から景点数・停留時間を動的に決定する
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from config import TIME_CONFIG


@dataclass
class SpotCandidate:
    name: str
    category: str           # tourism / historic / natural / leisure / restaurant / gas
    lat: float
    lon: float
    distance_from_route_m: float
    priority_score: float   # 0.0〜1.0 (OSM tagsから算出)
    estimated_stay_min: Optional[int] = None   # 確定後に入る


@dataclass
class TimelineEntry:
    order: int
    spot: SpotCandidate
    arrive_time: str        # "HH:MM"
    depart_time: str        # "HH:MM"
    stay_min: int
    leg_distance_km: float  # 前地点からの距離
    leg_time_min: int       # 前地点からの移動時間


@dataclass
class TimeBudget:
    total_min: int
    riding_min: int
    free_min: int
    buffer_min: int
    available_min: int      # free - buffer
    n_spots: int
    n_meals: int
    n_gas: int


def parse_time(t: str) -> int:
    """'HH:MM' -> 分(0:00からの経過分)"""
    h, m = map(int, t.split(":"))
    return h * 60 + m


def format_time(minutes: int) -> str:
    """分(0:00起点) -> 'HH:MM'"""
    minutes = max(0, minutes)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def calc_riding_time(distance_km: float, engine_cc: str) -> int:
    """距離と排量から純粋な移動時間(分)を算出"""
    avg_speed = TIME_CONFIG["avg_speed"][engine_cc]
    return int((distance_km / avg_speed) * 60)


def compute_time_budget(
    start_time: str,
    end_time: str,
    riding_distance_km: float,
    engine_cc: str,
    want_meal: bool,
    want_gas: bool,
) -> TimeBudget:
    """
    総時間予算から自由時間を計算し、景点数・食事・給油の数を動的決定する

    アルゴリズム:
    1. 総時間 = end_time - start_time
    2. 純移動時間 = distance / avg_speed
    3. 自由時間 = 総時間 - 純移動時間
    4. バッファ = 総時間 * buffer_ratio
    5. 実可用時間 = 自由時間 - バッファ
    6. 食事・給油の時間を差し引いた残りで景点数を算出
    """
    cfg = TIME_CONFIG

    total_min = parse_time(end_time) - parse_time(start_time)
    if total_min <= 0:
        raise ValueError(f"終了時刻は開始時刻より後にしてください: {start_time} → {end_time}")

    riding_min = calc_riding_time(riding_distance_km, engine_cc)
    free_min = total_min - riding_min
    buffer_min = int(total_min * cfg["buffer_ratio"])
    available_min = free_min - buffer_min

    # 食事・給油のスロットを確保
    n_meals = 0
    n_gas = 0
    meal_total = 0
    gas_total = 0

    if want_meal and available_min >= cfg["meal_time_min"]:
        # 6時間以上なら2食、それ以外は1食
        if total_min >= 360 and available_min >= cfg["meal_time_min"] * 2:
            n_meals = 2
        else:
            n_meals = 1
        meal_total = n_meals * cfg["meal_time_min"]

    if want_gas and available_min - meal_total >= cfg["gas_time_min"]:
        n_gas = 1
        gas_total = cfg["gas_time_min"]

    remaining_for_spots = available_min - meal_total - gas_total

    # 景点数 = 残り時間 ÷ 平均停留時間(min_とmax_の中間値)
    avg_stay = (cfg["min_spot_stay_min"] + cfg["max_spot_stay_min"]) // 2
    n_spots = max(0, remaining_for_spots // avg_stay)
    n_spots = min(n_spots, 5)   # 上限5箇所

    return TimeBudget(
        total_min=total_min,
        riding_min=riding_min,
        free_min=free_min,
        buffer_min=buffer_min,
        available_min=available_min,
        n_spots=n_spots,
        n_meals=n_meals,
        n_gas=n_gas,
    )


def allocate_stay_times(
    spots: list[SpotCandidate],
    budget: TimeBudget,
) -> list[SpotCandidate]:
    """
    priority_scoreに基づき各景点の停留時間を配分する
    高スコアの景点により多くの時間を割り当てる（加重配分）
    """
    cfg = TIME_CONFIG
    if not spots:
        return spots

    spot_budget = budget.available_min - budget.n_meals * cfg["meal_time_min"] - budget.n_gas * cfg["gas_time_min"]
    spot_budget = max(spot_budget, len(spots) * cfg["min_spot_stay_min"])

    total_score = sum(s.priority_score for s in spots) or 1.0
    assigned = []
    remaining = spot_budget

    for i, spot in enumerate(spots):
        if i == len(spots) - 1:
            stay = remaining
        else:
            stay = int((spot.priority_score / total_score) * spot_budget)

        stay = max(cfg["min_spot_stay_min"], min(cfg["max_spot_stay_min"], stay))
        spot.estimated_stay_min = stay
        assigned.append(spot)
        remaining -= stay
        if remaining <= 0:
            break

    return assigned


def build_timeline(
    start_time: str,
    spots: list[SpotCandidate],
    leg_distances_km: list[float],
    leg_times_min: list[int],
) -> list[TimelineEntry]:
    """
    出発時刻・各区間距離・停留時間から完全なタイムラインを構築する
    """
    cursor = parse_time(start_time)
    timeline: list[TimelineEntry] = []

    for i, spot in enumerate(spots):
        leg_dist = leg_distances_km[i] if i < len(leg_distances_km) else 0.0
        leg_time = leg_times_min[i] if i < len(leg_times_min) else 0

        cursor += leg_time
        arrive = format_time(cursor)
        stay = spot.estimated_stay_min or 30
        cursor += stay
        depart = format_time(cursor)

        timeline.append(TimelineEntry(
            order=i + 1,
            spot=spot,
            arrive_time=arrive,
            depart_time=depart,
            stay_min=stay,
            leg_distance_km=leg_dist,
            leg_time_min=leg_time,
        ))

    return timeline
