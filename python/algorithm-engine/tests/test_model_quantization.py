"""模型量化与 ONNX Runtime 推理单元测试。

测试覆盖：
- INT8/FP16 量化基本功能
- 量化前后模型大小对比
- 精度损失在可接受范围内
- 推理延迟降低 >= 30%
- 量化感知训练（QAT）模拟
- ONNX Runtime 推理后端
- 批量推理与性能统计
- 内存占用估算
- Adapter 注册与调用
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# 确保项目根目录在 sys.path 中
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_weights() -> np.ndarray:
    """生成模拟模型权重（He 初始化）。"""
    rng = np.random.RandomState(42)
    return rng.randn(256, 128).astype(np.float32) * np.sqrt(2.0 / 128)


@pytest.fixture
def sample_input() -> np.ndarray:
    """生成模拟推理输入数据。"""
    rng = np.random.RandomState(42)
    return rng.randn(10, 128).astype(np.float32)


@pytest.fixture
def quantizer():
    """ModelQuantizer 实例。"""
    from app.algorithms.edge.model_quantization import ModelQuantizer

    return ModelQuantizer()


@pytest.fixture
def onnx_inferencer():
    """OnnxRuntimeInferencer 实例。"""
    from app.algorithms.edge.onnx_runtime_inference import OnnxRuntimeInferencer

    return OnnxRuntimeInferencer()


# ---------------------------------------------------------------------------
# INT8 量化测试
# ---------------------------------------------------------------------------


class TestINT8Quantization:
    """INT8 量化功能测试。"""

    def test_int8_quantize_returns_int8_dtype(self, quantizer, sample_weights):
        """INT8 量化后数据类型应为 int8。"""
        quantized, info = quantizer.quantize_weights(sample_weights, "int8")
        assert quantized.dtype == np.int8
        assert info["dtype"] == "int8"

    def test_int8_quantize_range(self, quantizer, sample_weights):
        """INT8 量化值应在 [-127, 127] 范围内。"""
        quantized, _ = quantizer.quantize_weights(sample_weights, "int8")
        assert np.all(quantized >= -127)
        assert np.all(quantized <= 127)

    def test_int8_quantize_has_scale(self, quantizer, sample_weights):
        """INT8 量化信息应包含 scale。"""
        _, info = quantizer.quantize_weights(sample_weights, "int8")
        assert "scale" in info
        assert info["scale"] > 0

    def test_int8_compression_ratio(self, quantizer, sample_weights):
        """INT8 压缩比应约为 4x。"""
        size_info = quantizer.compare_model_size(sample_weights, "int8")
        assert size_info["compression_ratio"] == pytest.approx(4.0, rel=0.01)

    def test_int8_model_size_reduction(self, quantizer, sample_weights):
        """INT8 量化后模型大小应为原始的 1/4。"""
        size_info = quantizer.compare_model_size(sample_weights, "int8")
        assert size_info["quantized_size_bytes"] == size_info["original_size_bytes"] // 4


# ---------------------------------------------------------------------------
# FP16 量化测试
# ---------------------------------------------------------------------------


class TestFP16Quantization:
    """FP16 量化功能测试。"""

    def test_fp16_quantize_returns_float16_dtype(self, quantizer, sample_weights):
        """FP16 量化后数据类型应为 float16。"""
        quantized, info = quantizer.quantize_weights(sample_weights, "fp16")
        assert quantized.dtype == np.float16
        assert info["dtype"] == "float16"

    def test_fp16_compression_ratio(self, quantizer, sample_weights):
        """FP16 压缩比应约为 2x。"""
        size_info = quantizer.compare_model_size(sample_weights, "fp16")
        assert size_info["compression_ratio"] == pytest.approx(2.0, rel=0.01)

    def test_fp16_model_size_reduction(self, quantizer, sample_weights):
        """FP16 量化后模型大小应为原始的 1/2。"""
        size_info = quantizer.compare_model_size(sample_weights, "fp16")
        assert size_info["quantized_size_bytes"] == size_info["original_size_bytes"] // 2


# ---------------------------------------------------------------------------
# 精度损失评估测试
# ---------------------------------------------------------------------------


class TestAccuracyLoss:
    """精度损失评估测试。"""

    def test_int8_accuracy_loss_acceptable(self, quantizer, sample_weights):
        """INT8 量化精度损失应在可接受范围内。

        - RMSE 应小于 0.05
        - 余弦相似度应大于 0.99
        """
        quantized, info = quantizer.quantize_weights(sample_weights, "int8")
        accuracy = quantizer.evaluate_accuracy_loss(sample_weights, quantized, info)

        assert accuracy["rmse"] < 0.05, f"INT8 RMSE {accuracy['rmse']} 超出可接受范围"
        assert accuracy["cosine_similarity"] > 0.99, f"INT8 余弦相似度 {accuracy['cosine_similarity']} 过低"

    def test_fp16_accuracy_loss_acceptable(self, quantizer, sample_weights):
        """FP16 量化精度损失应在可接受范围内。

        - RMSE 应小于 0.001
        - 余弦相似度应大于 0.9999
        """
        quantized, info = quantizer.quantize_weights(sample_weights, "fp16")
        accuracy = quantizer.evaluate_accuracy_loss(sample_weights, quantized, info)

        assert accuracy["rmse"] < 0.001, f"FP16 RMSE {accuracy['rmse']} 超出可接受范围"
        assert accuracy["cosine_similarity"] > 0.9999, f"FP16 余弦相似度 {accuracy['cosine_similarity']} 过低"

    def test_fp16_more_accurate_than_int8(self, quantizer, sample_weights):
        """FP16 精度损失应小于 INT8。"""
        q_int8, info_int8 = quantizer.quantize_weights(sample_weights, "int8")
        q_fp16, info_fp16 = quantizer.quantize_weights(sample_weights, "fp16")

        acc_int8 = quantizer.evaluate_accuracy_loss(sample_weights, q_int8, info_int8)
        acc_fp16 = quantizer.evaluate_accuracy_loss(sample_weights, q_fp16, info_fp16)

        assert acc_fp16["mse"] < acc_int8["mse"], "FP16 MSE 应小于 INT8 MSE"
        assert acc_fp16["rmse"] < acc_int8["rmse"], "FP16 RMSE 应小于 INT8 RMSE"

    def test_accuracy_report_has_required_keys(self, quantizer, sample_weights):
        """精度评估报告应包含所有必需的指标。"""
        quantized, info = quantizer.quantize_weights(sample_weights, "int8")
        accuracy = quantizer.evaluate_accuracy_loss(sample_weights, quantized, info)

        required_keys = [
            "mse",
            "rmse",
            "mean_absolute_error",
            "max_absolute_error",
            "relative_error",
            "cosine_similarity",
        ]
        for key in required_keys:
            assert key in accuracy, f"缺少精度指标: {key}"


# ---------------------------------------------------------------------------
# 推理延迟测试
# ---------------------------------------------------------------------------


class TestInferenceLatency:
    """推理延迟对比测试。"""

    def test_int8_latency_reduction(self, quantizer, sample_weights, sample_input):
        """INT8 推理延迟降低应 >= 30%。"""
        original_latency = quantizer.simulate_inference(sample_weights, sample_input, "fp32", n_runs=20)
        int8_latency = quantizer.simulate_inference(sample_weights, sample_input, "int8", n_runs=20)

        reduction = (
            (original_latency["mean_latency_ms"] - int8_latency["mean_latency_ms"])
            / original_latency["mean_latency_ms"]
            * 100
        )
        assert reduction >= 30.0, f"INT8 延迟降低 {reduction:.1f}% 未达到 30% 目标"

    def test_fp16_latency_reduction(self, quantizer, sample_weights, sample_input):
        """FP16 推理延迟降低应 >= 30%。"""
        original_latency = quantizer.simulate_inference(sample_weights, sample_input, "fp32", n_runs=20)
        fp16_latency = quantizer.simulate_inference(sample_weights, sample_input, "fp16", n_runs=20)

        reduction = (
            (original_latency["mean_latency_ms"] - fp16_latency["mean_latency_ms"])
            / original_latency["mean_latency_ms"]
            * 100
        )
        assert reduction >= 30.0, f"FP16 延迟降低 {reduction:.1f}% 未达到 30% 目标"

    def test_latency_stats_has_percentiles(self, quantizer, sample_weights, sample_input):
        """延迟统计应包含百分位数据。"""
        latency = quantizer.simulate_inference(sample_weights, sample_input, "fp32", n_runs=20)
        for key in ["p50_latency_ms", "p95_latency_ms", "p99_latency_ms"]:
            assert key in latency, f"缺少延迟统计: {key}"


# ---------------------------------------------------------------------------
# 量化感知训练（QAT）测试
# ---------------------------------------------------------------------------


class TestQAT:
    """量化感知训练模拟测试。"""

    def test_qat_returns_loss_history(self, quantizer, sample_weights):
        """QAT 应返回损失历史记录。"""
        result = quantizer.simulate_qat(sample_weights, "int8", n_epochs=5)
        assert "loss_history" in result
        assert len(result["loss_history"]) == 5

    def test_qat_returns_accuracy_history(self, quantizer, sample_weights):
        """QAT 应返回精度历史记录。"""
        result = quantizer.simulate_qat(sample_weights, "int8", n_epochs=5)
        assert "accuracy_history" in result
        assert len(result["accuracy_history"]) == 5

    def test_qat_accuracy_recovery_non_negative(self, quantizer, sample_weights):
        """QAT 精度恢复率应 >= 0。"""
        result = quantizer.simulate_qat(sample_weights, "int8", n_epochs=5)
        assert result["accuracy_recovery"] >= 0.0


# ---------------------------------------------------------------------------
# 完整量化流水线测试
# ---------------------------------------------------------------------------


class TestQuantizationPipeline:
    """完整量化流水线测试。"""

    def test_pipeline_returns_report(self, quantizer, sample_weights):
        """流水线应返回 QuantizationReport。"""
        from app.algorithms.edge.model_quantization import QuantizationReport

        report = quantizer.run_quantization_pipeline(sample_weights, model_name="test_model", quantization_type="int8")
        assert isinstance(report, QuantizationReport)

    def test_pipeline_report_has_all_fields(self, quantizer, sample_weights):
        """流水线报告应包含所有字段。"""
        report = quantizer.run_quantization_pipeline(sample_weights, model_name="test_model", quantization_type="int8")
        report_dict = report.to_dict()

        required_keys = [
            "model_name",
            "quantization_type",
            "original_size_bytes",
            "quantized_size_bytes",
            "compression_ratio",
            "original_latency_ms",
            "quantized_latency_ms",
            "latency_reduction_pct",
            "mse",
            "rmse",
            "max_absolute_error",
            "mean_absolute_error",
            "qat_applied",
        ]
        for key in required_keys:
            assert key in report_dict, f"报告缺少字段: {key}"

    def test_pipeline_with_qat(self, quantizer, sample_weights):
        """带 QAT 的流水线应正确标记。"""
        report = quantizer.run_quantization_pipeline(
            sample_weights,
            model_name="test_model",
            quantization_type="int8",
            apply_qat=True,
            qat_epochs=5,
        )
        assert report.qat_applied is True
        assert report.qat_epochs == 5

    def test_pipeline_without_qat(self, quantizer, sample_weights):
        """不带 QAT 的流水线应正确标记。"""
        report = quantizer.run_quantization_pipeline(
            sample_weights,
            model_name="test_model",
            quantization_type="fp16",
            apply_qat=False,
        )
        assert report.qat_applied is False
        assert report.qat_epochs == 0

    def test_compatible_quantize_interface(self, quantizer, sample_weights):
        """兼容原有 quantize 接口应正常工作。"""
        result = quantizer.quantize(
            {
                "weights": sample_weights.tolist(),
                "quantization_type": "int8",
            }
        )
        assert result["quantized"] is True
        assert result["quantization_type"] == "int8"
        assert "compression_ratio" in result

    def test_compatible_quantize_pipeline_mode(self, quantizer, sample_weights):
        """兼容接口的 pipeline 模式应返回报告。"""
        result = quantizer.quantize(
            {
                "weights": sample_weights.tolist(),
                "quantization_type": "int8",
                "model_name": "test",
                "run_pipeline": True,
            }
        )
        assert result["quantized"] is True
        assert "report" in result


# ---------------------------------------------------------------------------
# ONNX Runtime 推理测试
# ---------------------------------------------------------------------------


class TestOnnxRuntimeInference:
    """ONNX Runtime 推理后端测试。"""

    def test_load_model(self, onnx_inferencer):
        """模型加载应返回 InferenceSession。"""
        from app.algorithms.edge.onnx_runtime_inference import InferenceSession

        session = onnx_inferencer.load_model("test_model")
        assert isinstance(session, InferenceSession)
        assert session.model_name == "test_model"
        assert session.model_loaded is True

    def test_single_inference(self, onnx_inferencer, sample_input):
        """单次推理应返回输出字典。"""
        result = onnx_inferencer.run(sample_input)
        assert "output" in result
        assert isinstance(result["output"], np.ndarray)
        assert result["output"].shape[0] == sample_input.shape[0]

    def test_inference_output_is_probability(self, onnx_inferencer, sample_input):
        """推理输出应为概率分布（和为 1）。"""
        result = onnx_inferencer.run(sample_input)
        output = result["output"]
        # 每行概率和应为 1
        row_sums = output.sum(axis=-1)
        np.testing.assert_allclose(row_sums, 1.0, rtol=1e-5)

    def test_batch_inference(self, onnx_inferencer, sample_input):
        """批量推理应返回正确数量的结果。"""
        results, stats = onnx_inferencer.run_batch(sample_input, batch_size=3)
        assert len(results) == 4  # ceil(10/3) = 4 批
        assert stats.total_samples == 10
        assert stats.batch_size == 3
        assert stats.n_batches == 4

    def test_batch_stats_has_throughput(self, onnx_inferencer, sample_input):
        """批量推理统计应包含吞吐量。"""
        _, stats = onnx_inferencer.run_batch(sample_input, batch_size=5)
        assert stats.throughput_fps > 0
        stats_dict = stats.to_dict()
        assert "throughput_fps" in stats_dict
        assert "p95_latency_ms" in stats_dict

    def test_benchmark(self, onnx_inferencer):
        """基准测试应返回有效统计。"""
        stats = onnx_inferencer.benchmark(input_shape=(1, 64), n_warmup=3, n_runs=10, batch_size=1)
        assert stats.total_samples == 10
        assert stats.mean_latency_ms > 0
        assert stats.throughput_fps > 0

    def test_memory_estimation(self, onnx_inferencer):
        """内存估算应返回详细结果。"""
        mem = onnx_inferencer.estimate_memory(
            input_shape=(1, 64),
            output_shape=(1, 10),
            batch_size=1,
            precision="fp32",
            n_layers=4,
        )
        assert "total_memory_mb" in mem
        assert "weights_memory_mb" in mem
        assert "activation_memory_mb" in mem
        assert "layer_details" in mem
        assert len(mem["layer_details"]) == 4
        assert mem["total_memory_mb"] > 0

    def test_memory_int8_smaller_than_fp32(self, onnx_inferencer):
        """INT8 内存占用应小于 FP32。"""
        mem_fp32 = onnx_inferencer.estimate_memory(precision="fp32")
        mem_int8 = onnx_inferencer.estimate_memory(precision="int8")
        assert mem_int8["total_memory_mb"] < mem_fp32["total_memory_mb"]

    def test_compatible_infer_interface(self, onnx_inferencer, sample_input):
        """兼容 infer 接口应正常工作。"""
        result = onnx_inferencer.infer(
            {
                "input_data": sample_input.tolist(),
                "precision": "fp16",
                "batch_size": 1,
            }
        )
        assert "predictions" in result
        assert "inference_time" in result
        assert "memory_usage" in result
        assert result["precision"] == "fp16"


# ---------------------------------------------------------------------------
# Adapter 注册测试
# ---------------------------------------------------------------------------


class TestAdapters:
    """Adapter 注册与调用测试。"""

    def test_model_quantization_adapter_execute(self, sample_weights):
        """ModelQuantizationAdapter 应能正常执行。"""
        from app.adapters.edge_adapter import ModelQuantizationAdapter

        adapter = ModelQuantizationAdapter()
        result = adapter.execute(
            {
                "weights": sample_weights.tolist(),
                "quantization_type": "int8",
            }
        )
        assert result["quantized"] is True

    def test_model_quantization_adapter_metadata(self):
        """ModelQuantizationAdapter 元数据应正确。"""
        from app.adapters.edge_adapter import ModelQuantizationAdapter

        adapter = ModelQuantizationAdapter()
        meta = adapter.get_metadata()
        assert meta.id == "model_quantization"
        assert meta.category == "edge"

    def test_onnx_runtime_adapter_execute(self, sample_input):
        """OnnxRuntimeInferenceAdapter 应能正常执行。"""
        from app.adapters.edge_adapter import OnnxRuntimeInferenceAdapter

        adapter = OnnxRuntimeInferenceAdapter()
        result = adapter.execute(
            {
                "input_data": sample_input.tolist(),
                "precision": "fp16",
            }
        )
        assert "predictions" in result

    def test_onnx_runtime_adapter_metadata(self):
        """OnnxRuntimeInferenceAdapter 元数据应正确。"""
        from app.adapters.edge_adapter import OnnxRuntimeInferenceAdapter

        adapter = OnnxRuntimeInferenceAdapter()
        meta = adapter.get_metadata()
        assert meta.id == "onnx_runtime_inference"
        assert meta.category == "edge"

    def test_onnx_runtime_adapter_benchmark_mode(self):
        """OnnxRuntimeInferenceAdapter benchmark 模式应正常工作。"""
        from app.adapters.edge_adapter import OnnxRuntimeInferenceAdapter

        adapter = OnnxRuntimeInferenceAdapter()
        result = adapter.execute(
            {
                "input_data": [[1.0, 2.0, 3.0]],
                "mode": "benchmark",
                "input_shape": [1, 64],
                "n_runs": 5,
                "n_warmup": 2,
            }
        )
        assert "stats" in result
        assert "mean_latency_ms" in result["stats"]

    def test_onnx_runtime_adapter_memory_mode(self):
        """OnnxRuntimeInferenceAdapter memory 模式应正常工作。"""
        from app.adapters.edge_adapter import OnnxRuntimeInferenceAdapter

        adapter = OnnxRuntimeInferenceAdapter()
        result = adapter.execute(
            {
                "input_data": [[1.0, 2.0, 3.0]],
                "mode": "memory",
                "input_shape": [1, 64],
                "output_shape": [1, 10],
                "precision": "int8",
            }
        )
        assert "memory" in result
        assert "total_memory_mb" in result["memory"]

    def test_adapter_validate_input(self, sample_weights):
        """Adapter validate_input 应正确验证。"""
        from app.adapters.edge_adapter import ModelQuantizationAdapter

        adapter = ModelQuantizationAdapter()
        assert adapter.validate_input({"weights": sample_weights.tolist()}) is True
        assert adapter.validate_input({}) is False

    def test_adapter_health_check(self):
        """Adapter health_check 应返回 True。"""
        from app.adapters.edge_adapter import (
            ModelQuantizationAdapter,
            OnnxRuntimeInferenceAdapter,
        )

        assert ModelQuantizationAdapter().health_check() is True
        assert OnnxRuntimeInferenceAdapter().health_check() is True
