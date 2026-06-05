#!/usr/bin/env python3
"""
XGBoost 气象要素订正模型

对 CNN/ConvLSTM 输出进行残差订正，使用 XGBoost 学习系统性偏差。
"""
import numpy as np
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


try:
    import xgboost as xgb
    XGB_AVAILABLE = True


except ImportError:
    XGB_AVAILABLE = False
    logger.warning("XGBoost not installed. Install with: pip install xgboost")


class XGBoostCorrector:
    """
    XGBoost 气象要素订正器

    对 CNN 订正后的预报场进行二次残差订正，学习空间位置、
    地形、季节等特征与预报误差之间的非线性关系。
    """

    def __init__(self, model_path: Optional[str] = None):
        self.models: Dict[str, Optional[xgb.Booster]] = {}
        self.model_path = model_path
        self.feature_names = [
            'latitude', 'longitude', 'elevation', 'month', 'hour',
            'wind_speed', 'temperature', 'humidity', 'pressure'
        ]

        if model_path and XGB_AVAILABLE:
            self._load_models()

    def _load_models(self):
        """加载预训练 XGBoost 模型（每个要素一个模型）"""
        import os
        variables = ['u10', 'v10', 't2m', 'rh2m', 'ps', 'blh']
        for var in variables:
            path = f"{self.model_path}/xgboost_{var}.json"
            if os.path.exists(path):
                self.models[var] = xgb.Booster()
                self.models[var].load_model(path)
                logger.info(f"Loaded XGBoost model for {var}")
            else:
                logger.warning(f"No XGBoost model found for {var} at {path}")

    def correct(self, predictions: np.ndarray, features: Dict[str, np.ndarray]) -> np.ndarray:
        """
        使用 XGBoost 对预测结果进行残差订正

        Args:
            predictions: CNN 输出 (B, 6, H, W) — [u10, v10, t2m, rh2m, ps, blh]
            features: 特征字典，包含 latitude, longitude, elevation 等

        Returns:
            订正后预测 (B, 6, H, W)
        """
        if not XGB_AVAILABLE or not self.models:
            logger.warning("XGBoost not available, returning uncorrected predictions")
            return predictions

        corrected = predictions.copy()
        B, C, H, W = predictions.shape

        for c, var in enumerate(['u10', 'v10', 't2m', 'rh2m', 'ps', 'blh']):
            if var not in self.models:
                continue

            # 构建特征矩阵
            n_samples = B * H * W
            X = np.zeros((n_samples, len(self.feature_names)))
            for i, name in enumerate(self.feature_names):
                if name in features:
                    feat = features[name]
                    X[:, i] = feat.reshape(-1)[:n_samples]

            # 预测残差
            dmatrix = xgb.DMatrix(X, feature_names=self.feature_names)
            residuals = self.models[var].predict(dmatrix)
            corrected[:, c] += residuals.reshape(B, H, W)

        logger.info(f"XGBoost correction applied: {list(self.models.keys())}")
        return corrected

    def is_available(self) -> bool:
        """检查是否有可用的 XGBoost 模型"""
        return XGB_AVAILABLE and len(self.models) > 0


class WeightValidator:
    """模型权重加载验证器"""

    @staticmethod
    def check_model_weights(model, model_name: str) -> bool:
        """
        检查 PyTorch 模型是否已加载预训练权重

        Returns:
            True 如果权重已加载（非随机初始化），False 如果为随机初始化
        """

        # 检查第一层卷积的权重是否接近默认初始化
        has_weights = False
        for name, param in model.named_parameters():
            if 'weight' in name and param.numel() > 0:
                # 检查权重是否与随机初始化有显著差异
                if param.abs().mean().item() > 0.01:
                    has_weights = True
                    break

        if not has_weights:
            logger.warning(
                f"⚠️ {model_name} 未加载预训练权重！"
                "当前输出为随机初始化结果，无实际预报价值。"
                "请加载预训练权重后再使用。"
            )
            return False

        logger.info(f"✅ {model_name} 权重已加载")
        return True

    @staticmethod
    def log_model_status(models: dict):
        """批量检查并记录模型状态"""
        all_loaded = True
        for name, model in models.items():
            if model is None:
                logger.error(f"❌ {name}: 模型为 None")
                all_loaded = False
            else:
                loaded = WeightValidator.check_model_weights(model, name)
                if not loaded:
                    all_loaded = False

        if not all_loaded:
            logger.warning(
                "部分模型未加载有效权重。系统将运行但输出的预报结果"
                "无实际参考价值。请确保模型权重文件可访问。"
            )
        return all_loaded
