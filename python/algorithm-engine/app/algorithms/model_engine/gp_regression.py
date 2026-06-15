"""高斯过程回归模型.

用于气象场插值和预测，支持多种核函数（RBF、Matern、线性），
输出预测均值、标准差和协方差矩阵。

支持不确定性量化：
- predict_with_uncertainty(): 返回预测值 + 标准差
- compute_confidence_interval(): 计算 95% 置信区间
- compute_prediction_variance(): 计算预测方差
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

    支持完整的不确定性量化能力，包括预测方差、标准差和置信区间计算。
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

    # ================================================================
    # 不确定性量化方法
    # ================================================================

    def predict_with_uncertainty(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行 GPR 预测并返回完整的不确定性信息.

        在标准 predict() 基础上，额外返回标准差、方差、
        归一化不确定性指标和预测质量评估。

        Args:
            params: 与 predict() 相同的参数字典.

        Returns:
            包含以下键的字典:
                - mean: 预测均值列表
                - std: 预测标准差列表
                - variance: 预测方差列表
                - covariance: 完整协方差矩阵
                - confidence_95_lower: 95% 置信区间下界
                - confidence_95_upper: 95% 置信区间上界
                - normalized_uncertainty: 归一化不确定性 [0, 1]
                - prediction_quality: 预测质量指标
                - hyperparameters: 超参数信息
                - n_train: 训练样本数
                - n_test: 测试样本数
        """
        result = self.predict(params)

        mean = np.asarray(result["mean"])
        std = np.asarray(result["std"])
        variance = np.asarray(result.get("covariance", []))
        if variance.ndim == 2:
            variance_diag = np.diag(variance)
        else:
            variance_diag = std**2

        # 归一化不确定性：将标准差映射到 [0, 1] 区间
        max_std = std.max() + 1e-10
        normalized_uncertainty = (std / max_std).tolist()

        # 预测质量指标：基于平均相对不确定性
        mean_std = float(std.mean())
        mean_abs = float(np.abs(mean).mean()) + 1e-10
        prediction_quality = float(np.clip(1.0 - mean_std / mean_abs, 0.0, 1.0))

        return {
            "mean": result["mean"],
            "std": result["std"],
            "variance": variance_diag.tolist(),
            "covariance": result["covariance"],
            "confidence_95_lower": (mean - 1.96 * std).tolist(),
            "confidence_95_upper": (mean + 1.96 * std).tolist(),
            "normalized_uncertainty": normalized_uncertainty,
            "prediction_quality": prediction_quality,
            "hyperparameters": result["hyperparameters"],
            "n_train": result["n_train"],
            "n_test": result["n_test"],
        }

    def compute_confidence_interval(
        self,
        params: dict[str, Any],
        confidence_level: float = 0.95,
    ) -> dict[str, Any]:
        """计算 GPR 预测的置信区间.

        Args:
            params: 与 predict() 相同的参数字典.
            confidence_level: 置信水平，默认 0.95（95%）.
                支持常见值：0.68 (1-sigma), 0.90, 0.95 (2-sigma), 0.99 (3-sigma).

        Returns:
            包含以下键的字典:
                - mean: 预测均值
                - std: 预测标准差
                - lower_bound: 置信区间下界
                - upper_bound: 置信区间上界
                - interval_width: 置信区间宽度
                - z_score: 使用的 Z 分位数
                - confidence_level: 实际置信水平
                - n_test: 测试点数
        """
        # 从标准正态分布获取 Z 分位数
        z_scores = {
            0.68: 1.0,
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576,
        }
        z = z_scores.get(confidence_level, 1.96)
        logger.info(
            "计算置信区间: confidence_level=%.2f, z_score=%.3f",
            confidence_level,
            z,
        )

        result = self.predict(params)
        mean = np.asarray(result["mean"])
        std = np.asarray(result["std"])

        lower_bound = mean - z * std
        upper_bound = mean + z * std
        interval_width = upper_bound - lower_bound

        return {
            "mean": mean.tolist(),
            "std": std.tolist(),
            "lower_bound": lower_bound.tolist(),
            "upper_bound": upper_bound.tolist(),
            "interval_width": interval_width.tolist(),
            "z_score": float(z),
            "confidence_level": float(confidence_level),
            "n_test": result["n_test"],
        }

    def compute_prediction_variance(self, params: dict[str, Any]) -> dict[str, Any]:
        """计算 GPR 预测方差及其分解.

        将预测方差分解为信号方差（核函数贡献）和噪声方差两部分，
        并提供方差统计摘要，用于评估模型在不同区域的预测可靠性。

        Args:
            params: 与 predict() 相同的参数字典.

        Returns:
            包含以下键的字典:
                - predictive_variance: 总预测方差
                - signal_variance: 信号方差分量（来自核函数）
                - noise_variance: 噪声方差分量
                - std: 预测标准差
                - coefficient_of_variation: 变异系数
                - variance_statistics: 方差统计摘要
                - n_test: 测试点数
        """
        result = self.predict(params)
        std = np.asarray(result["std"])
        predictive_variance = std**2

        # 信号方差分量：总方差减去噪声方差（取下界避免负值）
        signal_var = np.maximum(predictive_variance - self.noise_variance, 0.0)
        noise_var = np.full_like(predictive_variance, self.noise_variance)

        # 变异系数：标准差 / |均值|
        mean = np.asarray(result["mean"])
        abs_mean = np.abs(mean) + 1e-10
        cv = (std / abs_mean).tolist()

        # 方差统计摘要
        variance_statistics = {
            "min": float(predictive_variance.min()),
            "max": float(predictive_variance.max()),
            "mean": float(predictive_variance.mean()),
            "median": float(np.median(predictive_variance)),
            "std": float(np.std(predictive_variance)),
            "high_uncertainty_ratio": float(
                np.mean(predictive_variance > np.percentile(predictive_variance, 75))
            ),
        }

        return {
            "predictive_variance": predictive_variance.tolist(),
            "signal_variance": signal_var.tolist(),
            "noise_variance": noise_var.tolist(),
            "std": std.tolist(),
            "coefficient_of_variation": cv,
            "variance_statistics": variance_statistics,
            "n_test": result["n_test"],
        }
