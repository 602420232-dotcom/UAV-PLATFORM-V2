"""
贝叶斯主动观测决策算法


问题:
  无人机观测资源有限 (电量/时间), 每次只能采集少量站点。
  应该去哪些位置采集观测值, 才能最大化对预报的改进?


方法:
  贝叶斯主动学习 (Bayesian Active Learning)
  - 用 GPR 的预测方差衡量每个位置的"信息量"
  - 选择方差最大的位置去采集 (不确定性采样)
  - 采集后更新 GPR, 方差下降 → 选择下一个位置


流程:
  1. 用当前 GPR 风险场计算全局方差场
  2. 选择方差最大的 N 个未采样点
  3. 派出无人机去这些位置采集
  4. 采集到的观测值同化进 GPR
  5. 重新计算方差场 → 回到 1
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple
from scipy.spatial.distance import cdist


@dataclass
class ActiveObsConfig:
    """主动观测配置"""
    # 采集策略
    acquisition_function: str = "variance"  # variance | entropy | mutual_info | random
    n_observations_per_round: int = 5       # 每轮采集点数
    n_rounds: int = 10                      # 总轮数

    # 约束
    max_flight_range_km: float = 50.0       # 单次飞行最远
    max_observation_altitude: float = 300.0  # m
    min_distance_between_obs: float = 2.0   # km, 避免重复

    # GPR
    gpr_noise: float = 0.1
    gpr_lengthscale: float = 5.0            # km

    # 预算
    budget_per_round_wh: float = 100.0      # 每轮能耗预算 (Wh)


class BayesianActiveObserver:
    """
    贝叶斯主动观测决策器

    用法:
        observer = BayesianActiveObserver()
        for round in range(n_rounds):
            query_points = observer.select_observation_points(variance_map, sampled_positions)
            observations = fly_and_observe(query_points)  # 外部执行
            observer.update_gpr(query_points, observations)
    """

    def __init__(self, config: Optional[ActiveObsConfig] = None):
        self.config = config or ActiveObsConfig()
        self.sampled_positions: List[np.ndarray] = []
        self.sampled_values: List[float] = []
        self.gpr_model: Optional[object] = None

    def select_observation_points(self, variance_map: np.ndarray,
                                  existing_sites: Optional[List[Tuple[float, float]]] = None,
                                  n_points: Optional[int] = None) -> List[Tuple[float, float]]:
        """
        选择下一轮观测位置

        Args:
            variance_map: (H, W) GPR 方差场
            existing_sites: 已有观测站点 [(x, y), ...]
            n_points: 本轮采集数 (默认 config.n_observations_per_round)

        Returns:
            query_points: [(x, y), ...] 建议观测位置 (世界坐标 km)
        """
        H, W = variance_map.shape
        n = n_points or self.config.n_observations_per_round

        # 生成候选点网格 (世界坐标)
        candidates = []
        for i in range(0, H, 3):   # 3km 采样候选
            for j in range(0, W, 3):
                x = j * 1.0 - 75     # 世界坐标 km
                y = i * 1.0 - 75
                candidates.append((x, y, i, j, variance_map[i, j]))
        candidates = np.array(candidates)

        if len(candidates) == 0:
            return [(0, 0)]

        # 排除已有站点附近的候选点
        if existing_sites and len(existing_sites) > 0:
            existing = np.array(existing_sites)
            dists = cdist(candidates[:, :2], existing)
            too_close = dists.min(axis=1) < self.config.min_distance_between_obs
            candidates = candidates[~too_close]
            if len(candidates) == 0:
                return [(0, 0)]

        # 按采集函数排序
        if self.config.acquisition_function == "random":
            idx = np.random.choice(len(candidates), min(n, len(candidates)), replace=False)
        else:
            # 方差最大或熵最大
            scores = candidates[:, 4]
            if self.config.acquisition_function == "entropy":
                scores = 0.5 * np.log(2 * np.pi * np.e * np.maximum(scores, 1e-10))
            elif self.config.acquisition_function == "mutual_info":
                # 互信息近似: 高方差 + 与其他候选点差异大
                diversity = np.std(candidates[:, :2], axis=1)
                scores = scores * (1 + 0.1 * diversity)

            # 多样性: 选方差最大的几个但要分散
            top_n = min(n * 3, len(candidates))
            top_idx = np.argsort(scores)[-top_n:][::-1]

            # 从 top 里挑尽量分散的
            selected = []
            for idx in top_idx:
                pt = candidates[idx, :2]
                if len(selected) == 0:
                    selected.append(idx)
                else:
                    dists = cdist([pt], candidates[np.array(selected)][:, :2])
                    if dists.min() >= self.config.min_distance_between_obs:
                        selected.append(idx)
                if len(selected) >= n:
                    break
            idx = np.array(selected)

        return [(candidates[i, 0], candidates[i, 1]) for i in idx]

    def update_gpr(self, positions: List[Tuple[float, float]],
                   observations: List[float]):
        """
        用新采集的观测值更新 GPR

        Args:
            positions: 采集位置 [(x, y), ...]
            observations: 观测值 [value, ...]
        """
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, WhiteKernel

        for pos, val in zip(positions, observations):
            self.sampled_positions.append(np.array(pos))
            self.sampled_values.append(val)

        if len(self.sampled_positions) < 3:
            return  # 样本太少, 不更新

        X = np.array(self.sampled_positions)
        y = np.array(self.sampled_values)

        kernel = (RBF(length_scale=self.config.gpr_lengthscale)
                  + WhiteKernel(noise_level=self.config.gpr_noise))
        self.gpr_model = GaussianProcessRegressor(kernel=kernel, alpha=self.config.gpr_noise**2)
        self.gpr_model.fit(X, y)

    def compute_acquisition_value(self, x: float, y: float) -> float:
        """
        计算某个位置的采集价值

        Returns:
            value: 值越大越值得采集
        """
        if self.gpr_model is None:
            return 1.0

        pos = np.array([[x, y]])
        _, std = self.gpr_model.predict(pos, return_std=True)
        return float(std[0])

    def get_exploration_map(self, H: int = 150, W: int = 150) -> np.ndarray:
        """
        生成全场的采集价值图

        Returns:
            acquisition_map: (H, W) 值越高越建议去采集
        """
        if self.gpr_model is None:
            return np.ones((H, W))

        grid_x, grid_y = np.meshgrid(np.arange(W) * 1.0 - 75, np.arange(H) * 1.0 - 75)
        positions = np.column_stack([grid_x.ravel(), grid_y.ravel()])

        _, std = self.gpr_model.predict(positions, return_std=True)
        return std.reshape(H, W)
