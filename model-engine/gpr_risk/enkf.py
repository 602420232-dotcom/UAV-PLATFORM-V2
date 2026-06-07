"""
EnKF 贝叶斯动态同化模块
对应论文第四阶段 "4. 贝叶斯动态同化模块"


原理:
  1. 概率 U-Net 给出均值和方差，生成 N 个集合成员
  2. 集合成员前向传播 (时间演变)
  3. 新观测到达 → EnKF 分析更新
  4. 更新后集合均值 = 同化后分析场
  5. 更新后集合方差 = 不确定性 (下降了)


公式:
  X^a = X^f + K (Y - H X^f)
  K = P^f H^T (H P^f H^T + R)^{-1}
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List, Callable


@dataclass
class EnKFConfig:
    """EnKF 配置"""
    n_ensemble: int = 20             # 集合成员数 (论文说约20个)
    inflation_factor: float = 1.05   # 协方差膨胀 (防止滤波发散)
    localization_radius_km: float = 30.0  # 局地化半径
    observation_noise: float = 0.1   # 观测误差标准差 R
    use_mc_dropout: bool = True      # 用 MC Dropout 还是直接采样
    dropout_rate: float = 0.1


class EnsembleKalmanFilter:
    """
    集合卡尔曼滤波

    用法:
        enkf = EnsembleKalmanFilter(n_ensemble=20)
        # 初始集合: 从概率 U-Net 生成
        ensemble = enkf.generate_ensemble(mean, log_var)
        # 前向传播
        forecast = enkf.forecast(ensemble, forward_fn)
        # 同化新观测
        analysis = enkf.assimilate(forecast, observations, obs_positions, obs_operator)
    """

    def __init__(self, config: Optional[EnKFConfig] = None):
        self.config = config or EnKFConfig()
        self.ensemble_history: List[np.ndarray] = []

    # ── 1. 生成集合成员 ────────────────────────────

    def generate_ensemble(self, mean: np.ndarray,
                          log_var: np.ndarray) -> np.ndarray:
        """
        从概率 U-Net 输出生成 N 个集合成员

        Args:
            mean: (C, H, W) 预报均值
            log_var: (C, H, W) 对数方差

        Returns:
            ensemble: (N, C, H, W) 集合成员
        """
        N = self.config.n_ensemble
        std = np.exp(0.5 * log_var)
        noise = np.random.normal(0, 1, (N, ) + mean.shape)
        ensemble = mean + noise * std  # 每个成员 = 均值 + 扰动 × 标准差
        return ensemble

    # ── 2. 前向传播 ────────────────────────────

    def forecast(self, ensemble: np.ndarray,
                 forward_fn: Callable) -> np.ndarray:
        """
        每个集合成员前向传播 (时间演变)

        Args:
            ensemble: (N, C, H, W)
            forward_fn: 单个成员的预测函数

        Returns:
            forecast: (N, C, H, W)
        """
        N = ensemble.shape[0]
        forecast_members = []
        for i in range(N):
            member = ensemble[i]  # (C, H, W)
            forecast_member = forward_fn(member)
            forecast_members.append(forecast_member)
        return np.array(forecast_members)

    # ── 3. EnKF 分析更新 ─────────────────────────

    def assimilate(self, forecast: np.ndarray,
                   observations: np.ndarray,
                   obs_positions: np.ndarray,
                   obs_operator: Optional[Callable] = None
                   ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        EnKF 分析更新

        Args:
            forecast: (N, C, H, W) 预报集合
            observations: (M, ) 观测值
            obs_positions: (M, 2) 观测位置 (y, x)
            obs_operator: H 函数，将网格插值到观测位置

        Returns:
            analysis: (N, C, H, W) 同化后集合
            analysis_mean: (C, H, W) 同化后均值
            analysis_variance: (C, H, W) 同化后方差 (下降了!)
        """
        N, C, H, W = forecast.shape
        M = len(observations)

        # 集合均值
        ens_mean = forecast.mean(axis=0)  # (C, H, W)

        # 集合扰动 (每个成员减去均值)
        perturbations = forecast - ens_mean  # (N, C, H, W)

        # 计算预报协方差 P^f
        # P^f = (1/(N-1)) × X' × X'^T
        # 用扰动矩阵近似
        X_prime = perturbations.reshape(N, -1)  # (N, C*H*W)

        if obs_operator is not None:
            # 使用观测算子 H
            H_ensemble = np.array([obs_operator(forecast[i]) for i in range(N)])
        else:
            # 默认: 在观测位置取网格值
            H_ensemble = np.zeros((N, M))
            for i in range(N):
                for j, (y, x) in enumerate(obs_positions):
                    yi, xi = int(y), int(x)
                    yi = np.clip(yi, 0, H - 1)
                    xi = np.clip(xi, 0, W - 1)
                    H_ensemble[i, j] = forecast[i, 0, yi, xi]  # 取第一变量

        H_mean = H_ensemble.mean(axis=0)
        H_pert = H_ensemble - H_mean  # (N, M)

        # 计算卡尔曼增益 K
        # K = P^f H^T (H P^f H^T + R)^{-1}
        # 用集合近似: K = X' × (H')^T × (H' × (H')^T + R)^{-1} / (N-1)
        HPf = (X_prime.T @ H_pert) / (N - 1)  # (n_state, M)
        HPfHT = (H_pert.T @ H_pert) / (N - 1)  # (M, M)

        # 加观测噪声
        R = np.eye(M) * self.config.observation_noise ** 2
        innovation_cov = HPfHT + R

        # 卡尔曼增益
        try:
            K = HPf @ np.linalg.inv(innovation_cov)  # (n_state, M)
        except np.linalg.LinAlgError:
            K = HPf @ np.linalg.pinv(innovation_cov)

        # 每个集合成员分析更新
        analysis = np.zeros_like(forecast)
        for i in range(N):
            # 加扰动的观测 (EnKF 标准做法)
            obs_noise = np.random.normal(0, self.config.observation_noise, M)
            obs_perturbed = observations + obs_noise

            # 观测增量
            if obs_operator is not None:
                hx = obs_operator(forecast[i])
            else:
                hx = H_ensemble[i]

            innovation = obs_perturbed - hx  # 新息

            # 状态增量
            state_increment = K @ innovation  # (n_state,)
            analysis[i] = forecast[i] + state_increment.reshape(C, H, W)

        # 协方差膨胀
        if self.config.inflation_factor > 1.0:
            analysis_mean = analysis.mean(axis=0)
            analysis = analysis_mean + (analysis - analysis_mean) * self.config.inflation_factor

        # 输出
        analysis_mean = analysis.mean(axis=0)
        analysis_variance = analysis.var(axis=0)

        self.ensemble_history.append(analysis.copy())

        return analysis, analysis_mean, analysis_variance

    # ── 不确定性诊断 ──────────────────────────

    def uncertainty_reduction(self, prior_var: np.ndarray,
                              post_var: np.ndarray) -> float:
        """不确定性降低率 (越大说明同化效果越好)"""
        return 1 - post_var.mean() / max(prior_var.mean(), 1e-10)

    def get_ensemble_spread(self, ensemble: np.ndarray) -> float:
        """集合离散度 (越大说明不确定性越大)"""
        return float(ensemble.std(axis=0).mean())
