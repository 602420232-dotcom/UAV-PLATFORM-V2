#!/usr/bin/env python3
"""
GPR 风险场 API 路由
"""
import torch
import numpy as np
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


class RiskFieldRequest(BaseModel):
    """风险场计算请求"""
    latitude: float = Field(30.5, description="中心纬度")
    longitude: float = Field(103.5, description="中心经度")
    grid_size_km: float = Field(150.0, description="计算域大小 (km)")
    resolution_km: float = Field(1.0, description="网格分辨率 (km)")
    wind_threshold: float = Field(10.0, description="风速预警阈值 (m/s)")


class RiskFieldResponse(BaseModel):
    """风险场响应"""
    success: bool
    shape: List[int]
    risk_field: List[List[float]]
    variance_field: Optional[List[List[float]]] = None
    mean_field: Optional[List[List[float]]] = None
    data_source: str = "simulated"
    warning: Optional[str] = None


@router.post("/compute", response_model=RiskFieldResponse)
async def compute_risk_field(request: RiskFieldRequest):
    """
    计算气象风险场
    
    使用高斯过程回归生成不确定性方差场和综合风险评分。
    """
    try:
        from model_engine.gpr_risk.model import GPRiskEstimator
        
        # 计算网格
        n = int(request.grid_size_km / request.resolution_km)
        x = torch.linspace(-request.grid_size_km/2, request.grid_size_km/2, n)
        y = torch.linspace(-request.grid_size_km/2, request.grid_size_km/2, n)
        grid_x, grid_y = torch.meshgrid(x, y, indexing='ij')
        coords = torch.stack([grid_x.reshape(-1), grid_y.reshape(-1)], dim=1)
        
        # 初始化 GPR 估计器
        gpr = GPRiskEstimator()
        
        # 使用模拟残差（TODO: 接入真实 U-Net 输出）
        simulated_residual = torch.randn(1, 1, n, n) * 0.1
        fine_grid = torch.randn(1, 1, n, n)
        
        # 拟合 GPR
        gpr.fit(simulated_residual, coords)
        
        # 预测风险场
        risk = gpr.risk_field(fine_grid, wind_threshold=request.wind_threshold)
        
        # 预测均值和方差
        mean, variance = gpr.predict(coords)
        
        response = RiskFieldResponse(
            success=True,
            shape=[n, n],
            risk_field=risk.squeeze().tolist(),
            variance_field=variance.reshape(n, n).tolist(),
            mean_field=mean.reshape(n, n).tolist(),
            data_source="simulated",
            warning=(
                "⚠️ 当前 GPR 风险场使用模拟残差数据，仅供架构验证。"
                "需接入真实 U-Net 输出残差以获取有效风险场。"
            )
        )
        return response
        
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"GPR 依赖未安装: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"风险场计算失败: {str(e)}"
        )


@router.get("/status")
async def risk_service_status():
    """检查 GPR 风险场服务状态"""
    try:
        import torch
        import gpytorch
        return {
            "service": "GPR Risk Field",
            "torch_version": torch.__version__,
            "gpytorch_available": True,
            "data_source": "simulated",
            "warning": "使用模拟数据，需接入真实模型输出"
        }
    except ImportError as e:
        return {
            "service": "GPR Risk Field",
            "status": "unavailable",
            "error": str(e)
        }
