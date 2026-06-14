"""ONNX Runtime 推理后端模块。

模拟 ONNX Runtime 推理流程，支持批量推理、
推理性能统计（延迟、吞吐量）和内存占用估算。
使用模拟数据，不需要实际 ONNX 模型文件。
"""

from __future__ import annotations

import logging
import time as _time
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class InferenceSession:
    """模拟 ONNX Runtime 推理会话。

    Attributes:
        model_name: 模型名称。
        input_name: 输入节点名称。
        output_name: 输出节点名称。
        input_shape: 输入形状。
        output_shape: 输出形状。
        providers: 执行提供者列表。
        model_loaded: 模型是否已加载。
    """

    model_name: str = "simulated_model"
    input_name: str = "input"
    output_name: str = "output"
    input_shape: tuple[int, ...] = (1, 64)
    output_shape: tuple[int, ...] = (1, 10)
    providers: list[str] = field(default_factory=lambda: ["CPUExecutionProvider"])
    model_loaded: bool = True


@dataclass
class InferenceStats:
    """推理性能统计数据。

    Attributes:
        total_samples: 总推理样本数。
        batch_size: 批量大小。
        n_batches: 批次数。
        total_time_ms: 总耗时（毫秒）。
        mean_latency_ms: 平均延迟（毫秒）。
        std_latency_ms: 延迟标准差（毫秒）。
        min_latency_ms: 最小延迟（毫秒）。
        max_latency_ms: 最大延迟（毫秒）。
        p50_latency_ms: P50 延迟（毫秒）。
        p95_latency_ms: P95 延迟（毫秒）。
        p99_latency_ms: P99 延迟（毫秒）。
        throughput_fps: 吞吐量（样本/秒）。
        memory_peak_mb: 内存峰值占用（MB）。
        memory_avg_mb: 平均内存占用（MB）。
    """

    total_samples: int = 0
    batch_size: int = 1
    n_batches: int = 0
    total_time_ms: float = 0.0
    mean_latency_ms: float = 0.0
    std_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    throughput_fps: float = 0.0
    memory_peak_mb: float = 0.0
    memory_avg_mb: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式。"""
        return {
            "total_samples": self.total_samples,
            "batch_size": self.batch_size,
            "n_batches": self.n_batches,
            "total_time_ms": round(self.total_time_ms, 3),
            "mean_latency_ms": round(self.mean_latency_ms, 3),
            "std_latency_ms": round(self.std_latency_ms, 3),
            "min_latency_ms": round(self.min_latency_ms, 3),
            "max_latency_ms": round(self.max_latency_ms, 3),
            "p50_latency_ms": round(self.p50_latency_ms, 3),
            "p95_latency_ms": round(self.p95_latency_ms, 3),
            "p99_latency_ms": round(self.p99_latency_ms, 3),
            "throughput_fps": round(self.throughput_fps, 2),
            "memory_peak_mb": round(self.memory_peak_mb, 4),
            "memory_avg_mb": round(self.memory_avg_mb, 4),
        }


class OnnxRuntimeInferencer:
    """ONNX Runtime 推理后端。

    模拟 ONNX Runtime 的推理流程，提供：
    - 模型加载与会话管理
    - 批量推理
    - 推理性能统计（延迟、吞吐量）
    - 内存占用估算
    - 多精度推理支持（FP32/FP16/INT8）
    """

    # 各精度的每参数字节数
    PRECISION_BYTES = {
        "fp32": 4,
        "fp16": 2,
        "int8": 1,
    }

    # 各精度的计算延迟因子（相对于 FP32）
    PRECISION_LATENCY_FACTOR = {
        "fp32": 1.0,
        "fp16": 0.6,
        "int8": 0.4,
    }

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.precision = self.config.get("precision", "fp32")
        self.batch_size = self.config.get("batch_size", 1)
        self.model_name = self.config.get("model_name", "simulated_model")
        self.input_shape = self.config.get("input_shape", (1, 64))
        self.output_shape = self.config.get("output_shape", (1, 10))
        self.providers = self.config.get(
            "providers", ["CPUExecutionProvider"]
        )
        self._session: Optional[InferenceSession] = None

    # ------------------------------------------------------------------
    # 会话管理
    # ------------------------------------------------------------------

    def load_model(self, model_name: Optional[str] = None) -> InferenceSession:
        """加载模型（模拟）。

        Args:
            model_name: 模型名称。

        Returns:
            InferenceSession 实例。
        """
        if model_name:
            self.model_name = model_name

        self._session = InferenceSession(
            model_name=self.model_name,
            input_name="input",
            output_name="output",
            input_shape=self.input_shape,
            output_shape=self.output_shape,
            providers=self.providers,
            model_loaded=True,
        )

        logger.info(
            "模型加载完成: %s (providers=%s)",
            self.model_name,
            self.providers,
        )
        return self._session

    def get_session(self) -> InferenceSession:
        """获取当前推理会话。"""
        if self._session is None:
            return self.load_model()
        return self._session

    # ------------------------------------------------------------------
    # 推理
    # ------------------------------------------------------------------

    def run(
        self,
        input_data: np.ndarray,
        output_names: Optional[list[str]] = None,
    ) -> dict[str, np.ndarray]:
        """执行单次推理。

        Args:
            input_data: 输入数据数组。
            output_names: 输出节点名称列表。

        Returns:
            输出名称到输出数组的映射字典。
        """
        np.random.seed(42)
        session = self.get_session()

        # 模拟推理计算：矩阵乘法
        input_dim = input_data.shape[-1]
        output_dim = self.output_shape[-1]

        weights = np.random.randn(input_dim, output_dim).astype(np.float32)
        bias = np.random.randn(output_dim).astype(np.float32)

        # 根据精度调整计算
        if self.precision == "int8":
            scale = max(float(np.max(np.abs(weights))) / 127.0, 1e-10)
            q_weights = np.clip(
                np.round(weights / scale), -127, 127
            ).astype(np.int8)
            weights_fp32 = q_weights.astype(np.float32) * scale
            output = input_data.astype(np.float32) @ weights_fp32 + bias
        elif self.precision == "fp16":
            output = (
                input_data.astype(np.float16) @ weights.astype(np.float16) + bias.astype(np.float16)
            ).astype(np.float32)
        else:
            output = input_data @ weights + bias

        # 应用 Softmax
        if output.ndim == 1:
            exp_out = np.exp(output - np.max(output))
            output = exp_out / exp_out.sum()
        else:
            exp_out = np.exp(output - np.max(output, axis=-1, keepdims=True))
            output = exp_out / exp_out.sum(axis=-1, keepdims=True)

        out_name = (output_names or ["output"])[0]
        return {out_name: output}

    def infer(self, params: dict[str, Any]) -> dict[str, Any]:
        """兼容原有 Adapter 调用接口。

        Args:
            params: 推理参数字典，包含：
                - input_data: 输入数据。
                - precision: 推理精度。
                - batch_size: 批量大小。
                - run_batch: 是否执行批量推理。

        Returns:
            推理结果字典。
        """
        input_data = params.get("input_data", [])
        precision = params.get("precision", self.precision)
        batch_size = params.get("batch_size", self.batch_size)

        if not input_data:
            return {
                "predictions": [],
                "inference_time": 0.0,
                "memory_usage": 0.0,
                "precision": precision,
                "batch_size": batch_size,
            }

        self.precision = precision
        data = np.asarray(input_data, dtype=np.float32)

        t_start = _time.perf_counter()
        result = self.run(data)
        t_end = _time.perf_counter()

        inference_time = (t_end - t_start) * 1000

        # 内存估算
        memory_factor = self.PRECISION_LATENCY_FACTOR.get(precision, 1.0)
        input_bytes = data.nbytes * memory_factor
        model_bytes = data.shape[-1] * self.output_shape[-1] * 4 * memory_factor
        memory_usage = (input_bytes + model_bytes) / (1024 * 1024)

        return {
            "predictions": result.get("output", np.array([])).tolist(),
            "inference_time": round(inference_time, 3),
            "memory_usage": round(memory_usage, 4),
            "precision": precision,
            "batch_size": batch_size,
        }

    # ------------------------------------------------------------------
    # 批量推理
    # ------------------------------------------------------------------

    def run_batch(
        self,
        input_data: np.ndarray,
        batch_size: int = 8,
        output_names: Optional[list[str]] = None,
    ) -> tuple[list[dict[str, np.ndarray]], InferenceStats]:
        """执行批量推理。

        将输入数据分批处理，收集每批的延迟数据并生成性能统计。

        Args:
            input_data: 输入数据数组（第一维为样本维度）。
            batch_size: 每批样本数。
            output_names: 输出节点名称列表。

        Returns:
            (results, stats) 元组：
            - results: 每批推理结果列表。
            - stats: 推理性能统计。
        """
        n_samples = input_data.shape[0]
        n_batches = (n_samples + batch_size - 1) // batch_size

        results: list[dict[str, np.ndarray]] = []
        batch_latencies: list[float] = []
        memory_usages: list[float] = []

        for i in range(n_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, n_samples)
            batch_input = input_data[start_idx:end_idx]

            t_start = _time.perf_counter()
            batch_result = self.run(batch_input, output_names)
            t_end = _time.perf_counter()

            batch_latency = (t_end - t_start) * 1000
            batch_latencies.append(batch_latency)

            # 内存估算
            batch_bytes = batch_input.nbytes
            model_dim = self.output_shape[-1]
            model_bytes = batch_input.shape[-1] * model_dim * 4
            mem_mb = (batch_bytes + model_bytes) / (1024 * 1024)
            memory_usages.append(mem_mb)

            results.append(batch_result)

        # 汇总统计
        latencies = np.array(batch_latencies)
        total_time = float(np.sum(latencies))
        total_samples = n_samples

        stats = InferenceStats(
            total_samples=total_samples,
            batch_size=batch_size,
            n_batches=n_batches,
            total_time_ms=total_time,
            mean_latency_ms=float(np.mean(latencies)),
            std_latency_ms=float(np.std(latencies)),
            min_latency_ms=float(np.min(latencies)),
            max_latency_ms=float(np.max(latencies)),
            p50_latency_ms=float(np.percentile(latencies, 50)),
            p95_latency_ms=float(np.percentile(latencies, 95)),
            p99_latency_ms=float(np.percentile(latencies, 99)),
            throughput_fps=total_samples / max(total_time / 1000, 1e-10),
            memory_peak_mb=float(np.max(memory_usages)),
            memory_avg_mb=float(np.mean(memory_usages)),
        )

        logger.info(
            "批量推理完成: %d 样本, %d 批, 平均延迟=%.3fms, 吞吐=%.1f FPS",
            total_samples,
            n_batches,
            stats.mean_latency_ms,
            stats.throughput_fps,
        )

        return results, stats

    # ------------------------------------------------------------------
    # 性能统计
    # ------------------------------------------------------------------

    def benchmark(
        self,
        input_shape: tuple[int, ...] = (1, 64),
        n_warmup: int = 10,
        n_runs: int = 100,
        batch_size: int = 1,
    ) -> InferenceStats:
        """执行推理性能基准测试。

        Args:
            input_shape: 输入数据形状。
            n_warmup: 预热轮数。
            n_runs: 测试轮数。
            batch_size: 批量大小。

        Returns:
            InferenceStats 推理性能统计。
        """
        np.random.seed(42)

        # 生成模拟输入
        test_input = np.random.randn(batch_size, *input_shape[1:]).astype(np.float32)

        # 预热
        for _ in range(n_warmup):
            self.run(test_input)

        # 正式测试
        latencies = []
        memory_usages = []
        total_samples = n_runs * batch_size

        for _ in range(n_runs):
            t_start = _time.perf_counter()
            self.run(test_input)
            t_end = _time.perf_counter()

            latency = (t_end - t_start) * 1000
            latencies.append(latency)

            # 内存估算
            input_bytes = test_input.nbytes
            model_bytes = input_shape[-1] * self.output_shape[-1] * 4
            mem_mb = (input_bytes + model_bytes) / (1024 * 1024)
            memory_usages.append(mem_mb)

        latencies_arr = np.array(latencies)
        total_time = float(np.sum(latencies_arr))

        stats = InferenceStats(
            total_samples=total_samples,
            batch_size=batch_size,
            n_batches=n_runs,
            total_time_ms=total_time,
            mean_latency_ms=float(np.mean(latencies_arr)),
            std_latency_ms=float(np.std(latencies_arr)),
            min_latency_ms=float(np.min(latencies_arr)),
            max_latency_ms=float(np.max(latencies_arr)),
            p50_latency_ms=float(np.percentile(latencies_arr, 50)),
            p95_latency_ms=float(np.percentile(latencies_arr, 95)),
            p99_latency_ms=float(np.percentile(latencies_arr, 99)),
            throughput_fps=total_samples / max(total_time / 1000, 1e-10),
            memory_peak_mb=float(np.max(memory_usages)),
            memory_avg_mb=float(np.mean(memory_usages)),
        )

        logger.info(
            "基准测试完成: precision=%s, batch=%d, 平均延迟=%.3fms, P99=%.3fms, 吞吐=%.1f FPS",
            self.precision,
            batch_size,
            stats.mean_latency_ms,
            stats.p99_latency_ms,
            stats.throughput_fps,
        )

        return stats

    # ------------------------------------------------------------------
    # 内存占用估算
    # ------------------------------------------------------------------

    def estimate_memory(
        self,
        input_shape: tuple[int, ...] = (1, 64),
        output_shape: tuple[int, ...] = (1, 10),
        batch_size: int = 1,
        precision: str = "fp32",
        n_layers: int = 4,
    ) -> dict[str, Any]:
        """估算推理过程中的内存占用。

        Args:
            input_shape: 输入数据形状。
            output_shape: 输出数据形状。
            batch_size: 批量大小。
            precision: 推理精度。
            n_layers: 模拟层数。

        Returns:
            内存占用详细估算字典。
        """
        bytes_per_param = self.PRECISION_BYTES.get(precision, 4)

        # 输入数据内存
        input_elements = batch_size * int(np.prod(input_shape[1:]))
        input_memory = input_elements * bytes_per_param

        # 模型权重内存（模拟多层网络）
        # 假设每层有 input_dim -> hidden_dim -> output_dim 的权重
        input_dim = input_shape[-1]
        hidden_dim = input_dim * 2
        output_dim = output_shape[-1]

        weights_memory = 0
        layer_details = []
        for i in range(n_layers):
            if i == 0:
                w_elements = input_dim * hidden_dim + hidden_dim
                layer_name = f"layer_{i}_input->hidden"
            elif i == n_layers - 1:
                w_elements = hidden_dim * output_dim + output_dim
                layer_name = f"layer_{i}_hidden->output"
            else:
                w_elements = hidden_dim * hidden_dim + hidden_dim
                layer_name = f"layer_{i}_hidden->hidden"

            layer_mem = w_elements * bytes_per_param
            weights_memory += layer_mem
            layer_details.append({
                "name": layer_name,
                "n_params": w_elements,
                "memory_bytes": layer_mem,
                "memory_mb": round(layer_mem / (1024 * 1024), 4),
            })

        # 中间激活值内存
        activation_memory = batch_size * hidden_dim * bytes_per_param * n_layers

        # 输出内存
        output_elements = batch_size * int(np.prod(output_shape[1:]))
        output_memory = output_elements * bytes_per_param

        # 总内存
        total_memory = input_memory + weights_memory + activation_memory + output_memory

        # ONNX Runtime 框架开销
        framework_overhead = 50 * 1024 * 1024  # 约 50MB

        return {
            "input_memory_mb": round(input_memory / (1024 * 1024), 4),
            "weights_memory_mb": round(weights_memory / (1024 * 1024), 4),
            "activation_memory_mb": round(activation_memory / (1024 * 1024), 4),
            "output_memory_mb": round(output_memory / (1024 * 1024), 4),
            "total_memory_mb": round(total_memory / (1024 * 1024), 4),
            "framework_overhead_mb": round(framework_overhead / (1024 * 1024), 2),
            "estimated_peak_mb": round(
                (total_memory + framework_overhead) / (1024 * 1024), 4
            ),
            "precision": precision,
            "batch_size": batch_size,
            "n_layers": n_layers,
            "layer_details": layer_details,
        }
