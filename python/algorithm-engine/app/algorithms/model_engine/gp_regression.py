"""高斯过程回归模型.

用于气象场插值和预测，支持多种核函数（RBF、Matern、线性），
输出预测均值、标准差和协方差矩阵。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
from scipy.spatial.distance import cdist

logger = logging.getLogger(__name__)


class GPRegressionModel:
    """高斯过程回归模型.

    基于高斯过程回归进行气象场插值和预测，支持 RBF、Matern 和线性核函数。
    输出预测均值、标准差、协方差矩阵及超参数信息。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.kernel_type = self.config.get("kernel_type", "rbf")
        self.length_scale = self.config.get("length_scale", 1.0)
        self.signal_variance = self.config.get("signal_variance", 1.0)
        self.noise_variance = self.config.get("noise_variance", 0.1)
        np.random.seed(42)

    def predict(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行高斯过程回归预测.

        Args:
            params: 包含以下键的字典:
                - train_x: 训练输入数据，形状 (n_train, d)
                - train_y: 训练目标数据，形状 (n_train,)
                - test_x: 测试输入数据，形状 (n_test, d)
                - kernel_type: 核函数类型，可选 rbf / matern / linear
                - length_scale: 长度尺度参数
                - signal_variance: 信号方差

        Returns:
            包含预测均值、标准差、协方差矩阵和超参数的字典。
        """
        np.random.seed(42)

        train_x = np.asarray(params.get("train_x", np.zeros((10, 2))))
        train_y = np.asarray(params.get("train_y", np.zeros(10)))
        test_x = np.asarray(params.get("test_x", np.zeros((5, 2))))
        kernel_type = params.get("kernel_type", self.kernel_type)
        length_scale = params.get("length_scale", self.length_scale)
        signal_variance = params.get("signal_variance", self.signal_variance)

        n_train = len(train_x)
        n_test = len(test_x)

        # 计算核矩阵
        K = self._compute_kernel(  # noqa: N806
            train_x, train_x, kernel_type, length_scale, signal_variance
        )
        K += self.noise_variance * np.eye(n_train)
        K_s = self._compute_kernel(  # noqa: N806
            train_x, test_x, kernel_type, length_scale, signal_variance
        )
        K_ss = self._compute_kernel(  # noqa: N806
            test_x, test_x, kernel_type, length_scale, signal_variance
        )

        try:
            L = np.linalg.cholesky(K)  # noqa: N806
            alpha = np.linalg.solve(L.T, np.linalg.solve(L, train_y))
            mean = K_s.T @ alpha
            v = np.linalg.solve(L, K_s)
            cov = K_ss - v.T @ v
            var = np.diag(cov)
            var = np.maximum(var, 1e-10)
        except np.linalg.LinAlgError:
            logger.warning("Cholesky 分解失败，回退到正则化求解")
            K_reg = K + 1e-6 * np.eye(n_train)  # noqa: N806
            try:
                L = np.linalg.cholesky(K_reg)  # noqa: N806
                alpha = np.linalg.solve(L.T, np.linalg.solve(L, train_y))
                mean = K_s.T @ alpha
                v = np.linalg.solve(L, K_s)
                cov = K_ss - v.T @ v
                var = np.diag(cov)
                var = np.maximum(var, 1e-10)
            except np.linalg.LinAlgError:
                mean = np.zeros(n_test)
                var = np.ones(n_test) * signal_variance
                cov = np.eye(n_test) * signal_variance

        std = np.sqrt(var)

        hyperparameters = {
            "kernel_type": kernel_type,
            "length_scale": float(length_scale),
            "signal_variance": float(signal_variance),
            "noise_variance": float(self.noise_variance),
        }

        return {
            "mean": mean.tolist(),
            "std": std.tolist(),
            "covariance": cov.tolist(),
            "hyperparameters": hyperparameters,
            "n_train": n_train,
            "n_test": n_test,
        }

    def _compute_kernel(
        self,
        x1: np.ndarray,
        x2: np.ndarray,
        kernel_type: str,
        length_scale: float,
        signal_variance: float,
    ) -> np.ndarray:
        """计算核矩阵.

        Args:
            x1: 第一组输入点，形状 (n1, d).
            x2: 第二组输入点，形状 (n2, d).
            kernel_type: 核函数类型 (rbf / matern / linear).
            length_scale: 长度尺度参数.
            signal_variance: 信号方差.

        Returns:
            核矩阵，形状 (n1, n2).
        """
        if kernel_type == "rbf":
            return self._rbf_kernel(x1, x2, length_scale, signal_variance)
        elif kernel_type == "matern":
            return self._matern_kernel(x1, x2, length_scale, signal_variance)
        elif kernel_type == "linear":
            return self._linear_kernel(x1, x2, signal_variance)
        else:
            logger.warning("未知核函数类型 '%s'，回退到 RBF", kernel_type)
            return self._rbf_kernel(x1, x2, length_scale, signal_variance)

    @staticmethod
    def _rbf_kernel(
        x1: np.ndarray,
        x2: np.ndarray,
        length_scale: float,
        signal_variance: float,
    ) -> np.ndarray:
        """RBF（径向基函数）核."""
        dists = cdist(x1, x2, metric="sqeuclidean")
        return signal_variance * np.exp(-0.5 * dists / length_scale**2)

    @staticmethod
    def _matern_kernel(
        x1: np.ndarray,
        x2: np.ndarray,
        length_scale: float,
        signal_variance: float,
        nu: float = 1.5,
    ) -> np.ndarray:
        """Matern 核 (nu=1.5).

        Args:
            x1: 第一组输入点.
            x2: 第二组输入点.
            length_scale: 长度尺度.
            signal_variance: 信号方差.
            nu: Matern 参数，支持 0.5、1.5、2.5.

        Returns:
            Matern 核矩阵.
        """
        dists = cdist(x1, x2, metric="euclidean")
        scaled_dists = np.sqrt(3.0) * dists / length_scale
        if nu == 0.5:
            return signal_variance * np.exp(-scaled_dists)
        elif nu == 1.5:
            return signal_variance * (1.0 + scaled_dists) * np.exp(-scaled_dists)
        elif nu == 2.5:
            t = np.sqrt(5.0) * dists / length_scale
            return signal_variance * (1.0 + t + t**2 / 3.0) * np.exp(-t)
        else:
            return signal_variance * (1.0 + scaled_dists) * np.exp(-scaled_dists)

    @staticmethod
    def _linear_kernel(
        x1: np.ndarray,
        x2: np.ndarray,
        signal_variance: float,
    ) -> np.ndarray:
        """线性核."""
        return signal_variance * (x1 @ x2.T)
