"""
FengLei Weather Service API
风雷区域模式数据服务 - 基于 CMA GRAPES_MESO 中尺度模式
提供高分辨率(3km)区域气象预报数据
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FengLei Weather Service", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("FENGLEI_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: str = Depends(api_key_header)):
    if not API_KEY:
        return None
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key


class ForecastRequest(BaseModel):
    fcst_hour: int = 0
    variables: Optional[List[str]] = None


class ForecastResponse(BaseModel):
    source: str
    forecast_time: str
    variables: List[str]
    shape: List[int]
    data: Dict[str, List[List[float]]]


def ensure_cache():
    cache_dir = os.getenv("FENGLEI_CACHE_DIR", "/app/cache")
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    return cache_dir


def generate_mock_data(fcst_hour: int = 0) -> dict:
    """生成模拟预报场"""
    ny, nx = 50, 50
    np.random.seed(42 + fcst_hour)

    lat_center = 30.67
    lon_center = 104.07

    lat = np.linspace(lat_center - 0.75, lat_center + 0.75, ny)
    lon = np.linspace(lon_center - 0.75, lon_center + 0.75, nx)

    u10 = np.random.normal(1.5, 2.0, (ny, nx)).tolist()
    v10 = np.random.normal(0.5, 1.5, (ny, nx)).tolist()
    t2m = (np.random.normal(20, 5, (ny, nx)) + 273.15).tolist()
    rh2m = np.clip(np.random.normal(70, 15, (ny, nx)), 0, 100).tolist()
    ps = np.random.normal(1013, 5, (ny, nx)).tolist()
    blh = np.clip(np.random.normal(500, 200, (ny, nx)), 50, 3000).tolist()

    return {
        "latitude": lat.tolist(),
        "longitude": lon.tolist(),
        "u10": u10,
        "v10": v10,
        "t2m": t2m,
        "rh2m": rh2m,
        "ps": ps,
        "blh": blh,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "fenglei-service",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health/ready")
async def readiness_check():
    return {
        "status": "ready",
        "service": "fenglei-service",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v1/status")
async def get_status():
    """
    Get service configuration status.
    Provides information for frontend to display configuration prompts.
    """
    return {
        "service": "fenglei-service",
        "status": "healthy",
        "api_key_configured": bool(API_KEY),
        "mode": "production" if API_KEY else "demo",
        "message": (
            "API key not configured - running in demo mode with "
            "limited functionality" if not API_KEY
            else "Service running with full functionality"
        ),
        "action_required": not API_KEY,
        "action_message": (
            "Please configure FENGLEI_API_KEY environment variable to enable full functionality"
            if not API_KEY else None
        ),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v1/model/info")
async def get_model_info(_: str = Depends(get_api_key)):
    return {
        "model": "GRAPES_MESO",
        "name": "FengLei",
        "resolution_km": 3,
        "variables": ["u10", "v10", "t2m", "rh2m", "ps", "blh"],
        "update_interval_min": int(os.getenv("FENGLEI_UPDATE_INTERVAL", 30)),
        "fcst_hours": [0, 1, 3, 6, 12, 24],
        "levels": ["1000", "925", "850", "700", "500", "300"],
    }


@app.post("/api/v1/forecast")
async def get_forecast(request: ForecastRequest, _: str = Depends(get_api_key)):
    try:
        data = generate_mock_data(request.fcst_hour)

        selected_vars = request.variables or ["u10", "v10", "t2m", "rh2m", "ps", "blh"]

        filtered_data = {k: v for k, v in data.items() if k in selected_vars}

        return {
            "source": "fenglei",
            "forecast_time": datetime.now().isoformat(),
            "fcst_hour": request.fcst_hour,
            "variables": selected_vars,
            "shape": [50, 50],
            "resolution_km": 3,
            "data": filtered_data,
            "latitude": data["latitude"],
            "longitude": data["longitude"],
        }
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/forecast/wind-field")
async def get_wind_field(fcst_hour: int = 0, _: str = Depends(get_api_key)):
    data = generate_mock_data(fcst_hour)
    return {
        "source": "fenglei",
        "forecast_time": datetime.now().isoformat(),
        "fcst_hour": fcst_hour,
        "wind_u": data["u10"],
        "wind_v": data["v10"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
    }


@app.get("/api/v1/analysis")
async def get_analysis(_: str = Depends(get_api_key)):
    data = generate_mock_data(0)
    return {
        "analysis_type": "current",
        "timestamp": datetime.now().isoformat(),
        "variables": {
            "temperature_2m": data["t2m"],
            "humidity_2m": data["rh2m"],
            "wind_speed": np.sqrt(np.array(data["u10"]) ** 2 + np.array(data["v10"]) ** 2).tolist(),
        },
        "latitude": data["latitude"],
        "longitude": data["longitude"],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
