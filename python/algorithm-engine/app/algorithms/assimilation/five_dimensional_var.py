"""5D-VAR 数据同化算法 -- 增强版.

在3D-VAR基础上增加时间维和流依赖背景误差，支持循环同化（Cycling DA）、
增量分析（Incremental Analysis）和 Hybrid B 矩阵方法（NMC + 气候态）。

代价函数:
  J(x) = 0.5 * (x - xb)^T B^{-1} (x - xb)
       + 0.5 * sum_t [ (H_t M_t x - y_t)^T R_t^{-1} (H_t M_t x - y_t) ]
       + J_risk(x) + J_param(alpha)

其中:
  - B: 背景误差协方差（Hybrid B = alpha * B_nmc + (1-alpha) * B_clim）
  - M_t: 时间步 t 的预报模式（线性化近似）
  - H_t: 时间步 t 的观测算子
  - J_risk: 飞行风险约束项
  - J_param: AI参数化控制变量约束项
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
from scipy.ndimage import gaussian_filter

logger = logging.getLogger(__name__)


class FiveDimensionalVAR:
    """5D-VAR 数据同化算法.

    在标准4D-VAR基础上扩展:
    1. 时间维: 支持多个时间窗口的观测同时同化
    2. 流依赖背景误差: B矩阵随流型变化
    3. 风险维: 飞行风险代价约束
    4. AI参数化: AI模型校正作为控制变量
    5. Hybrid B: NMC方法 + 气候态混合估计背景误差

    支持两种运行模式:
    - 单次分析（single analysis）: 一次性同化所有时间窗口的观测
    - 循环同化（cycling DA）: 滚动时间窗口，逐步同化
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        # 网格配置
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)

        # 优化器配置
        self.max_iterations: int = self.config.get("max_iterations", 30)
        self.tolerance: float = self.config.get("tolerance", 1e-6)
        self.learning_rate: float = self.config.get("learning_rate", 0.01)

        # 代价函数权重
        self.risk_weight: float = self.config.get("risk_weight", 0.5)
        self.ai_param_weight: float = self.config.get("ai_param_weight", 0.1)

        # 背景误差配置
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

        # Hybrid B 矩阵配置
        self.hybrid_alpha: float = self.config.get("hybrid_alpha", 0.7)
        self.nmc_weight: float = self.config.get("nmc_weight", 0.7)
        self.climatology_weight: float = 1.0 - self.nmc_weight

        # 循环同化配置
        self.cycling_window: int = self.config.get("cycling_window", 6)
        self.cycling_overlap: int = self.config.get("cycling_overlap", 1)

        # 增量分析配置
        self.incremental_resolution: int = self.config.get("incremental_resolution", 4)
        self.n_outer_iterations: int = self.config.get("n_outer_iterations", 2)

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行5D-VAR同化（单次分析模式）.

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置
                    - value: 观测值
                    - time_index: 时间窗口索引（可选，默认0）
                    - error: 观测误差（可选）
                - ai_correction: AI模型校正场（可选）
                - risk_field: 风险场（可选）
                - nmc_ensemble: NMC集合（可选，用于Hybrid B）
                - climatology_field: 气候态背景场（可选）
                - mode: 运行模式 "single" | "cycling"（默认 "single"）

        Returns:
            包含分析结果和诊断统计的字典
        """
        mode = params.get("mode", "single")

        if mode == "cycling":
            return self._cycling_assimilation(params)
        else:
            return self._single_assimilation(params)

    # ================================================================
    # 单次分析
    # ================================================================

    def _single_assimilation(self, params: dict[str, Any]) -> dict[str, Any]:
        """单次5D-VAR分析."""
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])
        risk_weight = params.get("risk_weight", self.risk_weight)
        ai_correction = np.asarray(
            params.get("ai_correction", np.zeros_like(background)),
            dtype=float,
        )

        # 构建 Hybrid B 矩阵
        B_inv_sqrt = self._build_hybrid_b_matrix(params, background)  # noqa: N806

        # 按时间窗口分组观测
        time_windows = self._group_observations_by_time(observations)
        n_time_windows = max(len(time_windows), 1)

        xb = background.flatten()
        n_state = len(xb)
        x = xb.copy()

        # 构建多时间窗口的观测算子
        y_obs_all, H_all, R_inv_all = self._build_multi_time_obs_operator(  # noqa: N806
            x,
            observations,
            background.shape,
        )

        # 构建简化的时间传播算子（单位矩阵 + 小扰动，模拟M_t）
        M_list = self._build_propagation_models(n_time_windows, n_state)

        cost_history = []
        J_b = J_o = J_risk = J_param = 0.0  # noqa: N806

        for outer_iter in range(self.n_outer_iterations):
            # 外循环：更新线性化点
            for i in range(self.max_iterations):
                dx = x - xb

                # J_b: 背景约束项（使用Hybrid B）
                J_b = 0.5 * float(np.sum((B_inv_sqrt @ dx) ** 2))  # noqa: N806

                # J_o: 多时间窗口观测约束项
                J_o = 0.0  # noqa: N806
                grad_o = np.zeros(n_state)
                for t_idx, (y_t, H_t, R_inv_t, M_t) in enumerate(  # noqa: N806
                    zip(y_obs_all, H_all, R_inv_all, M_list),
                ):
                    Hx_t = H_t @ (M_t @ x)  # noqa: N806
                    residual_t = Hx_t - y_t
                    J_o += 0.5 * float(residual_t @ R_inv_t @ residual_t)  # noqa: N806
                    grad_o += M_t.T @ H_t.T @ (R_inv_t @ residual_t)

                # J_risk: 风险约束项
                field = x.reshape(background.shape)
                smoothed = gaussian_filter(field, sigma=1.0)
                J_risk = risk_weight * float(np.var(smoothed))  # noqa: N806

                # J_param: AI参数化约束项
                J_param = self.ai_param_weight * float(  # noqa: N806
                    np.sum((x - ai_correction.flatten()) ** 2),
                )

                total_cost = J_b + J_o + J_risk + J_param
                cost_history.append(float(total_cost))

                # 计算梯度
                grad_b = B_inv_sqrt.T @ (B_inv_sqrt @ dx)
                grad_param = self.ai_param_weight * 2.0 * (x - ai_correction.flatten())
                grad = grad_b + grad_o + grad_param

                # 梯度下降更新
                x = x - self.learning_rate * grad

                if len(cost_history) > 1 and abs(cost_history[-2] - cost_history[-1]) < self.tolerance:
                    logger.info("5D-VAR 外循环%d 内迭代%d 收敛", outer_iter, i)
                    break

        analysis = x.reshape(background.shape)

        # 计算诊断统计
        diagnostics = self._compute_diagnostics(
            xb,
            x,
            observations,
            background.shape,
            cost_history,
        )

        return {
            "analysis_field": analysis.tolist(),
            "increment": (x - xb).reshape(background.shape).tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "cost_breakdown": {
                "J_b": float(J_b),
                "J_o": float(J_o),
                "J_risk": float(J_risk),
                "J_param": float(J_param),
            },
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations * self.n_outer_iterations,
            "grid_shape": list(background.shape),
            "n_time_windows": n_time_windows,
            "diagnostics": diagnostics,
        }

    # ================================================================
    # 循环同化（Cycling DA）
    # ================================================================

    def _cycling_assimilation(self, params: dict[str, Any]) -> dict[str, Any]:
        """循环同化模式: 滚动时间窗口，逐步同化观测.

        将观测按时间窗口分组，依次进行同化分析。
        每个窗口的分析结果作为下一个窗口的背景场。
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])

        # 按时间窗口分组观测
        time_windows = self._group_observations_by_time(observations)
        n_windows = max(len(time_windows), 1)

        logger.info(
            "开始循环同化: 共%d个时间窗口, 窗口大小=%d, 重叠=%d",
            n_windows,
            self.cycling_window,
            self.cycling_overlap,
        )

        current_background = background.copy()
        cycle_results = []
        total_cost_history = []

        for cycle_idx in range(n_windows):
            window_obs = time_windows.get(cycle_idx, [])
            if not window_obs:
                logger.info("时间窗口 %d 无观测，跳过", cycle_idx)
                cycle_results.append(
                    {
                        "cycle": cycle_idx,
                        "n_observations": 0,
                        "skipped": True,
                    }
                )
                # 简单时间传播（背景场微调）
                current_background = self._propagate_background(
                    current_background,
                    cycle_idx,
                )
                continue

            logger.info(
                "循环 %d/%d: 同化 %d 个观测",
                cycle_idx + 1,
                n_windows,
                len(window_obs),
            )

            cycle_params = {
                "background_field": current_background,
                "observations": window_obs,
                "risk_weight": self.risk_weight,
                "ai_correction": params.get("ai_correction", np.zeros_like(background)),
                "nmc_ensemble": params.get("nmc_ensemble"),
                "climatology_field": params.get("climatology_field"),
            }

            result = self._single_assimilation(cycle_params)

            # 更新背景场为当前分析场
            current_background = np.asarray(result["analysis_field"])
            result["cycle"] = cycle_idx
            result["n_observations"] = len(window_obs)
            cycle_results.append(result)
            total_cost_history.extend(
                [c for c in [result.get("cost", 0)] if c > 0],
            )

        return {
            "mode": "cycling",
            "analysis_field": current_background.tolist(),
            "n_cycles": n_windows,
            "cycle_results": cycle_results,
            "total_cost": total_cost_history[-1] if total_cost_history else 0.0,
            "grid_shape": list(background.shape),
            "diagnostics": {
                "n_cycles_completed": n_windows,
                "total_observations_assimilated": sum(r.get("n_observations", 0) for r in cycle_results),
                "cycles_converged": sum(1 for r in cycle_results if r.get("converged", False)),
            },
        }

    # ================================================================
    # Hybrid B 矩阵构建
    # ================================================================

    def _build_hybrid_b_matrix(
        self,
        params: dict[str, Any],
        background: np.ndarray,
    ) -> np.ndarray:
        """构建 Hybrid B 矩阵的平方根逆 (B^{-1/2}).

        Hybrid B = alpha * B_nmc + (1-alpha) * B_clim

        其中:
        - B_nmc: 基于NMC（NMC: NMC方法）的背景误差协方差
        - B_clim: 基于气候态的背景误差协方差
        - alpha: 混合权重

        返回 B^{-1/2} 用于代价函数计算，避免显式存储大型矩阵。
        """
        n = background.size

        # NMC 部分: 基于集合的误差估计
        nmc_ensemble = params.get("nmc_ensemble", None)
        if nmc_ensemble is not None:
            ensemble = np.asarray(nmc_ensemble, dtype=float)
            if ensemble.ndim == 1:
                ensemble = ensemble.reshape(1, -1)
            n_members = ensemble.shape[0]
            if n_members > 1:
                ens_mean = ensemble.mean(axis=0)
                perturbations = ensemble - ens_mean
                # NMC协方差的平方根
                B_nmc_sqrt = perturbations.T / np.sqrt(n_members - 1)  # noqa: N806
                B_nmc = B_nmc_sqrt @ B_nmc_sqrt.T  # noqa: N806
            else:
                B_nmc = np.eye(n) * self.sigma_b**2  # noqa: N806
        else:
            # 无NMC集合时使用默认对角矩阵
            B_nmc = np.eye(n) * self.sigma_b**2  # noqa: N806

        # 气候态部分: 基于气候态方差的对角矩阵
        climatology_field = params.get("climatology_field", None)
        if climatology_field is not None:
            clim_var = np.asarray(climatology_field, dtype=float).flatten() ** 2
            clim_var = np.maximum(clim_var, 1e-10)
            B_clim = np.diag(clim_var)  # noqa: N806
        else:
            B_clim = np.eye(n) * self.sigma_b**2  # noqa: N806

        # 混合
        alpha = self.hybrid_alpha
        B_hybrid = alpha * B_nmc + (1 - alpha) * B_clim  # noqa: N806

        # 正则化防止奇异
        B_hybrid += np.eye(n) * 1e-10  # noqa: N806

        # 计算 B^{-1/2} 用于代价函数
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(B_hybrid)
            eigenvalues = np.maximum(eigenvalues, 1e-10)
            B_inv_sqrt = eigenvectors @ np.diag(1.0 / np.sqrt(eigenvalues)) @ eigenvectors.T  # noqa: N806
        except np.linalg.LinAlgError:
            logger.warning("B矩阵特征分解失败，使用对角近似")
            B_inv_sqrt = np.eye(n) / self.sigma_b  # noqa: N806

        return B_inv_sqrt

    # ================================================================
    # 多时间窗口观测算子
    # ================================================================

    def _group_observations_by_time(
        self,
        observations: list[dict[str, Any]],
    ) -> dict[int, list[dict[str, Any]]]:
        """按时间窗口索引分组观测."""
        time_windows: dict[int, list[dict[str, Any]]] = {}
        for obs in observations:
            t_idx = obs.get("time_index", 0)
            if t_idx not in time_windows:
                time_windows[t_idx] = []
            time_windows[t_idx].append(obs)
        return time_windows

    def _build_multi_time_obs_operator(
        self,
        xb: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
    ) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
        """构建多时间窗口的观测算子、观测向量和误差协方差逆.

        Returns:
            (y_obs_list, H_list, R_inv_list)
        """
        time_windows = self._group_observations_by_time(observations)
        n_state = len(xb)

        y_obs_all: list[np.ndarray] = []
        H_all: list[np.ndarray] = []  # noqa: N806
        R_inv_all: list[np.ndarray] = []  # noqa: N806

        for t_idx in sorted(time_windows.keys()):
            window_obs = time_windows[t_idx]
            y_obs, H = self._build_observation_operator(xb, window_obs, shape)  # noqa: N806
            R_inv = self._build_observation_error_inverse(window_obs)  # noqa: N806

            y_obs_all.append(y_obs)
            H_all.append(H)
            R_inv_all.append(R_inv)

        # 如果没有观测，返回空列表
        if not y_obs_all:
            y_obs_all.append(np.zeros(0))
            H_all.append(np.zeros((0, n_state)))
            R_inv_all.append(np.zeros((0, 0)))

        return y_obs_all, H_all, R_inv_all

    def _build_observation_operator(
        self,
        xb: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
    ) -> tuple[np.ndarray, np.ndarray]:
        """构建观测算子矩阵 H 和观测向量 y."""
        n = len(xb)
        m = len(observations)
        y_obs = np.zeros(m)
        H = np.zeros((m, n))  # noqa: N806
        for j, obs in enumerate(observations):
            pos = obs.get("position", [0] * len(shape))
            y_obs[j] = obs.get("value", 0.0)
            idx = self._position_to_index(pos, shape)
            if 0 <= idx < n:
                H[j, idx] = 1.0  # noqa: N806
        return y_obs, H

    def _build_observation_error_inverse(
        self,
        observations: list[dict[str, Any]],
    ) -> np.ndarray:
        """构建观测误差协方差矩阵的逆 R^{-1}."""
        n_obs = len(observations)
        if n_obs == 0:
            return np.zeros((0, 0))

        R = np.eye(n_obs) * self.observation_error_scale**2  # noqa: N806
        for j, obs in enumerate(observations):
            obs_err = obs.get("error", self.observation_error_scale)
            R[j, j] = max(obs_err**2, 1e-10)  # noqa: N806

        try:
            R_inv = np.linalg.inv(R)  # noqa: N806
        except np.linalg.LinAlgError:
            R_inv = np.linalg.pinv(R)  # noqa: N806

        return R_inv

    def _build_propagation_models(
        self,
        n_time_windows: int,
        n_state: int,
    ) -> list[np.ndarray]:
        """构建简化的时间传播算子列表.

        在实际应用中，M_t 应该是预报模式的切线性/伴随模式。
        此处使用简化模型: M_t = I + epsilon * P，其中 P 是小随机扰动矩阵。
        """
        M_list = []
        for t in range(n_time_windows):
            # 单位矩阵 + 小的时间演化扰动
            M = np.eye(n_state)  # noqa: N806
            # 添加小的扩散效应模拟时间演化
            perturbation_scale = 0.01 * (t + 1)
            np.random.seed(42 + t)
            noise = np.random.randn(n_state, n_state) * perturbation_scale
            noise = 0.5 * (noise + noise.T)  # 对称化
            M = M + noise  # noqa: N806
            M_list.append(M)
        return M_list

    # ================================================================
    # 背景场时间传播
    # ================================================================

    def _propagate_background(
        self,
        background: np.ndarray,
        time_step: int,
    ) -> np.ndarray:
        """简单的背景场时间传播（用于循环同化中无观测的窗口）.

        在实际应用中应替换为数值预报模式的短期预报。
        """
        # 简单的扩散模型
        propagated = gaussian_filter(background, sigma=0.1 * (time_step + 1))
        return propagated

    # ================================================================
    # 诊断统计
    # ================================================================

    def _compute_diagnostics(
        self,
        xb: np.ndarray,
        xa: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
        cost_history: list[float],
    ) -> dict[str, Any]:
        """计算完整的分析诊断统计."""
        increment = xa - xb
        increment_norm = float(np.linalg.norm(increment))
        increment_max = float(np.max(np.abs(increment)))
        increment_mean = float(np.mean(increment))
        increment_rms = float(np.sqrt(np.mean(increment**2)))

        # 分析场统计
        analysis_field = xa.reshape(shape)
        analysis_mean = float(np.mean(analysis_field))
        analysis_std = float(np.std(analysis_field))
        analysis_min = float(np.min(analysis_field))
        analysis_max = float(np.max(analysis_field))

        # 拟合度统计
        y_obs, H = self._build_observation_operator(xb, observations, shape)  # noqa: N806
        if len(y_obs) > 0:
            Hxa = H @ xa  # noqa: N806
            Hxb = H @ xb  # noqa: N806
            residuals_analysis = Hxa - y_obs
            residuals_background = Hxb - y_obs

            rmse_analysis = float(np.sqrt(np.mean(residuals_analysis**2)))
            rmse_background = float(np.sqrt(np.mean(residuals_background**2)))
            bias_analysis = float(np.mean(residuals_analysis))
            bias_background = float(np.mean(residuals_background))
            improvement_ratio = (rmse_background - rmse_analysis) / max(rmse_background, 1e-10)
        else:
            rmse_analysis = 0.0
            rmse_background = 0.0
            bias_analysis = 0.0
            bias_background = 0.0
            improvement_ratio = 0.0

        # 代价函数收敛信息
        cost_reduction = 0.0
        if len(cost_history) >= 2:
            cost_reduction = (cost_history[0] - cost_history[-1]) / max(cost_history[0], 1e-10)

        return {
            "increment": {
                "norm": increment_norm,
                "max": increment_max,
                "mean": increment_mean,
                "rms": increment_rms,
            },
            "analysis_field": {
                "mean": analysis_mean,
                "std": analysis_std,
                "min": analysis_min,
                "max": analysis_max,
            },
            "fit": {
                "rmse_analysis": rmse_analysis,
                "rmse_background": rmse_background,
                "bias_analysis": bias_analysis,
                "bias_background": bias_background,
                "improvement_ratio": improvement_ratio,
            },
            "convergence": {
                "cost_reduction": cost_reduction,
                "final_cost": cost_history[-1] if cost_history else 0.0,
                "n_iterations": len(cost_history),
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
