"""
多模型动态融合
将 风乌GHR + 天资 + 风雷 按置信度动态加权融合
"""
import logging
import torch
import torch.nn as nn
from typing import Dict, Optional
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FusionConfig:
    """融合配置"""
    # 初始权重 (业务评估后更新)
    initial_weights: Dict[str, float] = field(default_factory=lambda: {
        "fengwu_ghr": 0.15,  # 风乌 GHR: 全局背景
        "tianzi": 0.25,  # 天资: 全球确定性
        "fenglei": 0.60,  # 风雷: 区域高分辨率 (核心)
    })
    # 自适应权重更新周期 (步数)
    adapt_interval: int = 10
    # 滑动窗口大小 (用于计算 RMSE)
    window_size: int = 24


class DynamicWeightFusion:
    """
    动态加权融合
    根据近期验证 RMSE 自适应调整各模型权重
    """

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
        self.weights = dict(self.config.initial_weights)
        self.history: Dict[str, list] = {k: [] for k in self.weights}
        self.step = 0

    def fuse(self, fields: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        融合多模型预报

        Args:
            fields: {"fengwu_ghr": (B, C, H, W), "tianzi": ..., "fenglei": ...}
        Returns:
            fused: (B, C, H, W)
        """
        result = None
        total_weight = 0.0

        for name, model_field in fields.items():
            w = self.weights.get(name, 0.0)
            if w > 0:
                if result is None:
                    result = w * model_field
                else:
                    # 统一分辨率 (双线性插值到风雷分辨率)
                    target_shape = result.shape[-2:]
                    if model_field.shape[-2:] != target_shape:
                        model_field = torch.nn.functional.interpolate(
                            model_field, size=target_shape,
                            mode="bilinear", align_corners=False)
                    result = result + w * model_field
                total_weight += w

        if total_weight > 0:
            assert result is not None
            return result / total_weight
        raise ValueError("No valid field with positive weight found for fusion")

    def update_weights(self, observations: Dict[str, torch.Tensor],
                       ground_truth: torch.Tensor):
        """
        基于验证 RMSE 自适应更新权重

        Args:
            observations: 各模型预测 {"name": (B, C, H, W)}
            ground_truth: 真值观测 (B, C, H, W)
        """
        self.step += 1
        if self.step % self.config.adapt_interval != 0:
            return

        rmse = {}
        for name, pred in observations.items():
            if pred.shape != ground_truth.shape:
                pred = nn.functional.interpolate(
                    pred, size=ground_truth.shape[-2:], mode="bilinear", align_corners=False)
            err = ((pred - ground_truth) ** 2).mean().item()
            rmse_val = np.sqrt(err)
            self.history[name].append(rmse_val)
            # 滑动窗口均值
            window = self.history[name][-self.config.window_size:]
            rmse[name] = np.mean(window)

        # 反比加权: w_i = (1/RMSE_i) / Σ(1/RMSE_j)
        inv_rmse = {k: 1.0 / max(v, 1e-8) for k, v in rmse.items()}
        total_inv = sum(inv_rmse.values())
        self.weights = {k: v / total_inv for k, v in inv_rmse.items()}

        logger.info(f"[Fusion] 权重更新: {self.weights}")


class PhysicsConstraint(nn.Module):
    """
    物理一致性约束
    确保融合场满足基本物理定律
    """

    def __init__(self):
        super().__init__()

    def forward(self, field: torch.Tensor) -> torch.Tensor:
        """
        约束:
        1. 风速 ≥ 0
        2. 温度 ≥ 180K (≈ -93°C, 大气最低温)
        3. 比湿 ≥ 0
        4. 气压 ≥ 500hPa (成都平原~950hPa)
        """
        # 各通道物理约束 (根据变量索引)
        # 假设通道顺序: u10, v10, t2m, rh2m, ps, blh
        field = field.clone()

        # t2m ≥ 180K
        field[:, 2] = torch.clamp(field[:, 2], min=180.0)
        # ps ≥ 50000 Pa
        field[:, 4] = torch.clamp(field[:, 4], min=50000.0)
        # rh2m 0-100%
        field[:, 3] = torch.clamp(field[:, 3], min=0.0, max=100.0)
        # blh ≥ 50m
        field[:, 5] = torch.clamp(field[:, 5], min=50.0)

        return field
