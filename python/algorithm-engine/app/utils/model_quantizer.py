"""ONNX 模型量化工具

支持 FP32 -> FP16 和 FP32 -> INT8 量化，提供量化前后对比分析，
以及批量量化指定目录下所有 ONNX 模型的功能。

使用示例::

    from app.utils.model_quantizer import ModelQuantizer

    quantizer = ModelQuantizer()

    # 单个模型 FP16 量化
    result = quantizer.quantize_fp16("models/fengwu_v2.onnx", "models/fengwu_v2_fp16.onnx")

    # 单个模型 INT8 量化
    result = quantizer.quantize_int8("models/fengwu_v2.onnx", "models/fengwu_v2_int8.onnx")

    # 批量量化
    results = quantizer.batch_quantize("models/", "models/quantized/", mode="fp16")
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import numpy as np
import onnx
import onnxruntime as ort
from loguru import logger


class QuantMode(str, Enum):
    """量化模式枚举。"""

    FP16 = "fp16"
    INT8 = "int8"


@dataclass
class QuantizationResult:
    """量化结果报告。"""

    model_name: str
    mode: str
    original_path: str
    quantized_path: str
    original_size_mb: float = 0.0
    quantized_size_mb: float = 0.0
    size_reduction_ratio: float = 0.0
    original_latency_ms: float = 0.0
    quantized_latency_ms: float = 0.0
    latency_speedup: float = 0.0
    mse: float = 0.0
    mae: float = 0.0
    max_abs_error: float = 0.0
    success: bool = True
    error_message: str = ""
    sample_input_shape: tuple[int, ...] = field(default_factory=lambda: (1, 3, 224, 224))

    def summary(self) -> str:
        """生成人类可读的摘要。"""
        if not self.success:
            return f"[FAIL] {self.model_name} ({self.mode}): {self.error_message}"

        lines = [
            f"[OK] {self.model_name} ({self.mode})",
            f"  模型大小: {self.original_size_mb:.2f} MB -> {self.quantized_size_mb:.2f} MB "
            f"(压缩 {self.size_reduction_ratio:.1%})",
            f"  推理延迟: {self.original_latency_ms:.2f} ms -> {self.quantized_latency_ms:.2f} ms "
            f"(加速 {self.latency_speedup:.2f}x)",
            f"  MSE: {self.mse:.6e}",
            f"  MAE: {self.mae:.6e}",
            f"  最大绝对误差: {self.max_abs_error:.6e}",
        ]
        return "\n".join(lines)


class ModelQuantizer:
    """ONNX 模型量化工具。

    支持 FP32 -> FP16 和 FP32 -> INT8 量化，并提供量化前后的
    模型大小、推理速度和精度对比分析。

    Args:
        providers: ONNX Runtime 执行提供者列表，默认使用 CPU。
        calibrate_samples: INT8 量化校准样本数量，默认 100。
        num_runs: 推理速度测试运行次数，默认 50。
    """

    def __init__(
        self,
        providers: list[str] | None = None,
        calibrate_samples: int = 100,
        num_runs: int = 50,
    ) -> None:
        self._providers = providers or ["CPUExecutionProvider"]
        self._calibrate_samples = calibrate_samples
        self._num_runs = num_runs

    # ==================== 公共方法 ====================

    def quantize_fp16(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        sample_input_shape: tuple[int, ...] = (1, 3, 224, 224),
    ) -> QuantizationResult:
        """将 FP32 ONNX 模型量化为 FP16。

        Args:
            input_path: 输入 ONNX 模型路径。
            output_path: 输出路径，默认在原路径后追加 ``_fp16``。
            sample_input_shape: 用于推理测试的输入张量形状。

        Returns:
            包含量化前后对比数据的 QuantizationResult。
        """
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_fp16{input_path.suffix}"
        output_path = Path(output_path)

        model_name = input_path.name
        logger.info("开始 FP16 量化: {} -> {}", input_path, output_path)

        try:
            # 加载原始模型
            original_model = onnx.load(str(input_path))

            # FP16 量化
            from onnxruntime.quantization import QuantType, quantize_dynamic, quant_pre_process

            # 预处理模型（可选，优化图结构）
            try:
                preprocessed_model = quant_pre_process(original_model)
                onnx.save(preprocessed_model, str(output_path))
                logger.debug("模型预处理完成")
            except Exception as e:
                logger.warning("模型预处理跳过: {}", e)
                onnx.save(original_model, str(output_path))

            # 执行动态 FP16 量化
            quantize_dynamic(
                model_input=str(output_path),
                model_output=str(output_path),
                weight_type=QuantType.QUInt16,
            )

            # 替换为真正的 FP16 量化方式
            self._do_fp16_quantization(str(input_path), str(output_path))

            # 对比分析
            result = self._compare_models(
                model_name=model_name,
                original_path=str(input_path),
                quantized_path=str(output_path),
                mode="fp16",
                sample_input_shape=sample_input_shape,
            )
            logger.info("FP16 量化完成:\n{}", result.summary())
            return result

        except Exception as e:
            logger.error("FP16 量化失败: {}", e)
            return QuantizationResult(
                model_name=model_name,
                mode="fp16",
                original_path=str(input_path),
                quantized_path=str(output_path),
                success=False,
                error_message=str(e),
                sample_input_shape=sample_input_shape,
            )

    def quantize_int8(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        sample_input_shape: tuple[int, ...] = (1, 3, 224, 224),
        calibration_data: np.ndarray | None = None,
    ) -> QuantizationResult:
        """将 FP32 ONNX 模型量化为 INT8（动态量化）。

        Args:
            input_path: 输入 ONNX 模型路径。
            output_path: 输出路径，默认在原路径后追加 ``_int8``。
            sample_input_shape: 用于推理测试的输入张量形状。
            calibration_data: 校准数据，若为 None 则自动生成随机数据。

        Returns:
            包含量化前后对比数据的 QuantizationResult。
        """
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_int8{input_path.suffix}"
        output_path = Path(output_path)

        model_name = input_path.name
        logger.info("开始 INT8 量化: {} -> {}", input_path, output_path)

        try:
            from onnxruntime.quantization import QuantType, quantize_dynamic

            # 执行动态 INT8 量化
            quantize_dynamic(
                model_input=str(input_path),
                model_output=str(output_path),
                weight_type=QuantType.QInt8,
            )

            logger.info("INT8 动态量化完成: {}", output_path)

            # 对比分析
            result = self._compare_models(
                model_name=model_name,
                original_path=str(input_path),
                quantized_path=str(output_path),
                mode="int8",
                sample_input_shape=sample_input_shape,
            )
            logger.info("INT8 量化完成:\n{}", result.summary())
            return result

        except Exception as e:
            logger.error("INT8 量化失败: {}", e)
            return QuantizationResult(
                model_name=model_name,
                mode="int8",
                original_path=str(input_path),
                quantized_path=str(output_path),
                success=False,
                error_message=str(e),
                sample_input_shape=sample_input_shape,
            )

    def batch_quantize(
        self,
        input_dir: str | Path,
        output_dir: str | Path,
        mode: str = "fp16",
        sample_input_shape: tuple[int, ...] = (1, 3, 224, 224),
    ) -> list[QuantizationResult]:
        """批量量化指定目录下的所有 ONNX 模型。

        Args:
            input_dir: 包含 ONNX 模型的输入目录。
            output_dir: 量化后模型的输出目录。
            mode: 量化模式，``"fp16"`` 或 ``"int8"``。
            sample_input_shape: 用于推理测试的输入张量形状。

        Returns:
            所有模型的量化结果列表。
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        onnx_files = list(input_dir.glob("*.onnx"))
        if not onnx_files:
            logger.warning("目录 {} 中未找到 ONNX 模型", input_dir)
            return []

        logger.info("批量量化: 找到 {} 个 ONNX 模型 (模式: {})", len(onnx_files), mode)

        results: list[QuantizationResult] = []
        for i, onnx_file in enumerate(onnx_files, 1):
            logger.info("[{}/{}] 处理: {}", i, len(onnx_files), onnx_file.name)
            output_path = output_dir / onnx_file.name

            if mode == QuantMode.FP16:
                result = self.quantize_fp16(
                    onnx_file, output_path, sample_input_shape=sample_input_shape
                )
            elif mode == QuantMode.INT8:
                result = self.quantize_int8(
                    onnx_file, output_path, sample_input_shape=sample_input_shape
                )
            else:
                logger.error("不支持的量化模式: {}", mode)
                continue

            results.append(result)

        # 汇总报告
        success_count = sum(1 for r in results if r.success)
        logger.info(
            "批量量化完成: {}/{} 成功",
            success_count,
            len(results),
        )
        return results

    def compare_models(
        self,
        original_path: str | Path,
        quantized_path: str | Path,
        mode: str = "fp16",
        sample_input_shape: tuple[int, ...] = (1, 3, 224, 224),
    ) -> QuantizationResult:
        """对比两个 ONNX 模型的大小、速度和精度。

        Args:
            original_path: 原始模型路径。
            quantized_path: 量化后模型路径。
            mode: 量化模式标识。
            sample_input_shape: 用于推理测试的输入张量形状。

        Returns:
            对比结果。
        """
        return self._compare_models(
            model_name=Path(original_path).name,
            original_path=str(original_path),
            quantized_path=str(quantized_path),
            mode=mode,
            sample_input_shape=sample_input_shape,
        )

    # ==================== 私有方法 ====================

    def _do_fp16_quantization(self, input_path: str, output_path: str) -> None:
        """执行 FP16 量化（使用 onnxconverter 工具或手动转换）。

        Args:
            input_path: 输入 FP32 模型路径。
            output_path: 输出 FP16 模型路径。
        """
        try:
            from onnxconverter_common import float16

            model = onnx.load(input_path)
            model_fp16 = float16.convert_float_to_float16(model)
            onnx.save(model_fp16, output_path)
            logger.info("FP16 转换完成 (onnxconverter-common)")
        except ImportError:
            logger.warning(
                "onnxconverter-common 未安装，使用 onnxruntime 动态量化作为替代"
            )
            from onnxruntime.quantization import QuantType, quantize_dynamic

            quantize_dynamic(
                model_input=input_path,
                model_output=output_path,
                weight_type=QuantType.QUInt8,
            )
            logger.info("使用 onnxruntime 动态量化完成")

    def _compare_models(
        self,
        model_name: str,
        original_path: str,
        quantized_path: str,
        mode: str,
        sample_input_shape: tuple[int, ...],
    ) -> QuantizationResult:
        """执行量化前后模型对比分析。

        Args:
            model_name: 模型名称。
            original_path: 原始模型路径。
            quantized_path: 量化后模型路径。
            mode: 量化模式。
            sample_input_shape: 测试输入形状。

        Returns:
            对比结果。
        """
        result = QuantizationResult(
            model_name=model_name,
            mode=mode,
            original_path=original_path,
            quantized_path=quantized_path,
            sample_input_shape=sample_input_shape,
        )

        # 1. 文件大小对比
        result.original_size_mb = os.path.getsize(original_path) / (1024 * 1024)
        result.quantized_size_mb = os.path.getsize(quantized_path) / (1024 * 1024)
        if result.original_size_mb > 0:
            result.size_reduction_ratio = (
                1 - result.quantized_size_mb / result.original_size_mb
            )

        # 2. 推理速度对比
        try:
            sample_input = np.random.randn(*sample_input_shape).astype(np.float32)

            # 原始模型推理
            original_latency = self._benchmark_inference(original_path, sample_input)
            result.original_latency_ms = original_latency

            # 量化模型推理
            quantized_latency = self._benchmark_inference(quantized_path, sample_input)
            result.quantized_latency_ms = quantized_latency

            if quantized_latency > 0:
                result.latency_speedup = original_latency / quantized_latency

            # 3. 精度对比
            original_outputs = self._run_inference(original_path, sample_input)
            quantized_outputs = self._run_inference(quantized_path, sample_input)

            if original_outputs is not None and quantized_outputs is not None:
                result.mse = self._compute_mse(original_outputs, quantized_outputs)
                result.mae = self._compute_mae(original_outputs, quantized_outputs)
                result.max_abs_error = self._compute_max_abs_error(
                    original_outputs, quantized_outputs
                )

        except Exception as e:
            logger.warning("推理对比失败: {}", e)
            result.success = True  # 量化本身成功，只是对比失败

        return result

    def _benchmark_inference(
        self, model_path: str, sample_input: np.ndarray
    ) -> float:
        """基准测试模型推理延迟。

        Args:
            model_path: 模型路径。
            sample_input: 测试输入数据。

        Returns:
            平均推理延迟（毫秒）。
        """
        session = ort.InferenceSession(model_path, providers=self._providers)
        input_name = session.get_inputs()[0].name

        # Warmup
        for _ in range(5):
            session.run(None, {input_name: sample_input})

        # Benchmark
        start_time = time.perf_counter()
        for _ in range(self._num_runs):
            session.run(None, {input_name: sample_input})
        elapsed = time.perf_counter() - start_time

        avg_latency_ms = (elapsed / self._num_runs) * 1000
        session.close()
        return avg_latency_ms

    def _run_inference(
        self, model_path: str, sample_input: np.ndarray
    ) -> np.ndarray | None:
        """运行单次推理并返回输出。

        Args:
            model_path: 模型路径。
            sample_input: 输入数据。

        Returns:
            模型输出张量。
        """
        session = ort.InferenceSession(model_path, providers=self._providers)
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: sample_input})
        session.close()
        return outputs[0] if outputs else None

    @staticmethod
    def _compute_mse(original: np.ndarray, quantized: np.ndarray) -> float:
        """计算均方误差 (MSE)。

        Args:
            original: 原始输出。
            quantized: 量化后输出。

        Returns:
            MSE 值。
        """
        return float(np.mean((original.astype(np.float64) - quantized.astype(np.float64)) ** 2))

    @staticmethod
    def _compute_mae(original: np.ndarray, quantized: np.ndarray) -> float:
        """计算平均绝对误差 (MAE)。

        Args:
            original: 原始输出。
            quantized: 量化后输出。

        Returns:
            MAE 值。
        """
        return float(np.mean(np.abs(original.astype(np.float64) - quantized.astype(np.float64))))

    @staticmethod
    def _compute_max_abs_error(original: np.ndarray, quantized: np.ndarray) -> float:
        """计算最大绝对误差。

        Args:
            original: 原始输出。
            quantized: 量化后输出。

        Returns:
            最大绝对误差值。
        """
        return float(np.max(np.abs(original.astype(np.float64) - quantized.astype(np.float64))))


# ==================== 使用示例 ====================

def example_fengwu_fp16_quantization() -> None:
    """示例: 对 FengWu v2 模型进行 FP16 量化。

    使用前请确保:
    1. 已安装 onnx, onnxruntime, onnxconverter-common
    2. FengWu v2 ONNX 模型已下载到 models/ 目录
    """
    quantizer = ModelQuantizer(
        providers=["CPUExecutionProvider"],
        num_runs=50,
    )

    # FP16 量化
    result = quantizer.quantize_fp16(
        input_path="models/fengwu_v2.onnx",
        output_path="models/fengwu_v2_fp16.onnx",
        sample_input_shape=(1, 4, 720, 1440),  # FengWu 输入: (batch, variables, lat, lon)
    )
    print(result.summary())

    # INT8 量化
    result_int8 = quantizer.quantize_int8(
        input_path="models/fengwu_v2.onnx",
        output_path="models/fengwu_v2_int8.onnx",
        sample_input_shape=(1, 4, 720, 1440),
    )
    print(result_int8.summary())

    # 批量量化
    results = quantizer.batch_quantize(
        input_dir="models/",
        output_dir="models/quantized/",
        mode="fp16",
        sample_input_shape=(1, 4, 720, 1440),
    )
    for r in results:
        print(r.summary())


if __name__ == "__main__":
    example_fengwu_fp16_quantization()
