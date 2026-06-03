"""
风险感知代价重构算法
路径规划的核心代价函数。

代价 = α · 气象风险 + β · 能耗 + γ · 距离 + δ · 平滑性 + ε · 禁飞区惩罚

气象风险又细分为:
  - 侧风风险 (无人机侧翻)
  - 阵风风险 (突发颠簸)
  - 降水风险 (能见度/结冰)
  - 湍流风险 (PBL 内颠簸)
  - 热力风险 (上升/下沉气流)
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, List


@dataclass
class CostConfig:
    """代价权重配置"""
    # 主权重
    w_meteorological: float = 0.35    # 气象风险
    w_energy: float = 0.25           # 能耗
    w_distance: float = 0.20         # 距离
    w_smoothness: float = 0.10       # 平滑性
    w_restricted: float = 0.10       # 禁飞区

    # 子权重 (气象风险内部)
    w_crosswind: float = 0.30        # 侧风
    w_gust: float = 0.20             # 阵风
    w_turbulence: float = 0.25       # 湍流
    w_thermal: float = 0.15          # 热力
    w_precipitation: float = 0.10    # 降水

    # 阈值
    max_safe_wind: float = 12.0      # m/s, 超过此值禁飞
    max_gust: float = 15.0           # m/s
    max_turbulence_tke: float = 5.0  # m²/s²
    restricted_zone_penalty: float = 1e6

    # 无人机参数
    uav_mass: float = 5.0            # kg
    uav_drag_coeff: float = 0.3
    uav_wing_area: float = 0.5       # m²
    air_density: float = 1.225       # kg/m³
    battery_capacity: float = 500    # Wh


class RiskCostFunction:
    """
    风险感知代价函数

    输入: 气象场 + 风险场 + 禁飞区 → 输出: 每条边/路径的代价
    """

    def __init__(self, config: Optional[CostConfig] = None):
        self.config = config or CostConfig()

    def edge_cost(self, p1: np.ndarray, p2: np.ndarray,
                  wind_u: np.ndarray, wind_v: np.ndarray,
                  risk_map: np.ndarray, tke: Optional[np.ndarray] = None,
                  restricted_zones: Optional[np.ndarray] = None,
                  precipitation: Optional[np.ndarray] = None) -> float:
        """
        计算两格点之间的通行代价

        Args:
            p1, p2: (y, x) 格子坐标
            wind_u, wind_v: 风场
            risk_map: GPR 风险方差场
            tke: 湍流动能 (可选)
            restricted_zones: 禁飞区掩码 (可选)
            precipitation: 降水率 mm/h (可选)

        Returns:
            总代价 (浮点数)
        """
        # 内插气象值到路径中点
        mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        u = self._interp(wind_u, mid)
        v = self._interp(wind_v, mid)
        risk = self._interp(risk_map, mid)

        # 每个子代价
        met_cost = self._meteorological_cost(u, v, risk, tke, precipitation, mid)
        energy_cost = self._energy_cost(u, v, p1, p2)
        dist_cost = self._distance_cost(p1, p2)
        smooth_cost = 0.0  # 在路径规划器里做
        restricted_cost = self._restricted_zone_cost(mid, restricted_zones)

        # 总代价
        total = (self.config.w_meteorological * met_cost
                 + self.config.w_energy * energy_cost
                 + self.config.w_distance * dist_cost
                 + self.config.w_smoothness * smooth_cost
                 + self.config.w_restricted * restricted_cost)

        # 硬约束: 风速超过安全阈值 → 极高代价
        wind_speed = np.sqrt(u**2 + v**2)
        if wind_speed > self.config.max_safe_wind:
            total += 1e6 * (wind_speed / self.config.max_safe_wind) ** 3

        return float(total)

    # ── 子代价 ─────────────────────────────────

    def _meteorological_cost(self, u: float, v: float, risk: float,
                             tke: Optional[float],
                             precip: Optional[float],
                             pos: Tuple[float, float]) -> float:
        """气象风险子代价"""
        wind_speed = np.sqrt(u**2 + v**2)
        cost = 0.0

        # 侧风风险 (垂直航线分量)
        crosswind = abs(u)  # 简化为 u 分量
        cost += self.config.w_crosswind * (crosswind / self.config.max_safe_wind)

        # GPR 风险方差场 (不确定性越高越危险)
        cost += self.config.w_gust * risk

        # 湍流
        if tke is not None:
            cost += (self.config.w_turbulence
                     * min(tke / self.config.max_turbulence_tke, 1.0))

        # 降水
        if precip is not None:
            cost += self.config.w_precipitation * min(precip / 10.0, 1.0)

        return cost

    def _energy_cost(self, u: float, v: float,
                     p1: np.ndarray, p2: np.ndarray) -> float:
        """能耗代价: 考虑逆风增加的功耗"""
        dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2) * 1000  # km → m

        # 飞行方向
        if dist < 1:
            return 0.0
        flight_dir = np.array([p2[0] - p1[0], p2[1] - p1[1]])
        flight_dir = flight_dir / np.linalg.norm(flight_dir)

        # 风速在飞行方向上的投影 (逆风为正)
        wind_vec = np.array([u, v])
        headwind = -np.dot(wind_vec, flight_dir)
        headwind = max(headwind, 0)

        # 简化能耗模型: P = (mg + 0.5ρCdA(v+headwind)²) × v
        drag = (0.5 * self.config.air_density
                * self.config.uav_drag_coeff
                * self.config.uav_wing_area
                * (5 + headwind)**2)
        power = (self.config.uav_mass * 9.81 + drag) * 5  # 5m/s 巡航
        energy = power * dist / 5  # J

        return energy / self.config.battery_capacity  # 归一化

    def _distance_cost(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """距离代价"""
        return float(np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2))

    def _restricted_zone_cost(self, pos: Tuple[float, float],
                              zones: Optional[np.ndarray]) -> float:
        """禁飞区代价"""
        if zones is None:
            return 0.0
        gy, gx = int(pos[0]), int(pos[1])
        if 0 <= gy < zones.shape[0] and 0 <= gx < zones.shape[1]:
            if zones[gy, gx] > 0:
                return self.config.restricted_zone_penalty
        return 0.0

    @staticmethod
    def _interp(field: np.ndarray, pos: Tuple[float, float]) -> float:
        """双线性插值, 边界处理简单取最近"""
        y, x = pos
        H, W = field.shape
        yi, xi = int(y), int(x)
        yi = np.clip(yi, 0, H - 1)
        xi = np.clip(xi, 0, W - 1)

        if yi + 1 >= H or xi + 1 >= W:
            return float(field[yi, xi])

        # 双线性插值
        dy, dx = y - yi, x - xi
        return float(
            field[yi, xi] * (1 - dy) * (1 - dx)
            + field[yi + 1, xi] * dy * (1 - dx)
            + field[yi, xi + 1] * (1 - dy) * dx
            + field[yi + 1, xi + 1] * dy * dx
        )

    # ── 路径总代价 ─────────────────────────────

    def path_cost(self, path: List[np.ndarray],
                  wind_u: np.ndarray, wind_v: np.ndarray,
                  risk_map: np.ndarray,
                  **kwargs) -> float:
        """整条路径的总代价"""
        total = 0.0
        for i in range(len(path) - 1):
            total += self.edge_cost(path[i], path[i + 1],
                                    wind_u, wind_v, risk_map, **kwargs)
        return total
