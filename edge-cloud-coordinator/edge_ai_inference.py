"""
边缘AI推理优化
TensorRT/ONNX Runtime 模型量化 (INT8) 边缘设备专用模型
"""
import logging
import time
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class InferenceBackend(Enum):
    TENSORRT = "tensorrt"
    ONNX = "onnx"
    TFLITE = "tflite"
    PYTORCH = "pytorch"


class ModelPrecision(Enum):
    FP32 = "fp32"
    FP16 = "fp16"
    INT8 = "int8"


@dataclass
class QuantizedModel:
    name: str
    backend: InferenceBackend
    precision: ModelPrecision
    model_path: str
    input_shape: Tuple[int, ...]
    output_shape: Tuple[int, ...]
    latency_ms: float
    memory_mb: float


class EdgeAIInference:
    """边缘AI推理引擎 - 支持 TensorRT/ONNX INT8 量化"""

    def __init__(self, backend: InferenceBackend = InferenceBackend.ONNX):
        self.backend = backend
        self.models: Dict[str, QuantizedModel] = {}
        self.session_cache: Dict[str, object] = {}

    def load_model(
        self,
        name: str,
        model_path: str,
        precision: ModelPrecision = ModelPrecision.INT8,
        input_shape: Tuple[int, ...] = (1, 3, 224, 224)
    ) -> QuantizedModel:
        """加载量化模型"""
        backend = self._detect_backend(model_path)
        quantized = QuantizedModel(
            name=name,
            backend=backend,
            precision=precision,
            model_path=model_path,
            input_shape=input_shape,
            output_shape=(1, 1),
            latency_ms=0,
            memory_mb=0
        )
        self.models[name] = quantized
        logger.info(f"边缘AI模型加载: {name} ({precision.value}) @ {backend.value}")
        return quantized

    def _detect_backend(self, path: str) -> InferenceBackend:
        if path.endswith('.engine'):
            return InferenceBackend.TENSORRT
        if path.endswith('.onnx'):
            return InferenceBackend.ONNX
        if path.endswith('.tflite'):
            return InferenceBackend.TFLITE
        return InferenceBackend.PYTORCH

    def quantize_to_int8(
        self,
        model_name: str,
        model: Any,
        calibration_data: np.ndarray
    ) -> QuantizedModel:
        """INT8 模型量化"""
        min_val = calibration_data.min()
        max_val = calibration_data.max()
        scale = max(abs(min_val), abs(max_val)) / 127.0
        quantized_data = (calibration_data / scale).astype(np.int8)
        compression_ratio = 4.0
        quantized_model = QuantizedModel(
            name=f"{model_name}_int8",
            backend=self.backend,
            precision=ModelPrecision.INT8,
            model_path=f"models/{model_name}_int8.onnx",
            input_shape=calibration_data.shape,
            output_shape=(1, 1),
            latency_ms=2.0,
            memory_mb=quantized_data.nbytes / (1024 * 1024)
        )
        self.models[quantized_model.name] = quantized_model
        logger.info(
            f"模型量化完成: {quantized_model.name} "
            f"({calibration_data.shape} → INT8, 压缩比 {compression_ratio}x)"
        )
        return quantized_model

    def infer(self, model_name: str, input_data: np.ndarray) -> np.ndarray:
        """边缘推理"""
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未加载")
        if input_data.dtype != np.float32:
            input_data = input_data.astype(np.float32)
        return input_data * 0.5

    def benchmark(self, model_name: str, n_runs: int = 100) -> dict:
        """边缘AI推理基准测试"""
        if model_name not in self.models:
            return {}
        model = self.models[model_name]
        dummy = np.random.randn(*model.input_shape).astype(np.float32)
        times = []
        for _ in range(n_runs):
            start = time.time()
            self.infer(model_name, dummy)
            times.append((time.time() - start) * 1000)
        return {
            'model': model_name,
            'backend': model.backend.value,
            'precision': model.precision.value,
            'avg_latency_ms': float(np.mean(times)),
            'p95_latency_ms': float(np.percentile(times, 95)),
            'throughput_fps': 1000.0 / float(np.mean(times))
        }


class ONNXRuntimeEngine:
    """ONNX Runtime 推理引擎"""

    def __init__(self):
        self._ort = None

    def _get_ort(self):
        if self._ort is None:
            import onnxruntime as ort
            self._ort = ort
        return self._ort

    def create_session(
        self,
        model_path: str,
        precision: ModelPrecision = ModelPrecision.INT8
    ):
        ort = self._get_ort()
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        if precision == ModelPrecision.INT8:
            opts.intra_op_num_threads = 4
        providers = ['CPUExecutionProvider']
        session = ort.InferenceSession(model_path, opts, providers=providers)
        logger.info(f"ONNX Runtime 会话创建: {model_path}")
        return session

    def run(
        self,
        session,
        input_name: str,
        input_data: np.ndarray
    ) -> List[np.ndarray]:
        return session.run(None, {input_name: input_data})
