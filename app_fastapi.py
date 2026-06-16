# =============================================
# app_fastapi.py  ―  FastAPIバックエンド
# =============================================
#
# 起動方法:
#   uvicorn app_fastapi:app --reload --port 8000
#
# エンドポイント:
#   GET  /         → static/index.html を返す
#   POST /api/plan → agent.py を呼んでプランをJSON返す

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import agent

app = FastAPI()


class PlanRequest(BaseModel):
    origin: str
    destination: str
    start_time: str
    end_time: str
    engine_cc: str
    want_meal: bool
    want_gas: bool
    travel_style: str = "お任せ"


@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.post("/api/plan")
def create_plan(req: PlanRequest):
    try:
        result = agent.run_agent(
            req.origin,
            req.destination,
            req.start_time,
            req.end_time,
            req.engine_cc,
            req.want_meal,
            req.want_gas,
            req.travel_style,
            status_cb=None,
        )
        return {
            "plan_text": result["plan_text"],
            "distance_km": result["route"]["distance_km"],
            "timeline": result["timeline"],
            "geometry": result["geometry"],
            "time_budget": result["time_budget"],
            "spots_for_map": result["spots_for_map"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 静的ファイル（CSS/JS等）の配信
app.mount("/static", StaticFiles(directory="static"), name="static")
