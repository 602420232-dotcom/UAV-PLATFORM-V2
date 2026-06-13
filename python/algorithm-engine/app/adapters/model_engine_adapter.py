"""模型引擎算法适配器。

将 model_engine 目录下的算法注册到引擎中，包括：
- GPR 不确定性量化
- 贝叶斯神经网络
- LSTM 时间序列预测
- U-Net 天气预测
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.adapter import AlgorithmAdapter
from app.core.models import AlgorithmMetadata

logger = logging.getLogger(__name__)


class GPRUncertaintyAdapter(AlgorithmAdapter):
    """GPR 不确定性量化适配器。

    基于高斯过程回归对预测结果进行不确定性量化，
    输出均值、方差及置信区间。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="gpr_uncertainty",
                name="GPRUncertaintyQuantifier",
                category="model_engine",
                version="1.0.0",
                description="基于高斯过程回归的不确定性量化，输出均值、方差及置信区间",
                input_schema={
                    "type": "object",
                    "required": ["train_x", "train_y", "test_x"],
                    "properties": {
                        "train_x": {"type": "array"},
                        "train_y": {"type": "array"},
                        "test_x": {"type": "array"},
                        "length_scale": {"type": "number"},
                        "signal_variance": {"type": "number"},
                        "noise_variance": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "mean": {"type": "array"},
                        "variance": {"type": "array"},
                        "std": {"type": "array"},
                        "confidence_95_lower": {"type": "array"},
                        "confidence_95_upper": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.model_engine.gpr_uncertainty import (
            GPRUncertaintyQuantifier,
        )

        algo = GPRUncertaintyQuantifier(params.get("config"))
        return algo.quantify(params)  # type: ignore[attr-defined]


class BayesianNNAdapter(AlgorithmAdapter):
    """贝叶斯神经网络适配器。

    使用蒙特卡洛 Dropout 进行近似贝叶斯推断，
    输出预测均值与不确定性。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="bayesian_nn",
                name="BayesianNN",
                category="model_engine",
                version="1.0.0",
                description="贝叶斯神经网络，通过蒙特卡洛 Dropout 进行不确定性感知预测",
                input_schema={
                    "type": "object",
                    "required": ["input_data"],
                    "properties": {
                        "input_data": {"type": "array"},
                        "n_samples": {"type": "integer"},
                        "input_dim": {"type": "integer"},
                        "hidden_dim": {"type": "integer"},
                        "output_dim": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "mean": {"type": "array"},
                        "std": {"type": "array"},
                        "n_samples": {"type": "integer"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.model_engine.bayesian_nn import BayesianNN

        algo = BayesianNN(params.get("config"))
        return algo.predict(params)


class LSTMPredictorAdapter(AlgorithmAdapter):
    """LSTM 时间序列预测适配器。

    基于 LSTM 网络进行气象时间序列预测，
    支持多变量输入与多步输出。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="lstm_prediction",
                name="LSTMPredictor",
                category="model_engine",
                version="1.0.0",
                description="基于 LSTM 的气象时间序列预测，支持多变量输入与多步输出",
                input_schema={
                    "type": "object",
                    "required": ["input_sequence"],
                    "properties": {
                        "input_sequence": {"type": "array"},
                        "pred_length": {"type": "integer"},
                        "hidden_size": {"type": "integer"},
                        "num_layers": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "prediction": {"type": "array"},
                        "input_shape": {"type": "array"},
                        "output_shape": {"type": "array"},
                        "pred_length": {"type": "integer"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.model_engine.lstm_prediction import LSTMPredictor

        algo = LSTMPredictor(params.get("config"))
        return algo.forecast(params)  # type: ignore[attr-defined]


class UNetWeatherPredictorAdapter(AlgorithmAdapter):
    """U-Net 天气预测适配器。

    基于 U-Net 网络进行气象场降尺度/超分辨率预测，
    将粗网格（3km）映射到细网格（1km）。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="unet_weather",
                name="UNetWeatherPredictor",
                category="model_engine",
                version="1.0.0",
                description="基于 U-Net 的气象场降尺度预测，将粗网格映射到细网格",
                input_schema={
                    "type": "object",
                    "required": ["input_field"],
                    "properties": {
                        "input_field": {"type": "array"},
                        "scale_factor": {"type": "integer"},
                        "in_channels": {"type": "integer"},
                        "out_channels": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "output_field": {"type": "array"},
                        "input_shape": {"type": "array"},
                        "output_shape": {"type": "array"},
                        "scale_factor": {"type": "integer"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.model_engine.unet_weather import (
            UNetWeatherPredictor,
        )

        algo = UNetWeatherPredictor(params.get("config"))
        return algo.predict(params)
