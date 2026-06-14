"""稀疏高斯过程模型.

使用诱导点方法降低高斯过程回归的计算复杂度，适合大规模气象数据。
通过选取少量诱导点近似完整高斯过程，将计算复杂度从 O(n^3) 降至 O(nm^2)。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
from scipy.spatial.distance import cdist

logger = logging.getLogger(__name__)


class SparseGPModel:
    """稀疏高斯过程回归模型.

    基于诱导点方法的高斯过程近似，适用于大规模气象场数据。
    通过在训练数据中选取少量诱导点来近似完整核矩阵，
    显著降低计算和存储开销。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.n_inducing = self.config.get("n_inducing", 100)
        self.kernel_type = self.config.get("kernel_type", "rbf")
        self.length_scale = self.config.get("length_scale", 1.0)
        self.signal_variance = self.config.get("signal_variance", 1.0)
        self.noise_variance = self.config.get("noise_variance", 0.1)
        np.random.seed(42)

    def predict(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行稀疏高斯过程回归预测.

        Args:
            params: 包含以下键的字典:
                - train_x: 训练输入数据，形状 (n_train, d)
                - train_y: 训练目标数据，形状 (n_train,)
                - test_x: 测试输入数据，形状 (n_test, d)
                - n_inducing: 诱导点数量
                - kernel_type: 核函数类型 (rbf / matern / linear)

        Returns:
            包含预测均值、标准差、诱导点位置和计算节省比的字典。
        """
        np.random.seed(42)

        train_x = np.asarray(params.get("train_x", np.zeros((100, 2))))
        train_y = np.asarray(params.get("train_y", np.zeros(100)))
        test_x = np.asarray(params.get("test_x", np.zeros((20, 2))))
        n_inducing = params.get("n_inducing", self.n_inducing)
        kernel_type = params.get("kernel_type", self.kernel_type)
        length_scale = params.get("length_scale", self.length_scale)
        signal_variance = params.get("signal_variance", self.signal_variance)

        n_train = len(train_x)
        n_test = len(test_x)

        # 选取诱导点
        inducing_points = self._select_inducing_points(train_x, n_inducing)

        # 计算核矩阵
        K_mm = self._compute_kernel(  # noqa: N806
            inducing_points, inducing_points, kernel_type, length_scale, signal_variance
        )
        K_nm = self._compute_kernel(  # noqa: N806
            train_x, inducing_points, kernel_type, length_scale, signal_variance
        )
        K_sm = self._compute_kernel(  # noqa: N806
            test_x, inducing_points, kernel_type, length_scale, signal_variance
        )
        K_ss = self._compute_kernel(  # noqa: N806
            test_x, test_x, kernel_type, length_scale, signal_variance
        )

        # 添加噪声正则化
        K_mm_reg = K_mm + 1e-6 * np.eye(n_inducing)  # noqa: N806

        try:
            L_mm = np.linalg.cholesky(K_mm_reg)  # noqa: N806

            # 计算近似均值: K_sm @ K_mm^{-1} @ K_mm @ K_mm^{-1} @ K_nm^T @ y
            # 简化: K_sm @ K_mm^{-1} @ (K_nm^T @ y)
            A = np.linalg.solve(L_mm, K_nm.T)  # (m, n)
            A = np.linalg.solve(L_mm.T, A)  # (m, n)
            mean = K_sm @ np.linalg.solve(K_mm_reg, K_nm.T @ train_y)

            # 计算近似方差
            # Var = K_ss - K_sm @ K_mm^{-1} @ K_ms
            #   + K_sm @ K_mm^{-1} @ K_nm^T
            #   @ (K_nn + sigma^2 I)^{-1} @ K_nm @ K_mm^{-1} @ K_ms
            # 使用 FITC 近似简化
            B = np.linalg.solve(L_mm, K_sm.T)  # (m, n_test)
            B = np.linalg.solve(L_mm.T, B)  # (m, n_test)
            proj_cov = K_ss - K_sm @ B  # (n_test, n_test)

            # 添加数据项贡献
            diag_Knn = np.diag(self._compute_kernel(train_x, train_x, kernel_type, length_scale, signal_variance))
            diag_Qnn = np.sum(K_nm * A.T, axis=1)  # 投影方差
            sigma2 = self.noise_variance
            Lambda_inv = 1.0 / (diag_Knn - diag_Qnn + sigma2 + 1e-8)  # (n,)
            C = A * Lambda_inv[np.newaxis, :]  # (m, n)
            D = np.linalg.solve(L_mm, C @ K_nm.T)  # (m, m)
            D = np.linalg.solve(L_mm.T, D)  # (m, m)

            var = np.diag(proj_cov) + np.sum(K_sm * np.linalg.solve(K_mm_reg, D @ K_sm.T).T, axis=1)
            var = np.maximum(var, 1e-10)
        except np.linalg.LinAlgError:
            logger.warning("稀疏 GP Cholesky 分解失败，回退到简单预测")
            mean = np.zeros(n_test)
            var = np.ones(n_test) * signal_variance

        std = np.sqrt(var)

        # 计算节省比: 完整 GP 为 O(n^3)，稀疏 GP 为 O(nm^2)
        full_cost = n_train**3
        sparse_cost = n_train * n_inducing**2
        computational_saving = 1.0 - (sparse_cost / max(full_cost, 1))

        return {
            "mean": mean.tolist(),
            "std": std.tolist(),
            "inducing_points": inducing_points.tolist(),
            "computational_saving": float(computational_saving),
            "n_inducing": n_inducing,
            "n_train": n_train,
            "n_test": n_test,
        }

    def _select_inducing_points(
        self,
        train_x: np.ndarray,
        n_inducing: int,
    ) -> np.ndarray:
        """选取诱导点.

        使用 k-means++ 初始化策略从训练数据中选取诱导点。

        Args:
            train_x: 训练输入数据，形状 (n, d).
            n_inducing: 诱导点数量.

        Returns:
            诱导点数组，形状 (n_inducing, d).
        """
        n = len(train_x)
        n_inducing = min(n_inducing, n)

        if n_inducing >= n:
            return train_x.copy()

        # k-means++ 初始化
        indices = [np.random.randint(n)]
        for _ in range(1, n_inducing):
            dists = cdist(train_x, train_x[indices], metric="euclidean")
            min_dists = dists.min(axis=1)
            probs = min_dists / (min_dists.sum() + 1e-10)
            idx = np.random.choice(n, p=probs)
            indices.append(idx)

        return train_x[indices].copy()

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
            x1: 第一组输入点.
            x2: 第二组输入点.
            kernel_type: 核函数类型 (rbf / matern / linear).
            length_scale: 长度尺度参数.
            signal_variance: 信号方差.

        Returns:
            核矩阵.
        """
        if kernel_type == "rbf":
            dists = cdist(x1, x2, metric="sqeuclidean")
            return signal_variance * np.exp(-0.5 * dists / length_scale**2)
        elif kernel_type == "matern":
            dists = cdist(x1, x2, metric="euclidean")
            scaled = np.sqrt(3.0) * dists / length_scale
            return signal_variance * (1.0 + scaled) * np.exp(-scaled)
        elif kernel_type == "linear":
            return signal_variance * (x1 @ x2.T)
        else:
            logger.warning("未知核函数类型 '%s'，回退到 RBF", kernel_type)
            dists = cdist(x1, x2, metric="sqeuclidean")
            return signal_variance * np.exp(-0.5 * dists / length_scale**2)
