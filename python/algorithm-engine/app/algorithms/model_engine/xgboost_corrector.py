"""XGBoost气象预报修正器 (XGBoost Corrector).

基于梯度提升树的气象预报偏差修正模块。
使用numpy模拟决策树集成（梯度提升框架），
支持特征重要性分析和残差统计。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class XGBoostCorrector:
    """XGBoost气象预报修正器.

    利用梯度提升决策树集成学习气象预报与观测之间的非线性映射关系，
    对预报值进行系统性偏差修正。使用numpy模拟决策树构建和梯度提升过程。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """初始化XGBoost修正器.

        Args:
            config: 配置字典，支持以下参数:
                - n_estimators: 决策树数量（提升轮数），默认 100
                - max_depth: 决策树最大深度，默认 5
                - learning_rate: 学习率（收缩系数），默认 0.1
                - min_samples_split: 节点分裂最小样本数，默认 5
                - subsample: 每轮训练的样本采样比例，默认 0.8
                - max_features: 每棵树使用的最大特征数，默认 None（使用全部）
                - reg_lambda: L2正则化系数，默认 1.0
        """
        self.config = config or {}
        self.n_estimators = self.config.get("n_estimators", 100)
        self.max_depth = self.config.get("max_depth", 5)
        self.learning_rate = self.config.get("learning_rate", 0.1)
        self.min_samples_split = self.config.get("min_samples_split", 5)
        self.subsample = self.config.get("subsample", 0.8)
        self.max_features = self.config.get("max_features", None)
        self.reg_lambda = self.config.get("reg_lambda", 1.0)
        self._trees: list[dict[str, Any]] = []
        self._feature_importance: Optional[np.ndarray] = None

    def correct(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行XGBoost气象预报偏差修正.

        Args:
            params: 参数字典，包含:
                - features: 特征矩阵，形状 (N, F)
                - targets: 目标值（观测值），形状 (N,)
                - config: 可选的运行时配置覆盖

        Returns:
            包含以下键的字典:
                - corrected_values: 修正后的预测值
                - feature_importance: 各特征的重要性分数
                - residuals: 残差统计信息
        """
        np.random.seed(42)

        features = np.asarray(
            params.get("features", np.zeros((100, 10))),
            dtype=np.float64,
        )
        targets = np.asarray(
            params.get("targets", np.zeros(100)),
            dtype=np.float64,
        )
        config = params.get("config", {})
        if config:
            self.config.update(config)

        n_samples, n_features = features.shape

        logger.info(
            "XGBoost修正器: 样本数=%d, 特征数=%d, 树数量=%d, 最大深度=%d",
            n_samples, n_features, self.n_estimators, self.max_depth,
        )

        # 初始化特征重要性
        self._feature_importance = np.zeros(n_features)
        assert self._feature_importance is not None

        # 初始化预测为均值
        predictions = np.full(n_samples, np.mean(targets))

        # 梯度提升训练
        for i in range(self.n_estimators):
            # 计算负梯度（残差）
            residuals = targets - predictions

            # 计算梯度（MSE损失的梯度: -2 * residual）
            gradients = -2.0 * residuals
            # 计算Hessian（MSE损失的Hessian: 2）
            hessians = np.full(n_samples, 2.0)

            # 子采样
            if self.subsample < 1.0:
                sample_size = int(n_samples * self.subsample)
                indices = np.random.choice(n_samples, sample_size, replace=False)
            else:
                indices = np.arange(n_samples)

            # 构建决策树拟合梯度
            tree = self._build_tree(
                features[indices],
                gradients[indices],
                hessians[indices],
                depth=0,
            )
            self._trees.append(tree)

            # 更新预测
            tree_preds = self._predict_tree(tree, features)
            predictions += self.learning_rate * tree_preds

            if (i + 1) % 20 == 0:
                loss = float(np.mean((predictions - targets) ** 2))
                logger.info("XGBoost训练轮次 %d, MSE损失: %.6f", i + 1, loss)

        # 计算修正值
        corrected_values = predictions

        # 残差统计
        final_residuals = targets - corrected_values
        residuals_stats = {
            "mean": float(np.mean(final_residuals)),
            "std": float(np.std(final_residuals)),
            "min": float(np.min(final_residuals)),
            "max": float(np.max(final_residuals)),
            "rmse": float(np.sqrt(np.mean(final_residuals ** 2))),
            "mae": float(np.mean(np.abs(final_residuals))),
        }

        # 归一化特征重要性
        total_importance = np.sum(self._feature_importance)
        if total_importance > 0:
            normalized_importance = self._feature_importance / total_importance
        else:
            normalized_importance = self._feature_importance.copy()

        return {
            "corrected_values": corrected_values.tolist(),
            "feature_importance": normalized_importance.tolist(),
            "residuals": residuals_stats,
            "n_samples": n_samples,
            "n_features": n_features,
            "n_trees": self.n_estimators,
        }

    def _build_tree(
        self,
        x: np.ndarray,
        gradients: np.ndarray,
        hessians: np.ndarray,
        depth: int,
    ) -> dict[str, Any]:
        """递归构建决策树.

        使用梯度统计量（类似XGBoost的近似分裂算法）进行节点分裂。

        Args:
            x: 特征矩阵
            gradients: 梯度值
            hessians: Hessian值
            depth: 当前深度

        Returns:
            决策树节点字典
        """
        assert self._feature_importance is not None
        n_samples = len(gradients)

        # 叶子节点条件
        if (
            depth >= self.max_depth
            or n_samples < self.min_samples_split
            or n_samples <= 1
        ):
            # 计算叶子最优值: -sum(G) / (sum(H) + lambda)
            leaf_value = -np.sum(gradients) / (np.sum(hessians) + self.reg_lambda)
            return {"leaf": True, "value": leaf_value}

        # 特征子采样
        n_features = x.shape[1]
        if self.max_features and self.max_features < n_features:
            feature_indices = np.random.choice(
                n_features, self.max_features, replace=False,
            )
        else:
            feature_indices = np.arange(n_features)

        # 寻找最优分裂
        best_gain = -np.inf
        best_feature = 0
        best_threshold = 0.0
        G_total = np.sum(gradients)
        H_total = np.sum(hessians)

        for fi in feature_indices:
            feature_values = x[:, fi]
            sorted_indices = np.argsort(feature_values)
            sorted_features = feature_values[sorted_indices]
            sorted_g = gradients[sorted_indices]
            sorted_h = hessians[sorted_indices]

            G_left = 0.0
            H_left = 0.0

            for j in range(n_samples - 1):
                G_left += sorted_g[j]
                H_left += sorted_h[j]
                G_right = G_total - G_left
                H_right = H_total - H_left

                # 避免在相同值处分裂
                if sorted_features[j] == sorted_features[j + 1]:
                    continue

                # 计算增益
                gain = (
                    (G_left ** 2) / (H_left + self.reg_lambda)
                    + (G_right ** 2) / (H_right + self.reg_lambda)
                    - (G_total ** 2) / (H_total + self.reg_lambda)
                )

                if gain > best_gain:
                    best_gain = gain
                    best_feature = fi
                    best_threshold = (sorted_features[j] + sorted_features[j + 1]) / 2.0

        # 如果没有有效分裂
        if best_gain <= 0 or best_gain == -np.inf:
            leaf_value = -G_total / (H_total + self.reg_lambda)
            return {"leaf": True, "value": leaf_value}

        # 更新特征重要性
        self._feature_importance[best_feature] += best_gain

        # 分裂数据
        left_mask = x[:, best_feature] <= best_threshold
        right_mask = ~left_mask

        return {
            "leaf": False,
            "feature": int(best_feature),
            "threshold": float(best_threshold),
            "gain": float(best_gain),
            "left": self._build_tree(
                x[left_mask], gradients[left_mask], hessians[left_mask], depth + 1,
            ),
            "right": self._build_tree(
                x[right_mask], gradients[right_mask], hessians[right_mask], depth + 1,
            ),
        }

    def _predict_tree(
        self,
        tree: dict[str, Any],
        x: np.ndarray,
    ) -> np.ndarray:
        """使用决策树进行预测.

        Args:
            tree: 决策树节点
            x: 特征矩阵

        Returns:
            预测值数组
        """
        predictions = np.zeros(x.shape[0])
        for i in range(x.shape[0]):
            node = tree
            while not node.get("leaf", False):
                if x[i, node["feature"]] <= node["threshold"]:
                    node = node["left"]
                else:
                    node = node["right"]
            predictions[i] = node["value"]
        return predictions
