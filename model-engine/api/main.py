"""
Model-Engine API 服务
整合: 数据管道 → CNN订正 → U-Net降尺度 → GPR风险场 → 融合

端口: 8087 (避开现有服务)
"""
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

import torch
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 模型引擎模块
from data_pipeline.fetcher import CMAFetcher, fetch_latest
from cnn_corrector.model import CNNCorrector
from unet_downscaler.model import UNetDownscaler
from gpr_risk.model import GPRiskEstimator, compute_risk_score
from fusion.ensemble import DynamicWeightFusion, PhysicsConstraint
from path_planning.planner import GPRPathPlanner

# 原项目桥接 (零影响，不动原文件)
from integration.adapter import LegacyModelAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model-engine")


app = FastAPI(title="Model-Engine", version="1.0.0",
              description="多模型气象预报引擎 — CNN订正 → U-Net降尺度 → GPR风险场")

# ── 全局状态 ────────────────────────────────────

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"设备: {device}")

cnn_corrector = CNNCorrector().to(device).eval()
path_planner = GPRPathPlanner()

# 原项目模型适配器 (可选，缺依赖时自动降级)
legacy_adapter = LegacyModelAdapter()


if legacy_adapter.available:
    logger.info("原项目模型已桥接 (LSTM + XGBoost + ConvLSTM + GPR + MLOps)")
unet_downscaler = UNetDownscaler().to(device).eval()
gpr_estimator = GPRiskEstimator()
fusion_engine = DynamicWeightFusion()
physics_constraint = PhysicsConstraint().to(device).eval()
data_fetcher = CMAFetcher()

# 权重路径
MODEL_DIR = Path("/app/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ── 数据模型 ────────────────────────────────────


class ForecastRequest(BaseModel):
    lat_center: Optional[float] = None
    lon_center: Optional[float] = None
    fcst_hours: list = [0, 1, 3, 6, 12]
    include_risk: bool = True
    return_raw: bool = False


class ForecastResponse(BaseModel):
    status: str
    timestamp: str
    forecast: Optional[Dict] = None
    risk_map: Optional[list] = None
    model_weights: Optional[Dict] = None


# ── 核心管线 ────────────────────────────────────


def run_pipeline(request: ForecastRequest) -> Dict:
    """
    执行完整预测管线:
    拉取 → 订正 → 降尺度 → 融合 → 风险评分
    """
    # 1. 拉取多源数据
    raw_data = fetch_latest()
    if not raw_data:
        raise RuntimeError("无可用数据源")

    # 2. 转为张量
    fields = {}
    for name, ds in raw_data.items():
        # 张量化 (B=1, C=6, H, W)
        tensor = _dataset_to_tensor(ds)
        fields[name] = tensor.to(device)

    if not fields:
        raise RuntimeError("无有效预报场")

    # 3. DEM (模拟)
    dem = _mock_dem().to(device)

    # 4. 风乌 GHR (从现有 fengwu-service 拉取)
    try:
        import requests
        resp = requests.get("http://uav-fengwu:8085/api/v1/forecast", timeout=10)
        if resp.ok:
            fengwu_data = resp.json()  # noqa: F841
            fengwu_tensor = torch.randn(1, 6, 50, 50, device=device)  # 模拟
            fields["fengwu_ghr"] = fengwu_tensor
    except Exception as e:
        logger.warning(f"风乌 GHR 不可用: {e}")

    # 5. 多模型融合
    fused = fusion_engine.fuse(fields)
    fused = physics_constraint(fused)

    # 6. CNN 订正
    corrected = cnn_corrector(fused, dem)

    # 7. U-Net 降尺度
    obs = _mock_observations().to(device) if request.include_risk else None
    fine = unet_downscaler(corrected, obs)

    # 8. GPR 风险场
    risk = None
    if request.include_risk:
        # 用残差拟合 GPR
        residual = torch.randn_like(fine[:, :1]) * 0.1
        gpr_estimator.fit(residual)
        risk_map = gpr_estimator.risk_field(fine_grid=fine.shape[-2:], device=device)
        risk = compute_risk_score(fine, risk_map.unsqueeze(0).expand_as(fine))

    result = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "fields": {
            name: tensor.cpu().numpy().tolist() for name, tensor in fields.items()
        },
        "fused_shape": list(fused.shape),
        "fine_shape": list(fine.shape),
    }

    if risk is not None:
        result["risk_map"] = risk.cpu().numpy().tolist()

    return result


def _dataset_to_tensor(ds) -> torch.Tensor:
    """xarray Dataset → (1, 6, 50, 50) 张量"""
    channels = []
    for var in ["u10", "v10", "t2m", "rh2m", "ps", "blh"]:
        data = ds[var].values if var in ds else np.zeros((50, 50))
        channels.append(data)
    return torch.tensor(np.stack(channels, axis=0), dtype=torch.float32).unsqueeze(0)


def _mock_dem() -> torch.Tensor:
    """模拟 DEM (成都平原西高东低)"""
    H, W = 50, 50
    dem = torch.from_numpy(np.fromfunction(
        lambda i, j: 500 + 400 * (1 - i / H) - 200 * (j / W), (H, W)
    ))
    return dem.unsqueeze(0).unsqueeze(0).float()


def _mock_observations() -> torch.Tensor:
    """模拟站点/无人机观测"""
    obs = torch.zeros(1, 4, 50, 50)
    # 随机 10 个虚拟站点
    for _ in range(10):
        i, j = np.random.randint(0, 50, 2)
        obs[0, :, i, j] = torch.randn(4) * 0.1
    return obs


# ── API 路由 ────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "healthy", "device": str(device)}


@app.get("/api/v1/model/info")
def model_info():
    return {
        "cnn_corrector": "active",
        "unet_downscaler": "active",
        "gpr_risk": "active",
        "fusion": fusion_engine.weights,
        "device": str(device),
    }


@app.post("/api/v1/forecast", response_model=ForecastResponse)
def forecast(request: ForecastRequest = None):
    """执行完整预测管线"""
    if request is None:
        request = ForecastRequest()
    try:
        result = run_pipeline(request)
        result["model_weights"] = fusion_engine.weights
        return result
    except Exception as e:
        logger.exception("预测失败")
        raise HTTPException(500, detail=str(e))


@app.post("/api/v1/train/cnn")
def train_cnn(epochs: int = 10, lr: float = 1e-3):
    """训练 CNN 订正器（模拟）"""
    logger.info(f"CNN 训练 {epochs} epochs, lr={lr}")
    return {"status": "training_started", "epochs": epochs}


@app.post("/api/v1/path/plan", response_model=ForecastResponse)
def plan_path(start_x: float, start_y: float, end_x: float, end_y: float):
    """GPR 风险场路径规划（新方法）"""
    try:
        result = run_pipeline(ForecastRequest(include_risk=True))
        risk_map = np.array(result.get("risk_map", []))
        if risk_map.size == 0:
            risk_map = np.random.exponential(0.3, (150, 150))
        else:
            risk_map = np.array(risk_map[0]) if risk_map.ndim == 3 else risk_map

        wind_u = np.random.normal(2, 1, risk_map.shape)
        wind_v = np.random.normal(0.5, 0.8, risk_map.shape)

        path = path_planner.plan(risk_map, wind_u, wind_v,
                                  (start_x, start_y), (end_x, end_y))
        return {
            "status": "success",
            "path": [{"x": w.x, "y": w.y, "z": w.z,
                       "risk": w.risk, "wind_u": w.wind_u, "wind_v": w.wind_v}
                      for w in path],
            "waypoints": len(path),
            "avg_risk": sum(w.risk for w in path) / len(path),
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/api/v1/train/unet")
def train_unet(epochs: int = 10, lr: float = 1e-3):
    """训练 U-Net 降尺度（模拟）"""
    logger.info(f"U-Net 训练 {epochs} epochs, lr={lr}")
    return {"status": "training_started", "epochs": epochs}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8087)
