"""
FengWu Weather Model Inference Engine

Wraps the FengWu ONNX model for global weather forecasting.
Input: Two consecutive 6-hour ERA5 frames (69×721×1440)
Output: Up to 56 forecast steps (14 days, 6-hour intervals)
"""

from __future__ import annotations

import os
import time
import logging
import threading
import atexit
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class FengWuEngine:
    """FengWu weather forecasting inference engine."""

    # 69 atmospheric variables: 4 surface + 13 levels × 5 upper-air
    N_VARS = 69
    N_LAT = 721
    N_LON = 1440
    N_LEVELS = 13

    # Variable ordering
    # Surface: u10, v10, t2m, msl
    # Upper-air per level: z, q, u, v, t (13 levels: 50,100,150,200,250,300,400,500,600,700,850,925,1000 hPa)

    def __init__(
        self,
        model_path: str = "/app/model/fengwu_v2.onnx",
        data_mean_path: str = "/app/model/data_mean.npy",
        data_std_path: str = "/app/model/data_std.npy",
        use_gpu: bool = False,
        intra_threads: int = 4,
    ):
        self.model_path = model_path
        self.data_mean_path = data_mean_path
        self.data_std_path = data_std_path
        self.use_gpu = use_gpu
        self.intra_threads = intra_threads

        self._session = None
        self._data_mean = None
        self._data_std = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self) -> bool:
        """Load the ONNX model and normalization data."""
        import onnxruntime as ort

        if not os.path.exists(self.model_path):
            logger.error(f"Model file not found: {self.model_path}")
            return False

        try:
            # Configure ONNX Runtime
            options = ort.SessionOptions()
            options.enable_cpu_mem_arena = False
            options.enable_mem_pattern = False
            options.enable_mem_reuse = False
            options.intra_op_num_threads = self.intra_threads

            # Select execution provider
            providers = []
            if self.use_gpu:
                cuda_opts = {"arena_extend_strategy": "kSameAsRequested"}
                providers.append(("CUDAExecutionProvider", cuda_opts))
            providers.append("CPUExecutionProvider")

            self._session = ort.InferenceSession(
                self.model_path,
                sess_options=options,
                providers=providers,
            )

            # Load normalization parameters
            self._data_mean = np.load(self.data_mean_path)[:, np.newaxis, np.newaxis]
            self._data_std = np.load(self.data_std_path)[:, np.newaxis, np.newaxis]

            self._loaded = True
            provider = self._session.get_providers()
            logger.info(f"FengWu model loaded. Providers: {provider}")
            return True

        except Exception as e:
            logger.error(f"Failed to load FengWu model: {e}")
            self._loaded = False
            return False

    def predict(
        self,
        input_0h: np.ndarray,
        input_6h: np.ndarray,
        steps: int = 56,
    ) -> list[np.ndarray]:
        """
        Run FengWu inference.

        Args:
            input_0h: Atmospheric data at T+0h, shape (69, 721, 1440)
            input_6h: Atmospheric data at T+6h, shape (69, 721, 1440)
            steps: Number of 6-hour forecast steps (max 56 = 14 days)

        Returns:
            List of forecast arrays, each shape (69, 721, 1440)
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        steps = min(steps, 56)

        # Normalize inputs
        input1 = ((input_0h.astype(np.float32) - self._data_mean) / self._data_std)
        input2 = ((input_6h.astype(np.float32) - self._data_mean) / self._data_std)

        # Combine into model input: (1, 138, 721, 1440)
        model_input = np.concatenate((input1, input2), axis=0)[np.newaxis, :, :, :]
        model_input = model_input.astype(np.float32)

        results = []
        start_time = time.time()

        for step in range(steps):
            output = self._session.run(None, {"input": model_input})[0]

            # Roll: shift 69 channels from output, append 69 from previous input
            model_input = np.concatenate(
                (model_input[:, self.N_VARS:, :, :], output[:, :self.N_VARS, :, :]),
                axis=1,
            )

            # Denormalize
            forecast = (output[0, :self.N_VARS, :, :] * self._data_std) + self._data_mean
            results.append(forecast)

        elapsed = time.time() - start_time
        logger.info(
            f"Inference complete: {steps} steps in {elapsed:.1f}s "
            f"({elapsed / steps:.1f}s/step)"
        )
        return results

    def predict_surface(
        self,
        input_0h: np.ndarray,
        input_6h: np.ndarray,
        steps: int = 56,
    ) -> list[dict]:
        """
        Run inference and extract surface variables only.

        Returns list of dicts with u10, v10, t2m, msl per step.
        """
        results = self.predict(input_0h, input_6h, steps)
        surface = []
        for r in results:
            surface.append({
                "u10": r[0].tolist(),     # 10m U wind
                "v10": r[1].tolist(),     # 10m V wind
                "t2m": r[2].tolist(),     # 2m temperature
                "msl": r[3].tolist(),     # Mean sea level pressure
            })
        return surface


# Global engine instance with thread safety
_engine: Optional[FengWuEngine] = None
_engine_lock = threading.Lock()


def _cleanup_engine() -> None:
    """Cleanup global engine instance on program exit."""
    global _engine
    if _engine is not None:
        logger.info("Shutting down FengWu engine")
        if _engine._session is not None:
            del _engine._session
        _engine = None


atexit.register(_cleanup_engine)


def get_engine() -> Optional[FengWuEngine]:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = FengWuEngine(
                    model_path=os.environ.get("FENGWU_MODEL_PATH", "/app/model/fengwu_v2.onnx"),
                    data_mean_path=os.environ.get("FENGWU_MEAN_PATH", "/app/model/data_mean.npy"),
                    data_std_path=os.environ.get("FENGWU_STD_PATH", "/app/model/data_std.npy"),
                    use_gpu=os.environ.get("FENGWU_USE_GPU", "false").lower() == "true",
                    intra_threads=int(os.environ.get("FENGWU_THREADS", "4")),
                )
                _engine.load()
    return _engine
