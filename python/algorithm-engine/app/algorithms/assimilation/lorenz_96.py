"""Lorenz-96 模型数据同化算法.

Lorenz-96 是一个经典的混沌动力学模型，广泛用于数据同化
算法的测试和验证。该模型模拟沿纬圈一维排列的"大气变量"。

模型方程:
  dx_i/dt = (x_{i+1} - x_{i-2}) * x_{i-1} - x_i + F

  其中:
    - i = 1, ..., N (周期边界条件)
    - F: 外部强迫参数（控制混沌程度）
    - N: 系统维度

  当 F >= 8 时系统表现出混沌行为。

参考文献:
  Lorenz (1996), Proc. Seminar on Predictability, ECMWF, 297-324
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class Lorenz96Assimilation:
    """Lorenz-96 模型数据同化算法.

    特点:
    1. 使用 Lorenz-96 混沌模型作为预报模式
    2. 支持不同系统参数（N, F）
    3. 支持多种同化方法（EnKF, 3D-VAR, 4D-VAR）
    4. 内置真实状态生成和观测模拟
    5. 用于同化算法验证和性能评估

    配置参数:
        n_variables: Lorenz-96 系统维度 N
        forcing: 外部强迫参数 F
        dt: 时间步长
        assimilation_method: 同化方法
        obs_frequency: 观测频率（每隔多少步同化一次）
        obs_error: 观测误差标准差
        obs_density: 观测密度（0-1，1表示所有变量都被观测）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        # Lorenz-96 模型参数
        self.n_variables: int = self.config.get("n_variables", 40)
        self.forcing: float = self.config.get("forcing", 8.0)
        self.dt: float = self.config.get("dt", 0.05)

        # 同化配置
        self.assimilation_method: str = self.config.get("assimilation_method", "enkf")
        self.obs_frequency: int = self.config.get("obs_frequency", 4)
        self.obs_error: float = self.config.get("obs_error", 0.5)
        self.obs_density: float = self.config.get("obs_density", 0.8)

        # 集合配置
        self.ensemble_size: int = self.config.get("ensemble_size", 20)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)

        # 运行配置
        self.n_spinup_steps: int = self.config.get("n_spinup_steps", 1000)
        self.n_assimilation_cycles: int = self.config.get("n_assimilation_cycles", 100)
        self.n_forecast_steps: int = self.config.get("n_forecast_steps", 4)

        # 随机种子
        self.seed: int = self.config.get("seed", 42)

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行Lorenz-96模型数据同化实验.

        完整的实验流程:
        1. 初始化真实状态并spin-up
        2. 生成观测序列
        3. 执行循环同化
        4. 统计分析结果

        Args:
            params: 分析参数字典，包含:
                - n_variables: 系统维度（可选）
                - forcing: 外部强迫（可选）
                - assimilation_method: 同化方法（可选）
                - n_assimilation_cycles: 同化循环数（可选）
                - true_state: 真实状态（可选，用于双精度实验）

        Returns:
            包含分析结果、误差统计、时间序列等的字典
        """
        # 更新配置
        self.n_variables = params.get("n_variables", self.n_variables)
        self.forcing = params.get("forcing", self.forcing)
        self.assimilation_method = params.get("assimilation_method", self.assimilation_method)
        self.n_assimilation_cycles = params.get(
            "n_assimilation_cycles", self.n_assimilation_cycles
        )

        N = self.n_variables  # noqa: N806

        # 1. 初始化真实状态
        np.random.seed(self.seed)
        true_state = np.random.randn(N) * self.forcing * 0.1

        # Spin-up: 让系统达到混沌吸引子
        logger.info(
            "Lorenz-96 spin-up: %d步, N=%d, F=%.1f",
            self.n_spinup_steps, N, self.forcing,
        )
        for _ in range(self.n_spinup_steps):
            true_state = self._lorenz96_rhs(true_state, dt=self.dt)

        # 2. 初始化分析集合
        ensemble = self._initialize_ensemble(true_state)

        # 3. 循环同化
        rmse_time_series: list[float] = []
        spread_time_series: list[float] = []
        cycle_results: list[dict[str, Any]] = []

        current_true = true_state.copy()

        for cycle_idx in range(self.n_assimilation_cycles):
            # 预报步: 将真实状态和集合前向积分
            for _ in range(self.n_forecast_steps):
                current_true = self._lorenz96_rhs(current_true, dt=self.dt)
                for k in range(self.ensemble_size):
                    ensemble[k] = self._lorenz96_rhs(ensemble[k], dt=self.dt)

            # 生成观测
            obs_mask = self._generate_observation_mask(N)
            y_obs = current_true[obs_mask] + np.random.randn(np.sum(obs_mask)) * self.obs_error

            # 同化步
            analysis_result = self._assimilation_step(
                ensemble, y_obs, obs_mask
            )
            ensemble = analysis_result["ensemble"]

            # 统计
            analysis_mean = ensemble.mean(axis=0)
            rmse = float(np.sqrt(np.mean((analysis_mean - current_true) ** 2)))
            spread = float(np.std(ensemble, axis=0).mean())

            rmse_time_series.append(rmse)
            spread_time_series.append(spread)

            cycle_results.append({
                "cycle": cycle_idx,
                "rmse": rmse,
                "spread": spread,
                "n_observations": int(np.sum(obs_mask)),
            })

        # 最终统计
        final_analysis_mean = ensemble.mean(axis=0)
        final_rmse = float(np.sqrt(np.mean((final_analysis_mean - current_true) ** 2)))

        return {
            "analysis_field": final_analysis_mean.tolist(),
            "true_state": current_true.tolist(),
            "n_variables": N,
            "forcing": self.forcing,
            "assimilation_method": self.assimilation_method,
            "n_cycles": self.n_assimilation_cycles,
            "final_rmse": final_rmse,
            "mean_rmse": float(np.mean(rmse_time_series)),
            "mean_spread": float(np.mean(spread_time_series)),
            "rmse_time_series": rmse_time_series,
            "spread_time_series": spread_time_series,
            "cycle_results": cycle_results,
            "diagnostics": {
                "rmse_mean": float(np.mean(rmse_time_series)),
                "rmse_std": float(np.std(rmse_time_series)),
                "rmse_min": float(np.min(rmse_time_series)),
                "rmse_max": float(np.max(rmse_time_series)),
                "spread_mean": float(np.mean(spread_time_series)),
                "spread_rmse_ratio": float(
                    np.mean(spread_time_series) / max(np.mean(rmse_time_series), 1e-10)
                ),
            },
        }

    # ================================================================
    # Lorenz-96 模型
    # ================================================================

    def _lorenz96_rhs(self, x: np.ndarray, dt: float) -> np.ndarray:
        """Lorenz-96 模型右端项（使用RK4积分）.

        dx_i/dt = (x_{i+1} - x_{i-2}) * x_{i-1} - x_i + F

        使用四阶Runge-Kutta方法积分一个时间步。

        Args:
            x: 当前状态向量 (N,)
            dt: 时间步长

        Returns:
            积分一步后的状态向量
        """
        N = len(x)  # noqa: N806
        F = self.forcing

        def rhs(state: np.ndarray) -> np.ndarray:
            """计算右端项."""
            dxdt = np.zeros(N)
            for i in range(N):
                # 周期边界条件
                x_ip1 = state[(i + 1) % N]
                x_im1 = state[(i - 1) % N]
                x_im2 = state[(i - 2) % N]
                dxdt[i] = (x_ip1 - x_im2) * x_im1 - state[i] + F
            return dxdt

        # RK4积分
        k1 = rhs(x)
        k2 = rhs(x + 0.5 * dt * k1)
        k3 = rhs(x + 0.5 * dt * k2)
        k4 = rhs(x + dt * k3)

        return x + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    # ================================================================
    # 集合初始化
    # ================================================================

    def _initialize_ensemble(self, true_state: np.ndarray) -> np.ndarray:
        """围绕真实状态初始化集合成员."""
        N = len(true_state)  # noqa: N806
        np.random.seed(self.seed + 1)
        perturbation = np.random.randn(self.ensemble_size, N) * self.background_error_scale
        ensemble = true_state[np.newaxis, :] + perturbation
        return ensemble

    # ================================================================
    # 观测生成
    # ================================================================

    def _generate_observation_mask(self, N: int) -> np.ndarray:  # noqa: N806
        """生成观测掩码（决定哪些变量被观测）.

        Args:
            N: 系统维度

        Returns:
            布尔掩码数组
        """
        np.random.seed(None)  # 使用随机掩码
        mask = np.random.rand(N) < self.obs_density
        # 确保至少有一个观测
        if not np.any(mask):
            mask[0] = True
        return mask

    # ================================================================
    # 同化步
    # ================================================================

    def _assimilation_step(
        self,
        ensemble: np.ndarray,
        y_obs: np.ndarray,
        obs_mask: np.ndarray,
    ) -> dict[str, Any]:
        """执行单步同化.

        根据配置的同化方法选择不同的分析方案。

        Args:
            ensemble: 预报集合 (n_ens x N)
            y_obs: 观测向量 (m,)
            obs_mask: 观测掩码 (N,)

        Returns:
            包含更新后集合的字典
        """
        method = self.assimilation_method.lower()

        if method == "enkf":
            return self._enkf_step(ensemble, y_obs, obs_mask)
        elif method == "etkf":
            return self._etkf_step(ensemble, y_obs, obs_mask)
        elif method == "3dvar":
            return self._3dvar_step(ensemble, y_obs, obs_mask)
        else:
            logger.warning("未知同化方法 '%s'，使用EnKF", method)
            return self._enkf_step(ensemble, y_obs, obs_mask)

    def _enkf_step(
        self,
        ensemble: np.ndarray,
        y_obs: np.ndarray,
        obs_mask: np.ndarray,
    ) -> dict[str, Any]:
        """EnKF分析步."""
        n_ens = ensemble.shape[0]
        N = ensemble.shape[1]  # noqa: N806
        m = len(y_obs)

        # 构建局地观测算子
        H = np.zeros((m, N))  # noqa: N806
        obs_indices = np.where(obs_mask)[0]
        for j, idx in enumerate(obs_indices):
            H[j, idx] = 1.0  # noqa: N806

        # 集合统计
        x_mean = ensemble.mean(axis=0)
        X_pert = ensemble - x_mean[np.newaxis, :]
        Pf = (X_pert.T @ X_pert) / (n_ens - 1)

        # 卡尔曼增益
        R = np.eye(m) * self.obs_error**2  # noqa: N806
        HPHT = H @ Pf @ H.T  # noqa: N806
        try:
            K = Pf @ H.T @ np.linalg.inv(HPHT + R)  # noqa: N806
        except np.linalg.LinAlgError:
            K = np.zeros((N, m))  # noqa: N806

        # 更新集合成员
        np.random.seed(None)
        obs_pert = np.random.randn(n_ens, m) * self.obs_error
        for i in range(n_ens):
            innovation = (y_obs + obs_pert[i]) - H @ ensemble[i]
            ensemble[i] = ensemble[i] + K @ innovation

        return {"ensemble": ensemble}

    def _etkf_step(
        self,
        ensemble: np.ndarray,
        y_obs: np.ndarray,
        obs_mask: np.ndarray,
    ) -> dict[str, Any]:
        """ETKF分析步（确定性版本）."""
        n_ens = ensemble.shape[0]
        N = ensemble.shape[1]  # noqa: N806
        m = len(y_obs)

        H = np.zeros((m, N))  # noqa: N806
        obs_indices = np.where(obs_mask)[0]
        for j, idx in enumerate(obs_indices):
            H[j, idx] = 1.0  # noqa: N806

        x_mean = ensemble.mean(axis=0)
        X_pert = ensemble - x_mean[np.newaxis, :]
        X_pert_scaled = X_pert / np.sqrt(n_ens - 1)

        Yb = H @ X_pert_scaled.T
        R = np.eye(m) * self.obs_error**2  # noqa: N806
        R_inv = np.linalg.inv(R)  # noqa: N806

        S = Yb.T @ R_inv @ Yb
        T = np.linalg.inv(np.eye(n_ens) + S + np.eye(n_ens) * 1e-10)

        try:
            eigenvalues, eigenvectors = np.linalg.eigh(T)
            eigenvalues = np.maximum(eigenvalues, 1e-10)
            T_sqrt = eigenvectors @ np.diag(np.sqrt(eigenvalues)) @ eigenvectors.T
        except np.linalg.LinAlgError:
            T_sqrt = np.eye(n_ens) / np.sqrt(n_ens)

        K = X_pert_scaled.T @ Yb.T @ R_inv @ T  # noqa: N806
        innovation = y_obs - H @ x_mean
        analysis_mean = x_mean + K @ innovation

        analysis_pert = X_pert_scaled @ T_sqrt.T * np.sqrt(n_ens - 1)
        ensemble = analysis_mean[np.newaxis, :] + analysis_pert

        return {"ensemble": ensemble}

    def _3dvar_step(
        self,
        ensemble: np.ndarray,
        y_obs: np.ndarray,
        obs_mask: np.ndarray,
    ) -> dict[str, Any]:
        """简化3D-VAR分析步."""
        N = ensemble.shape[1]  # noqa: N806
        m = len(y_obs)

        H = np.zeros((m, N))  # noqa: N806
        obs_indices = np.where(obs_mask)[0]
        for j, idx in enumerate(obs_indices):
            H[j, idx] = 1.0  # noqa: N806

        x_mean = ensemble.mean(axis=0)
        R = np.eye(m) * self.obs_error**2  # noqa: N806
        B = np.eye(N) * self.background_error_scale**2  # noqa: N806

        # 简化3D-VAR: x_a = x_b + B H^T (H B H^T + R)^{-1} (y - H x_b)
        HBHt = H @ B @ H.T  # noqa: N806
        try:
            K = B @ H.T @ np.linalg.inv(HBHt + R)  # noqa: N806
        except np.linalg.LinAlgError:
            K = np.zeros((N, m))  # noqa: N806

        innovation = y_obs - H @ x_mean
        analysis_mean = x_mean + K @ innovation

        # 用分析均值替换所有集合成员（3D-VAR不更新集合扰动）
        ensemble = np.tile(analysis_mean, (ensemble.shape[0], 1))
        # 添加小扰动保持集合展开度
        ensemble += np.random.randn(*ensemble.shape) * self.background_error_scale * 0.1

        return {"ensemble": ensemble}

    # ================================================================
    # 工具方法
    # ================================================================

    @staticmethod
    def generate_true_state(
        n_variables: int = 40,
        forcing: float = 8.0,
        dt: float = 0.05,
        n_spinup: int = 1000,
        seed: int = 42,
    ) -> np.ndarray:
        """生成Lorenz-96模型的spin-up后的真实状态.

        Args:
            n_variables: 系统维度
            forcing: 外部强迫
            dt: 时间步长
            n_spinup: spin-up步数
            seed: 随机种子

        Returns:
            spin-up后的状态向量
        """
        np.random.seed(seed)
        x = np.random.randn(n_variables) * forcing * 0.1

        for _ in range(n_spinup):
            dxdt = np.zeros(n_variables)
            for i in range(n_variables):
                x_ip1 = x[(i + 1) % n_variables]
                x_im1 = x[(i - 1) % n_variables]
                x_im2 = x[(i - 2) % n_variables]
                dxdt[i] = (x_ip1 - x_im2) * x_im1 - x[i] + forcing

            k1 = dxdt
            k2_state = x + 0.5 * dt * k1
            k2 = np.zeros(n_variables)
            for i in range(n_variables):
                x_ip1 = k2_state[(i + 1) % n_variables]
                x_im1 = k2_state[(i - 1) % n_variables]
                x_im2 = k2_state[(i - 2) % n_variables]
                k2[i] = (x_ip1 - x_im2) * x_im1 - k2_state[i] + forcing

            x = x + (dt / 6.0) * (k1 + 2 * k2)

        return x
