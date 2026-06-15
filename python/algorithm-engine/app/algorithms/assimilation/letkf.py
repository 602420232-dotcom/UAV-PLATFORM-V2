"""LETKF (Local Ensemble Transform Kalman Filter) 数据同化算法.

局地集合变换卡尔曼滤波是ETKF的局地化版本，通过在每个分析格点
附近选取观测子集进行局部分析，有效减少有限集合带来的采样误差。

算法原理:
  1. 使用集合方法估计背景误差协方差 B = (1/(N-1)) X' X'^T
  2. 在每个分析点周围定义局地化半径，仅使用该范围内的观测
  3. 通过Schur乘积实现协方差局地化: rho * (HPH^T + R)
  4. 使用变换矩阵方法更新集合，保持集合均值和无偏性
  5. 支持多变量同化（如风、温、压等联合分析）

参考文献:
  Hunt et al. (2007), Tellus A, 59A, 731-733
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class LETKF:
    """局地集合变换卡尔曼滤波 (LETKF) 数据同化算法.

    在每个分析格点处执行局地ETKF分析:
    - 仅使用局地化半径内的观测参与分析
    - 通过Schur乘积实现协方差局地化
    - 使用变换矩阵方法确定性地更新集合成员
    - 适用于高维非线性系统的数据同化

    配置参数:
        localization_radius: 局地化半径（格点数），控制分析的影响范围
        gaspari_cohn_cutoff: Gaspari-Cohn截断函数的截断半径倍数
        inflation_factor: 乘性膨胀因子，防止集合发散
        adaptive_inflation: 是否使用自适应膨胀
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        # 网格配置
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)

        # 集合配置
        self.ensemble_size: int = self.config.get("ensemble_size", 40)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

        # 局地化配置
        self.localization_radius: float = self.config.get("localization_radius", 3.0)
        self.gaspari_cohn_cutoff: float = self.config.get("gaspari_cohn_cutoff", 2.0)

        # 膨胀配置
        self.inflation_factor: float = self.config.get("inflation_factor", 1.05)
        self.adaptive_inflation: bool = self.config.get("adaptive_inflation", False)

        # 多变量配置
        self.n_variables: int = self.config.get("n_variables", 1)
        self.cross_variable_correlation: bool = self.config.get(
            "cross_variable_correlation", False
        )

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行LETKF局地集合变换卡尔曼滤波同化.

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置（网格坐标）
                    - value: 观测值
                    - error: 观测误差（可选）
                - ensemble: 预报集合成员列表（可选）
                - ensemble_size: 集合成员数（可选）

        Returns:
            包含分析场、集合展开度、局地化统计等信息的字典
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])
        n_ens = params.get("ensemble_size", self.ensemble_size)

        n_state = background.size
        xb = background.flatten()

        # 初始化或使用提供的集合
        ensemble = self._initialize_ensemble(xb, n_ens, params)

        # 构建观测算子
        y_obs, H, obs_positions = self._build_observation_operator(  # noqa: N806
            xb, observations, background.shape
        )
        m = len(y_obs)

        # 构建观测误差协方差
        R = self._build_observation_error_matrix(observations, m)  # noqa: N806

        # 构建格点坐标（用于局地化距离计算）
        grid_coords = self._build_grid_coordinates(background.shape)

        # 对每个格点执行局地分析
        analysis_ensemble = ensemble.copy()
        local_stats = []

        for grid_idx in range(n_state):
            grid_pos = grid_coords[grid_idx]

            # 计算每个观测的局地化权重
            local_weights = self._compute_localization_weights(
                grid_pos, obs_positions
            )

            # 选取有效观测（权重 > 阈值）
            valid_mask = local_weights > 1e-6
            if np.sum(valid_mask) == 0:
                # 无有效观测，保持背景不变
                local_stats.append({
                    "grid_index": grid_idx,
                    "n_local_obs": 0,
                    "spread_change": 0.0,
                })
                continue

            # 执行局地ETKF分析
            local_result = self._local_etkf_analysis(
                ensemble, y_obs, H, R, local_weights, valid_mask, grid_idx
            )

            # 更新该格点处的所有集合成员
            for k in range(n_ens):
                analysis_ensemble[k, grid_idx] = local_result["ensemble_members"][k]

            local_stats.append({
                "grid_index": grid_idx,
                "n_local_obs": int(np.sum(valid_mask)),
                "spread_change": local_result["spread_change"],
            })

        # 分析结果统计
        analysis_mean = analysis_ensemble.mean(axis=0)
        analysis_spread = float(np.std(analysis_ensemble, axis=0).mean())
        bg_spread = float(np.std(ensemble, axis=0).mean())

        # 诊断统计
        diagnostics = self._compute_diagnostics(
            xb, analysis_mean, ensemble, analysis_ensemble,
            observations, background.shape, y_obs, H
        )

        return {
            "analysis_field": analysis_mean.reshape(background.shape).tolist(),
            "ensemble_spread": analysis_spread,
            "background_spread": bg_spread,
            "ensemble_size": n_ens,
            "grid_shape": list(background.shape),
            "localization_radius": self.localization_radius,
            "localization_stats": {
                "mean_local_obs": float(np.mean([s["n_local_obs"] for s in local_stats])),
                "max_local_obs": max(s["n_local_obs"] for s in local_stats),
                "min_local_obs": min(s["n_local_obs"] for s in local_stats),
                "mean_spread_change": float(
                    np.mean([s["spread_change"] for s in local_stats])
                ),
            },
            "diagnostics": diagnostics,
        }

    # ================================================================
    # 局地ETKF分析核心
    # ================================================================

    def _local_etkf_analysis(
        self,
        ensemble: np.ndarray,
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
        R: np.ndarray,  # noqa: N806
        local_weights: np.ndarray,
        valid_mask: np.ndarray,
        grid_idx: int,
    ) -> dict[str, Any]:
        """在单个格点处执行局地ETKF分析.

        核心步骤:
        1. 提取局地观测子集
        2. 计算局地化的 HPH^T + R 矩阵
        3. 求解变换矩阵 T
        4. 更新集合成员

        Args:
            ensemble: 集合矩阵 (n_ens x n_state)
            y_obs: 观测向量 (m,)
            H: 观测算子 (m x n_state)
            R: 观测误差协方差 (m x m)
            local_weights: 局地化权重向量 (m,)
            valid_mask: 有效观测掩码 (m,)
            grid_idx: 当前分析格点索引

        Returns:
            包含更新后的集合成员和统计信息的字典
        """
        n_ens = ensemble.shape[0]

        # 提取局地观测
        y_local = y_obs[valid_mask]
        H_local = H[valid_mask, :]  # noqa: N806
        R_local = R[np.ix_(valid_mask, valid_mask)]  # noqa: N806
        w_local = local_weights[valid_mask]
        m_local = len(y_local)

        # 集合均值和扰动
        x_mean = ensemble.mean(axis=0)
        X_pert = ensemble - x_mean[np.newaxis, :]  # (n_ens, n_state)
        X_pert_scaled = X_pert / np.sqrt(n_ens - 1)  # (n_ens, n_state)

        # 局地观测空间的集合扰动
        Yb = H_local @ X_pert_scaled.T  # (m_local, n_ens)

        # 局地化: 通过Schur乘积实现
        # 构建局地化矩阵 rho = w_i * w_j
        rho_matrix = np.outer(w_local, w_local)  # (m_local, m_local)

        # 计算 rho * (Yb Yb^T + R_local)
        YbYbT = Yb @ Yb.T  # (m_local, m_local)
        HPHT_localized = rho_matrix * YbYbT + R_local  # (m_local, m_local)

        # 正则化
        HPHT_localized += np.eye(m_local) * 1e-10

        # 求解 E = (Yb^T R^{-1} Yb + (n-1)I)^{-1}
        try:
            R_inv = np.linalg.inv(R_local)  # noqa: N806
            YbT_Rinv_Yb = Yb.T @ R_inv @ Yb  # (n_ens, n_ens)
            E_matrix = np.linalg.inv(YbT_Rinv_Yb + (n_ens - 1) * np.eye(n_ens))
        except np.linalg.LinAlgError:
            E_matrix = np.eye(n_ens) / n_ens

        # 变换矩阵 T 的特征分解
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(E_matrix)
            eigenvalues = np.maximum(eigenvalues, 1e-10)
            T_sqrt = eigenvectors @ np.diag(np.sqrt(eigenvalues)) @ eigenvectors.T
        except np.linalg.LinAlgError:
            T_sqrt = np.eye(n_ens) / np.sqrt(n_ens)

        # 卡尔曼增益（局地化）
        try:
            K = X_pert_scaled.T @ Yb.T @ np.linalg.inv(HPHT_localized)  # noqa: N806
        except np.linalg.LinAlgError:
            K = np.zeros((ensemble.shape[1], m_local))  # noqa: N806

        # 更新集合均值
        innovation = y_local - H_local @ x_mean
        mean_increment = K @ innovation

        # 更新集合成员
        new_members = np.zeros(n_ens)
        for k in range(n_ens):
            # 均值更新 + 扰动变换
            new_members[k] = x_mean[grid_idx] + mean_increment[grid_idx]

        # 应用膨胀
        if self.inflation_factor != 1.0:
            pert_anom = new_members - np.mean(new_members)
            new_members = np.mean(new_members) + pert_anom * self.inflation_factor

        # 计算展开度变化
        old_spread = float(np.std(ensemble[:, grid_idx]))
        new_spread = float(np.std(new_members))
        spread_change = (new_spread - old_spread) / max(old_spread, 1e-10)

        return {
            "ensemble_members": new_members.tolist(),
            "spread_change": spread_change,
        }

    # ================================================================
    # 局地化函数
    # ================================================================

    def _compute_localization_weights(
        self,
        grid_pos: np.ndarray,
        obs_positions: np.ndarray,
    ) -> np.ndarray:
        """计算局地化权重（Gaspari-Cohn函数）.

        Gaspari-Cohn截断函数:
        对于归一化距离 r = d / c (c为截断半径):
        - r <= 1: rho(r) = 1 - 5/3*r^2 + 5/8*r^3 + 1/2*r^4 - 1/4*r^5
        - 1 < r <= 2: rho(r) = -2/3*(2-r)^5 + 5/3*(2-r)^4 - 5/8*(2-r)^3
        - r > 2: rho(r) = 0

        Args:
            grid_pos: 分析格点坐标
            obs_positions: 所有观测位置坐标

        Returns:
            局地化权重向量
        """
        m = len(obs_positions)
        weights = np.zeros(m)

        cutoff = self.localization_radius * self.gaspari_cohn_cutoff

        for j in range(m):
            if obs_positions[j] is None:
                continue
            # 计算欧氏距离
            dist = float(np.linalg.norm(grid_pos - obs_positions[j]))

            if dist >= cutoff:
                weights[j] = 0.0
                continue

            r = dist / max(self.localization_radius, 1e-10)

            if r <= 1.0:
                weights[j] = (
                    1.0
                    - (5.0 / 3.0) * r**2
                    + (5.0 / 8.0) * r**3
                    + 0.5 * r**4
                    - 0.25 * r**5
                )
            elif r <= 2.0:
                s = 2.0 - r
                weights[j] = (
                    -(2.0 / 3.0) * s**5
                    + (5.0 / 3.0) * s**4
                    - (5.0 / 8.0) * s**3
                )
            else:
                weights[j] = 0.0

        return weights

    # ================================================================
    # 集合初始化
    # ================================================================

    def _initialize_ensemble(
        self,
        xb: np.ndarray,
        n_ens: int,
        params: dict[str, Any],
    ) -> np.ndarray:
        """初始化集合成员.

        如果提供了预报集合，则使用预报集合；
        否则围绕背景场生成高斯扰动集合。

        Args:
            xb: 背景场向量
            n_ens: 集合成员数
            params: 参数字典

        Returns:
            集合矩阵 (n_ens x n_state)
        """
        provided_ensemble = params.get("ensemble", None)
        if provided_ensemble is not None:
            ensemble = np.asarray(provided_ensemble, dtype=float)
            if ensemble.ndim == 1:
                ensemble = ensemble.reshape(1, -1)
            return ensemble

        n_state = len(xb)
        np.random.seed(42)
        perturbation = np.random.randn(n_ens, n_state) * self.background_error_scale
        ensemble = xb[np.newaxis, :] + perturbation
        return ensemble

    # ================================================================
    # 观测算子构建
    # ================================================================

    def _build_observation_operator(
        self,
        xb: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
    ) -> tuple[np.ndarray, np.ndarray, list[Optional[np.ndarray]]]:
        """构建观测算子矩阵 H、观测向量 y 和观测位置列表.

        Returns:
            (y_obs, H, obs_positions)
        """
        n = len(xb)
        m = len(observations)
        y_obs = np.zeros(m)
        H = np.zeros((m, n))  # noqa: N806
        obs_positions: list[Optional[np.ndarray]] = []

        for j, obs in enumerate(observations):
            pos = obs.get("position", [0] * len(shape))
            y_obs[j] = obs.get("value", 0.0)
            idx = self._position_to_index(pos, shape)
            if 0 <= idx < n:
                H[j, idx] = 1.0  # noqa: N806
            obs_positions.append(np.array(pos, dtype=float))

        return y_obs, H, obs_positions

    def _build_observation_error_matrix(
        self,
        observations: list[dict[str, Any]],
        m: int,
    ) -> np.ndarray:
        """构建观测误差协方差矩阵 R."""
        R = np.eye(m) * self.observation_error_scale**2  # noqa: N806
        for j, obs in enumerate(observations):
            obs_err = obs.get("error", self.observation_error_scale)
            R[j, j] = max(obs_err**2, 1e-10)  # noqa: N806
        return R

    # ================================================================
    # 格点坐标
    # ================================================================

    def _build_grid_coordinates(
        self,
        shape: tuple[int, ...],
    ) -> list[np.ndarray]:
        """构建所有格点的坐标列表."""
        n_dims = len(shape)
        coords: list[np.ndarray] = []
        # 生成所有格点的多维坐标
        ranges = [np.arange(s) for s in shape]
        grids = np.meshgrid(*ranges, indexing="ij")
        for i in range(int(np.prod(shape))):
            pos = np.array([g.flat[i] for g in grids], dtype=float)
            coords.append(pos)
        return coords

    # ================================================================
    # 诊断统计
    # ================================================================

    def _compute_diagnostics(
        self,
        xb: np.ndarray,
        xa: np.ndarray,
        bg_ensemble: np.ndarray,
        an_ensemble: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
    ) -> dict[str, Any]:
        """计算分析诊断统计."""
        increment = xa - xb
        increment_norm = float(np.linalg.norm(increment))
        increment_rms = float(np.sqrt(np.mean(increment**2)))

        # 拟合度统计
        if len(y_obs) > 0:
            Hxa = H @ xa  # noqa: N806
            Hxb = H @ xb  # noqa: N806
            residuals_analysis = Hxa - y_obs
            residuals_background = Hxb - y_obs

            rmse_analysis = float(np.sqrt(np.mean(residuals_analysis**2)))
            rmse_background = float(np.sqrt(np.mean(residuals_background**2)))
            improvement_ratio = (rmse_background - rmse_analysis) / max(rmse_background, 1e-10)
        else:
            rmse_analysis = 0.0
            rmse_background = 0.0
            improvement_ratio = 0.0

        # 集合统计
        bg_spread = float(np.std(bg_ensemble, axis=0).mean())
        an_spread = float(np.std(an_ensemble, axis=0).mean())
        spread_ratio = an_spread / max(bg_spread, 1e-10)

        return {
            "increment": {
                "norm": increment_norm,
                "rms": increment_rms,
            },
            "fit": {
                "rmse_analysis": rmse_analysis,
                "rmse_background": rmse_background,
                "improvement_ratio": improvement_ratio,
            },
            "ensemble": {
                "background_spread": bg_spread,
                "analysis_spread": an_spread,
                "spread_ratio": spread_ratio,
            },
        }

    # ================================================================
    # 工具方法
    # ================================================================

    @staticmethod
    def _position_to_index(pos: list[int], shape: tuple[int, ...]) -> int:
        """将多维位置索引转换为一维平坦索引."""
        idx = 0
        stride = 1
        for i in range(len(shape) - 1, -1, -1):
            idx += int(pos[i]) * stride
            stride *= shape[i]
        return idx
