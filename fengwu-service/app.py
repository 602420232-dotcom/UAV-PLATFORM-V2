"""
FengWu Weather Forecast Service

REST API for global weather forecasting using the FengWu ONNX model.
Provides endpoints for submitting ERA5 data and retrieving forecasts.

Security: API Key authentication required for all endpoints except /health
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from inference_engine import get_engine, FengWuEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fengwu-service")


# ─── Security Configuration ──────────────────────────────────────────────────
_API_KEY = os.getenv("FENGWU_API_KEY", "")
_ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "localhost:3000,localhost:8080").split(",")

def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API Key from request header."""
    if not _API_KEY:
        logger.warning("⚠️  FENGWU_API_KEY not configured — authentication disabled")
        return True
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return True


# ─── Lifespan: load model on startup ───────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading FengWu model...")
    engine = get_engine()
    if not engine or not engine.is_loaded:
        logger.warning(
            "Model not loaded — service will return 503 until model is available. "
            "Ensure model files are mounted at /app/model/"
        )
    yield


app = FastAPI(
    title="FengWu Weather Forecast Service",
    description="Global weather forecasting using FengWu deep learning model",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration - restrict origins in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_ALLOWED_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )
    logger.info(f"🔒 Production CORS enabled for origins: {_ALLOWED_ORIGINS}")
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.warning("⚠️  Development CORS mode — allow all origins")


# ─── Models ─────────────────────────────────────────────────────────────────
class ForecastRequest(BaseModel):
    input_0h: list[list[list[float]]] = Field(
        description="ERA5 atmospheric data at T+0h, shape (69, 721, 1440)"
    )
    input_6h: list[list[list[float]]] = Field(
        description="ERA5 atmospheric data at T+6h, shape (69, 721, 1440)"
    )
    steps: int = Field(default=56, ge=1, le=56, description="Forecast steps (6h each)")
    surface_only: bool = Field(default=True, description="Return surface variables only")


class ForecastStep(BaseModel):
    step: int
    lead_hours: int
    u10: Optional[list[list[float]]] = None
    v10: Optional[list[list[float]]] = None
    t2m: Optional[list[list[float]]] = None
    msl: Optional[list[list[float]]] = None


class ForecastResponse(BaseModel):
    status: str
    model: str
    steps: int
    lead_time_hours: int
    computation_time_s: float
    forecasts: list[ForecastStep]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str
    uptime_seconds: float


# ─── Startup time ──────────────────────────────────────────────────────────
_start_time = time.time()


# ─── Endpoints ──────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
async def health():
    engine = get_engine()
    return HealthResponse(
        status="UP" if (engine and engine.is_loaded) else "DEGRADED",
        model_loaded=engine.is_loaded if engine else False,
        model_path=engine.model_path if engine else "N/A",
        uptime_seconds=time.time() - _start_time,
    )


@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe."""
    engine = get_engine()
    if engine and engine.is_loaded:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Model not loaded")


@app.post("/api/v1/forecast", response_model=ForecastResponse, dependencies=[Depends(verify_api_key)])
async def forecast(request: ForecastRequest):
    """
    Run FengWu weather forecast.

    Input: Two consecutive 6-hour ERA5 frames (69×721×1440).
    Output: Up to 56 forecast steps (14 days).

    The 69 variables are ordered as:
      Surface[0:4]:  u10, v10, t2m, msl
      Level 50hPa:   z, q, u, v, t  (indices 4-8)
      Level 100hPa:  z, q, u, v, t  (indices 9-13)
      ... (13 levels total)
    """
    engine = get_engine()
    if not engine or not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Convert to numpy
    try:
        input_0h = np.array(request.input_0h, dtype=np.float32)
        input_6h = np.array(request.input_6h, dtype=np.float32)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input data: {e}")

    expected_shape = (FengWuEngine.N_VARS, FengWuEngine.N_LAT, FengWuEngine.N_LON)
    if input_0h.shape != expected_shape or input_6h.shape != expected_shape:
        raise HTTPException(
            status_code=400,
            detail=f"Input shape must be {expected_shape}, "
                   f"got {input_0h.shape} and {input_6h.shape}",
        )

    # Run inference
    t0 = time.time()
    try:
        if request.surface_only:
            results = engine.predict_surface(
                input_0h, input_6h, steps=request.steps
            )
        else:
            results = engine.predict(
                input_0h, input_6h, steps=request.steps
            )
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")

    elapsed = time.time() - t0

    # Build response
    forecasts = []
    for i, r in enumerate(results):
        step_data = ForecastStep(step=i, lead_hours=(i + 1) * 6)
        if request.surface_only and isinstance(r, dict):
            step_data.u10 = r.get("u10")
            step_data.v10 = r.get("v10")
            step_data.t2m = r.get("t2m")
            step_data.msl = r.get("msl")
        forecasts.append(step_data)

    return ForecastResponse(
        status="success",
        model=os.path.basename(engine.model_path),
        steps=len(forecasts),
        lead_time_hours=len(forecasts) * 6,
        computation_time_s=round(elapsed, 1),
        forecasts=forecasts,
    )


@app.post("/api/v1/forecast/wind", dependencies=[Depends(verify_api_key)])
async def forecast_wind(request: ForecastRequest):
    """
    Lightweight endpoint — returns only wind speed/direction as grid summary.
    Useful for UAV path planning quick lookups.
    """
    engine = get_engine()
    if not engine or not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    input_0h = np.array(request.input_0h, dtype=np.float32)
    input_6h = np.array(request.input_6h, dtype=np.float32)

    results = engine.predict(input_0h, input_6h, steps=request.steps)

    wind_summary = []
    for step, data in enumerate(results):
        u10 = data[0]  # shape (721, 1440)
        v10 = data[1]
        wind_speed = np.sqrt(u10**2 + v10**2)
        wind_dir = np.arctan2(v10, u10) * 180 / np.pi

        wind_summary.append({
            "step": step,
            "lead_hours": (step + 1) * 6,
            "wind_speed_avg": float(np.mean(wind_speed)),
            "wind_speed_max": float(np.max(wind_speed)),
            "wind_speed_min": float(np.min(wind_speed)),
        })

    return {"status": "success", "model": os.path.basename(engine.model_path), "wind": wind_summary}


@app.get("/api/v1/model/info", dependencies=[Depends(verify_api_key)])
async def model_info():
    """Return model metadata."""
    engine = get_engine()
    if not engine or not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "model": os.path.basename(engine.model_path),
        "variables": FengWuEngine.N_VARS,
        "grid": f"{FengWuEngine.N_LAT}×{FengWuEngine.N_LON}",
        "levels": FengWuEngine.N_LEVELS,
        "max_forecast_steps": 56,
        "max_lead_time": "14 days",
        "step_interval": "6 hours",
        "provider": engine._session.get_providers()[0] if engine._session else "unknown",
    }


# Required for lifespan
import os
