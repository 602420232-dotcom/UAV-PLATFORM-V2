"""边缘计算算法适配器。

将 edge 目录下的算法注册到引擎中，包括：
- 联邦学习
- 模型量化
- V2X通信
- 边缘AI推理
- LLM辅助决策
- 自组织网络
- 边缘聚合器
- 模型压缩器
- 拆分学习
- 知识蒸馏
- 边缘调度器
- 边缘缓存管理器
- 边云数据同步
- 边缘模型更新
- 边缘资源监控
- 边缘任务卸载
- 边缘安全
- 边缘容错
- 边缘带宽优化器
- 边缘异常检测器
- ONNX Runtime 推理
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
    支持断点续训、通信压缩、学习率调度和早停。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="federated_learning",
                name="FederatedLearning",
                category="edge",
                version="2.0.0",
                description="边缘设备联邦学习，支持 FedAvg/FedProx 聚合、断点续训、通信压缩",
                input_schema={
                    "type": "object",
                    "required": ["client_updates"],
                    "properties": {
                        "client_updates": {"type": "array"},
                        "strategy": {"type": "string", "enum": ["fedavg", "fedprox"]},
                        "n_rounds": {"type": "integer"},
                        "n_clients": {"type": "integer"},
                        "learning_rate": {"type": "number"},
                        "mu": {
                            "type": "number",
                            "description": "FedProx proximal term coefficient",
                        },
                        "lr_schedule": {
                            "type": "string",
                            "enum": ["constant", "step", "exponential"],
                        },
                        "lr_decay": {"type": "number"},
                        "early_stop_patience": {"type": "integer"},
                        "checkpoint_dir": {"type": "string"},
                        "compression_method": {"type": "string", "enum": ["top_k", "fp16"]},
                        "compression_k_ratio": {"type": "number"},
                        "resume": {"type": "boolean"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "global_model": {"type": "array"},
                        "strategy": {"type": "string"},
                        "n_rounds_completed": {"type": "integer"},
                        "n_rounds_target": {"type": "integer"},
                        "early_stopped": {"type": "boolean"},
                        "best_metric": {"type": "number"},
                        "history": {"type": "array"},
                        "final_loss": {"type": "number"},
                        "compression_stats": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute federated learning.

        Supports two modes:
        1. Legacy mode: when 'client_updates' contains raw weight arrays,
           uses the legacy FederatedLearner interface.
        2. New mode: when 'client_updates' contains dicts with 'model_update'
           keys, uses FedAvgServer/FedProxServer.
        """
        strategy = params.get("strategy", "fedavg")
        client_updates = params.get("client_updates", [])

        # Detect mode: if client_updates are plain lists (legacy), use FederatedLearner
        if client_updates and isinstance(client_updates[0], list):
            from app.algorithms.edge.federated_learning import FederatedLearner

            algo = FederatedLearner(params.get("config"))
            return algo.train(params)

        # New mode: use FedAvgServer or FedProxServer
        if strategy == "fedprox":
            from app.algorithms.edge.federated_learning import FedProxServer

            server = FedProxServer(
                model_shape=params.get("model_shape", (10,)),
                n_rounds=params.get("n_rounds", 10),
                learning_rate=params.get("learning_rate", 0.01),
                mu=params.get("mu", 0.01),
                lr_schedule=params.get("lr_schedule", "constant"),
                lr_decay=params.get("lr_decay", 0.9),
                early_stop_patience=params.get("early_stop_patience", 5),
                checkpoint_dir=params.get("checkpoint_dir"),
                compression_method=params.get("compression_method"),
                compression_k_ratio=params.get("compression_k_ratio", 0.1),
            )
        else:
            from app.algorithms.edge.federated_learning import FedAvgServer

            server = FedAvgServer(
                model_shape=params.get("model_shape", (10,)),
                n_rounds=params.get("n_rounds", 10),
                learning_rate=params.get("learning_rate", 0.01),
                lr_schedule=params.get("lr_schedule", "constant"),
                lr_decay=params.get("lr_decay", 0.9),
                early_stop_patience=params.get("early_stop_patience", 5),
                checkpoint_dir=params.get("checkpoint_dir"),
                compression_method=params.get("compression_method"),
                compression_k_ratio=params.get("compression_k_ratio", 0.1),
            )

        # Build client data list from params
        client_data_list = []
        for i, cu in enumerate(client_updates):
            if isinstance(cu, dict):
                client_data_list.append(cu)
            else:
                client_data_list.append({"client_id": f"client_{i}"})

        return server.train(
            client_data_list=client_data_list,
            resume=params.get("resume", False),
        )


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
                        "mode": {
                            "type": "string",
                            "enum": ["broadcast", "unicast", "channel_quality", "network_topology"],
                        },
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


class EdgeAIInferenceAdapter(AlgorithmAdapter):
    """边缘AI推理适配器。

    在边缘设备上执行轻量级AI模型推理，
    支持 INT8/FP16 量化推理。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_ai_inference",
                name="EdgeAIInference",
                category="edge",
                version="1.0.0",
                description="边缘设备轻量级AI模型推理，支持INT8/FP16量化推理",
                input_schema={
                    "type": "object",
                    "required": ["input_data"],
                    "properties": {
                        "input_data": {"type": "array"},
                        "precision": {"type": "string", "enum": ["int8", "fp16", "fp32"]},
                        "batch_size": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "predictions": {"type": "array"},
                        "inference_time": {"type": "number"},
                        "memory_usage": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_ai_inference import EdgeAIInference

        algo = EdgeAIInference(params.get("config"))
        return algo.infer(params)


class LLMAssistedDecisionAdapter(AlgorithmAdapter):
    """LLM辅助决策适配器。

    大语言模型辅助飞行决策，
    自然语言任务描述转规划约束。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="llm_assisted_decision",
                name="LLMAssistedDecision",
                category="edge",
                version="1.0.0",
                description="大语言模型辅助飞行决策，自然语言任务描述转规划约束",
                input_schema={
                    "type": "object",
                    "required": ["task_description"],
                    "properties": {
                        "task_description": {"type": "string"},
                        "context": {"type": "object"},
                        "constraints": {"type": "array"},
                        "alternatives_count": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "decision": {"type": "object"},
                        "reasoning": {"type": "string"},
                        "confidence": {"type": "number"},
                        "alternatives": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.llm_assisted_decision import LLMAssistedDecision

        algo = LLMAssistedDecision(params.get("config"))
        return algo.decide(params)


class SelfOrganizingNetworkAdapter(AlgorithmAdapter):
    """自组织网络适配器。

    边缘设备自组织网络拓扑，
    动态调整通信链路。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="self_organizing_network",
                name="SelfOrganizingNetwork",
                category="edge",
                version="1.0.0",
                description="边缘设备自组织网络拓扑，动态调整通信链路",
                input_schema={
                    "type": "object",
                    "required": ["nodes"],
                    "properties": {
                        "nodes": {"type": "array"},
                        "signal_range": {"type": "number"},
                        "interference": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "topology": {"type": "object"},
                        "network_metrics": {"type": "object"},
                        "connectivity": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.self_organizing_network import SelfOrganizingNetwork

        algo = SelfOrganizingNetwork(params.get("config"))
        return algo.organize(params)


class EdgeAggregatorAdapter(AlgorithmAdapter):
    """边缘聚合器适配器。

    边缘数据聚合，多节点数据汇总与压缩。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_aggregator",
                name="EdgeAggregator",
                category="edge",
                version="1.0.0",
                description="边缘数据聚合，多节点数据汇总与压缩",
                input_schema={
                    "type": "object",
                    "required": ["node_data"],
                    "properties": {
                        "node_data": {"type": "array"},
                        "aggregation_method": {"type": "string"},
                        "compression_enabled": {"type": "boolean"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "aggregated_data": {"type": "array"},
                        "compression_ratio": {"type": "number"},
                        "node_contributions": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_aggregator import EdgeAggregator

        algo = EdgeAggregator(params.get("config"))
        return algo.aggregate(params)


class ModelCompressorAdapter(AlgorithmAdapter):
    """模型压缩器适配器。

    AI模型压缩（剪枝/量化/蒸馏），适配边缘部署。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="model_compressor",
                name="ModelCompressor",
                category="edge",
                version="1.0.0",
                description="AI模型压缩（剪枝/量化/蒸馏），适配边缘部署",
                input_schema={
                    "type": "object",
                    "required": ["weights"],
                    "properties": {
                        "weights": {"type": "array"},
                        "compression_method": {"type": "string"},
                        "target_ratio": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "compressed_model": {"type": "array"},
                        "compression_ratio": {"type": "number"},
                        "accuracy_retention": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.model_compressor import ModelCompressor

        algo = ModelCompressor(params.get("config"))
        return algo.compress(params)


class SplitLearningAdapter(AlgorithmAdapter):
    """拆分学习适配器。

    模型拆分训练，前端在边缘后端在云端。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="split_learning",
                name="SplitLearning",
                category="edge",
                version="1.0.0",
                description="模型拆分训练，前端在边缘后端在云端",
                input_schema={
                    "type": "object",
                    "required": ["data", "labels"],
                    "properties": {
                        "data": {"type": "array"},
                        "labels": {"type": "array"},
                        "split_layer": {"type": "integer"},
                        "n_epochs": {"type": "integer"},
                        "learning_rate": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "model_updates": {"type": "object"},
                        "training_stats": {"type": "object"},
                        "communication_cost": {"type": "integer"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.split_learning import SplitLearning

        algo = SplitLearning(params.get("config"))
        return algo.train(params)


class KnowledgeDistillationAdapter(AlgorithmAdapter):
    """知识蒸馏适配器。

    教师模型到学生模型的知识蒸馏。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="knowledge_distillation",
                name="KnowledgeDistillation",
                category="edge",
                version="1.0.0",
                description="教师模型到学生模型的知识蒸馏",
                input_schema={
                    "type": "object",
                    "required": ["teacher_outputs", "data", "labels"],
                    "properties": {
                        "teacher_outputs": {"type": "array"},
                        "data": {"type": "array"},
                        "labels": {"type": "array"},
                        "temperature": {"type": "number"},
                        "alpha": {"type": "number"},
                        "n_epochs": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "student_model": {"type": "object"},
                        "distillation_loss": {"type": "number"},
                        "accuracy_transfer": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.knowledge_distillation import KnowledgeDistillation

        algo = KnowledgeDistillation(params.get("config"))
        return algo.distill(params)


class EdgeSchedulerAdapter(AlgorithmAdapter):
    """边缘调度器适配器。

    边缘计算任务调度，负载均衡与资源分配。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_scheduler",
                name="EdgeScheduler",
                category="edge",
                version="1.0.0",
                description="边缘计算任务调度，负载均衡与资源分配",
                input_schema={
                    "type": "object",
                    "required": ["tasks", "nodes"],
                    "properties": {
                        "tasks": {"type": "array"},
                        "nodes": {"type": "array"},
                        "scheduling_policy": {"type": "string"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "schedule": {"type": "object"},
                        "resource_allocation": {"type": "object"},
                        "utilization": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_scheduler import EdgeScheduler

        algo = EdgeScheduler(params.get("config"))
        return algo.schedule(params)


class EdgeCacheManagerAdapter(AlgorithmAdapter):
    """边缘缓存管理器适配器。

    边缘缓存策略管理，LRU/LFU/预测性缓存。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_cache_manager",
                name="EdgeCacheManager",
                category="edge",
                version="1.0.0",
                description="边缘缓存策略管理，LRU/LFU/预测性缓存",
                input_schema={
                    "type": "object",
                    "required": ["operation"],
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["get", "put", "evict", "stats", "predictive"],
                        },
                        "key": {"type": "string"},
                        "value": {},
                        "cache_policy": {"type": "string"},
                        "max_size": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "cache_status": {"type": "object"},
                        "hit_rate": {"type": "number"},
                        "evicted_items": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_cache_manager import EdgeCacheManager

        algo = EdgeCacheManager(params.get("config"))
        return algo.manage(params)


class EdgeDataSyncAdapter(AlgorithmAdapter):
    """边云数据同步适配器。

    边缘与云端数据同步，增量同步与冲突解决。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_data_sync",
                name="EdgeDataSync",
                category="edge",
                version="1.0.0",
                description="边缘与云端数据同步，增量同步与冲突解决",
                input_schema={
                    "type": "object",
                    "properties": {
                        "edge_data": {"type": "object"},
                        "cloud_data": {"type": "object"},
                        "sync_mode": {"type": "string"},
                        "conflict_resolution": {"type": "string"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "sync_result": {"type": "object"},
                        "data_volume": {"type": "integer"},
                        "latency": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_data_sync import EdgeDataSync

        algo = EdgeDataSync(params.get("config"))
        return algo.sync(params)


class EdgeModelUpdateAdapter(AlgorithmAdapter):
    """边缘模型更新适配器。

    边缘模型OTA更新，差量更新与回滚。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_model_update",
                name="EdgeModelUpdate",
                category="edge",
                version="1.0.0",
                description="边缘模型OTA更新，差量更新与回滚",
                input_schema={
                    "type": "object",
                    "required": ["new_weights"],
                    "properties": {
                        "new_weights": {"type": "array"},
                        "target_version": {"type": "string"},
                        "update_strategy": {"type": "string"},
                        "verify_checksum": {"type": "boolean"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "update_status": {"type": "string"},
                        "version_diff": {"type": "object"},
                        "rollback_info": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_model_update import EdgeModelUpdate

        algo = EdgeModelUpdate(params.get("config"))
        return algo.update(params)


class EdgeResourceMonitorAdapter(AlgorithmAdapter):
    """边缘资源监控适配器。

    边缘设备资源监控（CPU/GPU/内存/带宽）。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_resource_monitor",
                name="EdgeResourceMonitor",
                category="edge",
                version="1.0.0",
                description="边缘设备资源监控（CPU/GPU/内存/带宽）",
                input_schema={
                    "type": "object",
                    "properties": {
                        "resource_types": {"type": "array"},
                        "alert_thresholds": {"type": "object"},
                        "simulate": {"type": "boolean"},
                        "n_samples": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "resource_status": {"type": "object"},
                        "alerts": {"type": "array"},
                        "utilization_history": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_resource_monitor import EdgeResourceMonitor

        algo = EdgeResourceMonitor(params.get("config"))
        return algo.monitor(params)


class EdgeTaskOffloadAdapter(AlgorithmAdapter):
    """边缘任务卸载适配器。

    计算任务卸载决策，本地vs云端执行选择。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_task_offload",
                name="EdgeTaskOffload",
                category="edge",
                version="1.0.0",
                description="计算任务卸载决策，本地vs云端执行选择",
                input_schema={
                    "type": "object",
                    "required": ["tasks"],
                    "properties": {
                        "tasks": {"type": "array"},
                        "edge_resources": {"type": "object"},
                        "network_conditions": {"type": "object"},
                        "offload_policy": {"type": "string"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "offload_decision": {"type": "array"},
                        "latency_estimate": {"type": "object"},
                        "energy_cost": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_task_offload import EdgeTaskOffload

        algo = EdgeTaskOffload(params.get("config"))
        return algo.offload(params)


class EdgeSecurityAdapter(AlgorithmAdapter):
    """边缘安全模块适配器。

    边缘设备安全通信，数据加密与认证。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_security",
                name="EdgeSecurity",
                category="edge",
                version="1.0.0",
                description="边缘设备安全通信，数据加密与认证",
                input_schema={
                    "type": "object",
                    "required": ["operation"],
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["encrypt", "decrypt", "authenticate", "verify"],
                        },
                        "data": {},
                        "key": {"type": "string"},
                        "encryption_method": {"type": "string"},
                        "auth_method": {"type": "string"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "security_status": {"type": "object"},
                        "encryption_info": {"type": "object"},
                        "auth_result": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_security import EdgeSecurity

        algo = EdgeSecurity(params.get("config"))
        return algo.secure(params)


class EdgeFaultToleranceAdapter(AlgorithmAdapter):
    """边缘容错适配器。

    边缘设备故障检测与容错，任务迁移与恢复。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_fault_tolerance",
                name="EdgeFaultTolerance",
                category="edge",
                version="1.0.0",
                description="边缘设备故障检测与容错，任务迁移与恢复",
                input_schema={
                    "type": "object",
                    "required": ["operation"],
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["detect", "recover", "migrate", "status"],
                        },
                        "nodes": {"type": "array"},
                        "failed_node_id": {"type": "string"},
                        "target_node_id": {"type": "string"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "fault_report": {"type": "object"},
                        "recovery_actions": {"type": "array"},
                        "availability": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_fault_tolerance import EdgeFaultTolerance

        algo = EdgeFaultTolerance(params.get("config"))
        return algo.handle(params)


class EdgeBandwidthOptimizerAdapter(AlgorithmAdapter):
    """边缘带宽优化器适配器。

    边缘通信带宽优化，数据优先级调度与压缩。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_bandwidth_optimizer",
                name="EdgeBandwidthOptimizer",
                category="edge",
                version="1.0.0",
                description="边缘通信带宽优化，数据优先级调度与压缩",
                input_schema={
                    "type": "object",
                    "required": ["data_streams"],
                    "properties": {
                        "data_streams": {"type": "array"},
                        "total_bandwidth": {"type": "number"},
                        "compression_ratio": {"type": "number"},
                        "scheduling_algorithm": {"type": "string"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "bandwidth_allocation": {"type": "object"},
                        "throughput": {"type": "object"},
                        "priority_queue": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_bandwidth_optimizer import EdgeBandwidthOptimizer

        algo = EdgeBandwidthOptimizer(params.get("config"))
        return algo.optimize(params)


class EdgeAnomalyDetectorAdapter(AlgorithmAdapter):
    """边缘异常检测器适配器。

    边缘设备运行异常检测，基于统计方法。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="edge_anomaly_detector",
                name="EdgeAnomalyDetector",
                category="edge",
                version="1.0.0",
                description="边缘设备运行异常检测，基于统计方法",
                input_schema={
                    "type": "object",
                    "required": ["metrics"],
                    "properties": {
                        "metrics": {"type": "object"},
                        "detection_method": {"type": "string"},
                        "zscore_threshold": {"type": "number"},
                        "iqr_factor": {"type": "number"},
                        "window_size": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "anomalies": {"type": "array"},
                        "anomaly_scores": {"type": "object"},
                        "normal_range": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.edge_anomaly_detector import EdgeAnomalyDetector

        algo = EdgeAnomalyDetector(params.get("config"))
        return algo.detect(params)


class OnnxRuntimeInferenceAdapter(AlgorithmAdapter):
    """ONNX Runtime 推理后端适配器。

    模拟 ONNX Runtime 推理流程，支持批量推理、
    推理性能统计和内存占用估算。
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="onnx_runtime_inference",
                name="OnnxRuntimeInference",
                category="edge",
                version="1.0.0",
                description="ONNX Runtime 推理后端，支持批量推理、性能统计和内存估算",
                input_schema={
                    "type": "object",
                    "required": ["input_data"],
                    "properties": {
                        "input_data": {"type": "array"},
                        "precision": {
                            "type": "string",
                            "enum": ["fp32", "fp16", "int8"],
                        },
                        "batch_size": {"type": "integer"},
                        "model_name": {"type": "string"},
                        "mode": {
                            "type": "string",
                            "enum": ["infer", "batch", "benchmark", "memory"],
                        },
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "predictions": {"type": "array"},
                        "inference_time": {"type": "number"},
                        "memory_usage": {"type": "number"},
                        "stats": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.edge.onnx_runtime_inference import OnnxRuntimeInferencer

        config = params.get("config", {})
        algo = OnnxRuntimeInferencer(config)
        mode = params.get("mode", "infer")

        if mode == "benchmark":
            stats = algo.benchmark(
                input_shape=tuple(params.get("input_shape", [1, 64])),
                n_warmup=params.get("n_warmup", 10),
                n_runs=params.get("n_runs", 100),
                batch_size=params.get("batch_size", 1),
            )
            return {"stats": stats.to_dict()}
        elif mode == "memory":
            mem = algo.estimate_memory(
                input_shape=tuple(params.get("input_shape", [1, 64])),
                output_shape=tuple(params.get("output_shape", [1, 10])),
                batch_size=params.get("batch_size", 1),
                precision=params.get("precision", "fp32"),
                n_layers=params.get("n_layers", 4),
            )
            return {"memory": mem}
        elif mode == "batch":
            import numpy as np

            input_data = np.asarray(params.get("input_data", []), dtype=np.float32)
            batch_size = params.get("batch_size", 8)
            _, stats = algo.run_batch(input_data, batch_size=batch_size)
            return {"stats": stats.to_dict()}
        else:
            return algo.infer(params)
