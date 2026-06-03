"""
原项目模型适配器
将 meteor-forecast-service 的 LSTM/XGBoost/ConvLSTM/GPR 适配到 model-engine 管线

集成方式: 桥接引用（不移动原文件）
影响: 零。原项目 README/引用/构建 完全不受影响
"""
import logging
from typing import Optional, Dict, Any
import numpy as np

from .bridge import (
    LEGACY_AVAILABLE,
    MeteorForecast, MeteorForecastEnhanced,
    ModelConfig, MLOpsPipeline, ModelServingAPI, ModelStatus,
)

logger = logging.getLogger(__name__)


class LegacyModelAdapter:
    """
    原模型适配器

    将 meteor-forecast 模型自适应接入 model-engine:
    - LSTM → 时序特征提取
    - XGBoost → 风场订正 baseline
    - ConvLSTM → 时空预测
    - GPR (sklearn) → 风险场备选
    - fusion_forecast() → 融合结果
    """

    def __init__(self):
        self.available = LEGACY_AVAILABLE
        if not self.available:
            logger.warning("原模型不可用（缺依赖），适配器降级为 pass-through")
            return

        # 初始化原模型
        self.model = MeteorForecast() if not self._has_enhanced() else None
        self.model_enhanced = MeteorForecastEnhanced() if self._has_enhanced() else None
        self.mlops = MLOpsPipeline() if LEGACY_AVAILABLE else None
        self.model_serving = ModelServingAPI() if LEGACY_AVAILABLE else None

        logger.info(f"原模型适配器就绪 (enhanced={self.model_enhanced is not None})")

    def _has_enhanced(self) -> bool:
        try:
            from meteor_forecast_enhanced import MeteorForecast
            return True
        except ImportError:
            return False

    # ── LSTM 时序预测 ──

    def lstm_predict(self, sequence: np.ndarray) -> np.ndarray:
        """原 LSTM 时序预测 → 供 CNN 订正器的时序模块使用"""
        if not self.available:
            return self._passthrough(sequence)
        return np.array(self.model.predict(sequence))

    # ── XGBoost 订正 ──

    def xgb_correct(self, coarse_field: np.ndarray) -> np.ndarray:
        """XGBoost 风场订正 → 作为 CNN 订正器的轻量 baseline"""
        if not self.available:
            return self._passthrough(coarse_field)
        if self.model_enhanced:
            return np.array(self.model_enhanced.predict(coarse_field))
        return np.array(self.model.predict(coarse_field))

    # ── GPR 风险场 ──

    def gpr_risk(self, residuals: np.ndarray,
                 positions: Optional[np.ndarray] = None) -> np.ndarray:
        """原 sklearn GPR 风险估计 → GPR 风险场的备选"""
        if not self.available:
            return np.zeros_like(residuals)
        # 原模型的 GPR 是 sklearn 实现，不适应批量 GPU 数据
        # 建议在数据量小 (<10k) 时使用，大批量用 GPyTorch
        return np.zeros_like(residuals)  # 暂存

    # ── 融合预测 ──

    def fusion_forecast(self, lstm_out: np.ndarray, xgb_out: np.ndarray,
                        convlstm_out: np.ndarray) -> np.ndarray:
        """原融合预测 → 接入 fusion/ensemble.py"""
        if not self.available or not self.model_enhanced:
            return self._ensemble_fallback(lstm_out, xgb_out, convlstm_out)
        return np.array(self.model_enhanced.fusion_forecast(lstm_out))

    # ── MLOps 集成 ──

    def register_checkpoint(self, model_name: str, metrics: Dict,
                            version: Optional[str] = None) -> Optional[str]:
        """将新模型 checkpoint 注册到原 MLOps 流水线"""
        if not self.mlops:
            return None
        self.mlops.register_model(
            model=self,
            name=model_name,
            version=version or "1.0.0",
            metrics=metrics,
            dataset_size=metrics.get("n_samples", 0),
        )
        return version

    def ab_test(self, model_name: str, model_a: Any, model_b: Any,
                test_data) -> Dict:
        """A/B 测试新模型 vs 原模型"""
        if not self.mlops:
            return {"error": "MLOps not available"}
        return self.mlops.ab_test(model_name, model_a, model_b, test_data)

    # ── 降级处理 ──

    def _passthrough(self, data: np.ndarray) -> np.ndarray:
        return data

    @staticmethod
    def _ensemble_fallback(*arrays: np.ndarray) -> np.ndarray:
        return np.mean(arrays, axis=0)
