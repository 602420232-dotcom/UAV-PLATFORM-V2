"""边缘计算算法适配器。

将 edge 目录下的算法注册到引擎中，包括：
- 联邦学习
- 模型量化
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.adapter import AlgorithmAdapter
from app.core.models import AlgorithmMetadata

logger = logging.getLogger(__name__)


class FederatedLearningAdapter(AlgorithmAdapter):
    """联邦学习适配器。

    在边缘设备间进行分布式模型训练，
    支持 FedAvg 和 FedProx 聚合策略。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="federated_learning",
                name="FederatedLearning",
                category="edge",
                version="1.0.0",
                description="边缘设备联邦学习，支持 FedAvg 和 FedProx 聚合策略",
                input_schema={
                    "type": "object",
                    "required": ["client_updates"],
                    "properties": {
                        "client_updates": {"type": "array"},
                        "strategy": {"type": "string"},
                        "n_rounds": {"type": "integer"},
                        "n_clients": {"type": "integer"},
                        "learning_rate": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "global_model": {"type": "array"},
                        "strategy": {"type": "string"},
                        "n_rounds": {"type": "integer"},
                        "history": {"type": "array"},
                        "final_loss": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.federated_learning import FederatedLearner

        algo = FederatedLearner(params.get("config"))
        return algo.train(params)


class ModelQuantizationAdapter(AlgorithmAdapter):
    """模型量化适配器。

    将模型权重从高精度转换为低精度（INT8/FP16），
    以减少模型体积并加速边缘端推理。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="model_quantization",
                name="ModelQuantization",
                category="edge",
                version="1.0.0",
                description="模型量化，支持 INT8 和 FP16 精度压缩以适配边缘部署",
                input_schema={
                    "type": "object",
                    "required": ["weights"],
                    "properties": {
                        "weights": {"type": "array"},
                        "quantization_type": {"type": "string"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "quantized": {"type": "boolean"},
                        "quantization_type": {"type": "string"},
                        "original_size": {"type": "integer"},
                        "quantized_size": {"type": "integer"},
                        "compression_ratio": {"type": "number"},
                        "shape": {"type": "array"},
                        "dtype": {"type": "string"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.model_quantization import ModelQuantizer

        algo = ModelQuantizer(params.get("config"))
        return algo.quantize(params)


class V2XCommunicationAdapter(AlgorithmAdapter):
    """V2X 通信模拟适配器。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="v2x_communication",
                name="V2XCommunication",
                category="edge",
                version="1.0.0",
                description="V2X 车联网通信模拟（DSRC/C-V2X），支持广播/单播/信道质量评估",
                input_schema={
                    "type": "object",
                    "required": ["sender_position"],
                    "properties": {
                        "sender_position": {"type": "array"},
                        "receiver_positions": {"type": "array"},
                        "message_size_bytes": {"type": "integer"},
                        "mode": {"type": "string", "enum": ["broadcast", "unicast", "channel_quality", "network_topology"]},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "receivers": {"type": "array"},
                        "snr": {"type": "number"},
                        "packet_loss": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.v2x_communication import V2XCommunication
        algo = V2XCommunication(params.get("config"))
        mode = params.get("mode", "broadcast")
        if mode == "unicast":
            return algo.unicast(params)
        elif mode == "channel_quality":
            return algo.channel_quality(params)
        elif mode == "network_topology":
            return algo.network_topology(params)
        else:
            return algo.broadcast(params)
