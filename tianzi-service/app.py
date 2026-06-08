"""
TianZi Weather Analysis Service

REST API for high-resolution weather analysis using the TianZi model.
Provides endpoints for submitting observation data and retrieving analysis results.

Security: API Key authentication required for all endpoints except /health
          CORS must be restricted to known service origins in production.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Optional, List

import numpy as np
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


sys.path.insert(
    0, os.path.join(
        os.path.dirname(__file__), "..", "common-utils",
        "src", "main", "python")
)

from inference_engine import TianZiEngine  # noqa: E402
from security_middleware import SecurityMiddleware  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tianzi-service")


# ─── Security Configuration ──────────────────────────────────────────────────

# Production mode check — if TIANZI_ENV=production, API key is REQUIRED
_TIANZI_ENV = os.getenv("TIANZI_ENV", "development").lower()
_IS_PRODUCTION = _TIANZI_ENV == "production"

_API_KEY = os.getenv("TIANZI_API_KEY", "")


if not _API_KEY:
    logger.warning(
        "⚠  TIANZI_API_KEY not set \u2014 authentication DISABLED. "
        "Service will run in demo mode with mock data. "
        "Set TIANZI_API_KEY environment variable for full functionality."
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
    logger.info("Loading TianZi model...")
    global _engine
    try:
        _engine = TianZiEngine()
        _engine.load()
        logger.info("TianZi model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load TianZi model: {e}")
        _engine = None
    yield


_engine: Optional[TianZiEngine] = None

app = FastAPI(
    title="TianZi Weather Analysis Service",
    description="High-resolution weather analysis using TianZi deep learning model",
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
    _jwt_middleware = SecurityMiddleware()

    @app.middleware("http")
    async def jwt_auth_middleware(
            request: Request, call_next):
        public_paths = {
            "/health", "/actuator/health", "/health/ready"}
        if request.url.path not in public_paths:
            await _jwt_middleware.verify(request)  # type: ignore[arg-type]
        return await call_next(request)

    logger.info("JWT authentication enabled")


else:
    logger.warning(
        "JWT_SECRET not set — authentication DISABLED. "
        "Set JWT_SECRET environment variable to enable JWT auth."
    )


# ─── Models ─────────────────────────────────────────────────────────────────


class AnalysisRequest(BaseModel):
    observation_data: List[List[List[float]]] = Field(
        description="Observation data grid, shape (variables, lat, lon)"
    )
    background_data: Optional[List[List[List[float]]]] = Field(
        default=None,
        description="Background field data for assimilation, shape (variables, lat, lon)"
    )
    analysis_type: str = Field(
        default="analysis",
        description="Analysis type: 'analysis', 'forecast', 'assimilation'"
    )
    resolution_km: float = Field(
        default=1.0,
        description="Target resolution in kilometers"
    )


class AnalysisResult(BaseModel):
    variable: str
    data: List[List[float]]
    units: str
    description: str


class AnalysisResponse(BaseModel):
    status: str
    model: str
    analysis_type: str
    resolution_km: float
    computation_time_s: float
    results: List[AnalysisResult]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str
    uptime_seconds: float
    api_key_configured: bool
    mode: str  # 'production' or 'demo'


# ─── Startup time ──────────────────────────────────────────────────────────
_start_time = time.time()


# ─── Endpoints ──────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="UP" if (_engine and _engine.is_loaded) else "DEGRADED",
        model_loaded=_engine.is_loaded if _engine else False,
        model_path=_engine.model_path if _engine else "N/A",
        uptime_seconds=time.time() - _start_time,
        api_key_configured=bool(_API_KEY),
        mode="production" if _API_KEY else "demo",
    )


@app.get("/actuator/health", response_model=HealthResponse)
async def actuator_health():
    """Spring Boot Actuator 兼容的健康检查端点。"""
    return await health()


@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe."""
    if _engine and _engine.is_loaded:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Model not loaded")


@app.get("/api/v1/status")
async def get_status():
    """
    Get service configuration status.
    Provides information for frontend to display configuration prompts.
    """
    return {
        "service": "tianzi-service",
        "status": "UP" if (_engine and _engine.is_loaded) else "DEGRADED",
        "api_key_configured": bool(_API_KEY),
        "mode": "production" if _API_KEY else "demo",
        "message": "API key not configured - running in demo mode with limited functionality" 
                   if not _API_KEY else "Service running with full functionality",
        "action_required": not _API_KEY,
        "action_message": "Please configure TIANZI_API_KEY environment variable to enable full functionality"
                          if not _API_KEY else None,
    }


@app.post(
    "/api/v1/analysis",
    response_model=AnalysisResponse,
    dependencies=[Depends(verify_api_key)],
)
async def analyze(request: AnalysisRequest):
    """
    Run TianZi weather analysis.

    Input: Observation data and optional background field.
    Output: High-resolution analysis results.
    """
    if not _engine or not _engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        obs_data = np.array(request.observation_data, dtype=np.float32)
        bg_data = np.array(request.background_data, dtype=np.float32) \
            if request.background_data else None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input data: {e}")

    t0 = time.time()
    try:
        if request.analysis_type == "assimilation" and bg_data is not None:
            results = _engine.assimilate(obs_data, bg_data, resolution_km=request.resolution_km)
        elif request.analysis_type == "forecast":
            results = _engine.predict(obs_data, steps=12, resolution_km=request.resolution_km)
        else:
            results = _engine.analyze(obs_data, resolution_km=request.resolution_km)
    except Exception as e:
        logger.error("Analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")

    elapsed = time.time() - t0

    analysis_results = []
    for var_name, var_data in results.items():  # pyright: ignore[reportAttributeAccessIssue]
        analysis_results.append(AnalysisResult(
            variable=var_name,
            data=var_data.tolist() if isinstance(var_data, np.ndarray) else var_data,
            units=_engine.get_variable_units(var_name),
            description=_engine.get_variable_description(var_name)
        ))

    return AnalysisResponse(
        status="success",
        model=os.path.basename(_engine.model_path),
        analysis_type=request.analysis_type,
        resolution_km=request.resolution_km,
        computation_time_s=round(elapsed, 1),
        results=analysis_results,
    )


@app.post(
    "/api/v1/analysis/wind-field",
    dependencies=[Depends(verify_api_key)],
)
async def wind_field(request: AnalysisRequest):
    """
    Lightweight endpoint — returns only wind field data.
    Useful for UAV path planning quick lookups.
    """
    if not _engine or not _engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        obs_data = np.array(request.observation_data, dtype=np.float32)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input data: {e}")

    results = _engine.get_wind_field(obs_data, resolution_km=request.resolution_km)

    wind_speed = np.sqrt(results['u10']**2 + results['v10']**2)

    return {
        "status": "success",
        "model": os.path.basename(_engine.model_path),
        "resolution_km": request.resolution_km,
        "u10": results['u10'].tolist(),
        "v10": results['v10'].tolist(),
        "wind_speed_avg": float(np.mean(wind_speed)),
        "wind_speed_max": float(np.max(wind_speed)),
        "wind_speed_min": float(np.min(wind_speed)),
    }


@app.get(
    "/api/v1/model/info",
    dependencies=[Depends(verify_api_key)],
)
async def model_info():
    """Return model metadata."""
    if not _engine or not _engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    provider = "unknown"
    if hasattr(_engine, '_session') and _engine._session is not None:
        try:
            provider = _engine._session.get_providers()[0]
        except Exception:
            provider = "unknown"

    return {
        "model": os.path.basename(_engine.model_path),
        "name": "TianZi Weather Analysis Model",
        "version": _engine.version,
        "variables": _engine.N_VARS,
        "max_resolution_km": _engine.MAX_RESOLUTION_KM,
        "supported_analysis_types": ["analysis", "forecast", "assimilation"],
        "provider": provider,
    }
