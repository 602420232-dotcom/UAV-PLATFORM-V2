"""
FengWu Weather Forecast Service

REST API for global weather forecasting using the FengWu ONNX model.
Provides endpoints for submitting ERA5 data and retrieving forecasts.

Security: API Key authentication required for all endpoints except /health
          CORS must be restricted to known service origins in production.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Optional

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "common-utils", "src", "main", "python")
)

import numpy as np
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from inference_engine import get_engine, FengWuEngine
from security_middleware import SecurityMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fengwu-service")


# ─── Security Configuration ──────────────────────────────────────────────────

# Production mode check — if FENGWU_ENV=production, API key is REQUIRED
_FENGWU_ENV = os.getenv("FENGWU_ENV", "development").lower()
_IS_PRODUCTION = _FENGWU_ENV == "production"

_API_KEY = os.getenv("FENGWU_API_KEY", "")
if not _API_KEY:
    if _IS_PRODUCTION:
        raise RuntimeError(
            "FENGWU_API_KEY is required in production mode. "
            "Set FENGWU_API_KEY environment variable before starting the service."
        )
    logger.warning(
        "⚠  FENGWU_API_KEY not set \u2014 authentication DISABLED. "
        "Set FENGWU_API_KEY environment variable for production."
    )


def verify_api_key(
    x_api_key: str = Header(default="", alias="X-API-Key"),
):
    if not _API_KEY:
        return True

    if not x_api_key:
        logger.warning("Authentication failed: missing X-API-Key header")
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    if x_api_key != _API_KEY:
        logger.warning("Authentication failed: invalid API key")
        raise HTTPException(status_code=401, detail="Invalid API Key")

    return True


# ─── CORS Configuration ──────────────────────────────────────────────────────
# Must be set via CORS_ORIGINS environment variable.
# Development defaults allow localhost origins only.
_cors_origins_str = os.getenv("CORS_ORIGINS")
if _cors_origins_str:
    _ALLOWED_ORIGINS = [o.strip() for o in _cors_origins_str.split(",")]
    logger.info("CORS configured for origins: %s", _ALLOWED_ORIGINS)
else:
    _ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8080"]
    if _IS_PRODUCTION:
        raise RuntimeError(
            "CORS_ORIGINS is required in production mode. "
            "Set CORS_ORIGINS environment variable before starting the service."
        )
    logger.warning(
        "CORS_ORIGINS not set, using development defaults: %s. "
        "Set CORS_ORIGINS environment variable for production.",
        _ALLOWED_ORIGINS,
    )


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

# CORS configuration - restrict to explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)
logger.info("🔒 CORS enabled for origins: %s", _ALLOWED_ORIGINS)

# JWT 认证中间件（与 Java 后端共享 JWT_SECRET，补充 API Key 认证）
_jwt_secret = os.getenv("JWT_SECRET", "") or os.getenv("JWT_SECRET_KEY", "")
_jwt_middleware = None
if _jwt_secret:
    _jwt_middleware = SecurityMiddleware(
        secret_key=_jwt_secret,
        algorithm="HS512",
    )
    _jwt_middleware.protect_app(
        app,
        public_paths=["/health", "/actuator/health", "/health/ready"],
    )
    logger.info("JWT authentication enabled")
else:
    logger.warning(
        "JWT_SECRET not set — authentication DISABLED. "
        "Set JWT_SECRET environment variable to enable JWT auth."
    )


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


@app.get("/actuator/health", response_model=HealthResponse)
async def actuator_health():
    """Spring Boot Actuator 兼容的健康检查端点。"""
    return await health()


@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe."""
    engine = get_engine()
    if engine and engine.is_loaded:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Model not loaded")


@app.post(
    "/api/v1/forecast",
    response_model=ForecastResponse,
    dependencies=[Depends(verify_api_key)],
)
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


@app.post(
    "/api/v1/forecast/wind",
    dependencies=[Depends(verify_api_key)],
)
async def forecast_wind(request: ForecastRequest):
    """
    Lightweight endpoint — returns only wind speed/direction as grid summary.
    Useful for UAV path planning quick lookups.
    """
    engine = get_engine()
    if not engine or not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        input_0h = np.array(request.input_0h, dtype=np.float32)
        input_6h = np.array(request.input_6h, dtype=np.float32)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input data: {e}")

    results = engine.predict(input_0h, input_6h, steps=request.steps)

    wind_summary = []
    for step, data in enumerate(results):
        if isinstance(data, dict):
            u10 = data.get("u10")
            v10 = data.get("v10")
            if u10 is None or v10 is None:
                continue
        elif isinstance(data, (list, np.ndarray)) and len(data) >= 2:
            u10 = data[0]
            v10 = data[1]
        else:
            continue

        wind_speed = np.sqrt(u10**2 + v10**2)

        wind_summary.append({
            "step": step,
            "lead_hours": (step + 1) * 6,
            "wind_speed_avg": float(np.mean(wind_speed)),
            "wind_speed_max": float(np.max(wind_speed)),
            "wind_speed_min": float(np.min(wind_speed)),
        })

    return {
        "status": "success",
        "model": os.path.basename(engine.model_path),
        "wind": wind_summary,
    }


@app.get(
    "/api/v1/model/info",
    dependencies=[Depends(verify_api_key)],
)
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



