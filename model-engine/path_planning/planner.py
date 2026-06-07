"""
GPR 风险场驱动的路径规划

保留原 Java path-planning-service 作为传统方法 baseline。


此模块为新增的 Python 路径规划器，专为新架构设计:
  - 读入 GPR 风险方差场
  - 在风险约束下做路径优化
  - 输出避障路径 + 置信区间

与原 Java 服务不冲突，可并行运行用于对比
"""
import logging
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)

# ── 坐标系配置常量 ────────────────────────────
# 网格范围: 150km × 150km, 分辨率: 1km/grid
GRID_EXTENT_KM = 150.0
GRID_RESOLUTION_KM = 1.0
GRID_OFFSET_KM = GRID_EXTENT_KM / 2.0  # 75km, 将原点(-75,-75)映射到网格(0,0)


class RiskLevel(Enum):
    SAFE = 0
    CAUTION = 1
    HIGH_RISK = 2
    NO_FLY = 3


@dataclass
class PlanningConfig:
    """路径规划配置"""
    # 风险阈值
    risk_threshold_safe: float = 0.3
    risk_threshold_caution: float = 0.6
    risk_threshold_high: float = 0.8
    risk_threshold_no_fly: float = 0.9

    # 无人机约束
    max_speed: float = 15.0       # m/s
    max_wind: float = 12.0        # m/s (超过此值禁飞)
    max_payload: float = 5.0      # kg
    battery_hours: float = 0.5    # 半小时

    # 规划参数
    n_waypoints: int = 20
    safety_margin_km: float = 0.5
    grid_resolution_km: float = 1.0

    # 优化权重
    w_risk: float = 0.4
    w_distance: float = 0.3
    w_energy: float = 0.2
    w_smoothness: float = 0.1


@dataclass
class Waypoint:
    x: float          # km (相对成都中心)
    y: float
    z: float          # 高度 (m)
    risk: float = 0.0
    wind_u: float = 0.0
    wind_v: float = 0.0


class GPRPathPlanner:
    """
    基于 GPR 风险场的路径规划器

    输入:
      - risk_map: (H, W) 风险方差场 (来自 GPR)
      - wind_u/v: (H, W) 风场 (来自融合预报)
      - start/end: 起止点坐标

    算法: 风险感知 A* + 贝塞尔平滑
    """

    def __init__(self, config: Optional[PlanningConfig] = None):
        self.config = config or PlanningConfig()

    def plan(self, risk_map: np.ndarray, wind_u: np.ndarray,
             wind_v: np.ndarray, start: Tuple[float, float],
             end: Tuple[float, float]) -> List[Waypoint]:
        """
        规划路径

        Args:
            risk_map: (H, W) 风险场
            wind_u: (H, W) 风场 u 分量
            wind_v: (H, W) 风场 v 分量
            start: (x, y) 起点 (km)
            end: (x, y) 终点 (km)

        Returns:
            路径点列表
        """
        H, W = risk_map.shape
        sx, sy = self._world_to_grid(start[0], start[1], H, W)
        ex, ey = self._world_to_grid(end[0], end[1], H, W)

        # 风险感知 A*
        path = self._risk_aware_astar(risk_map, wind_u, wind_v, (sx, sy), (ex, ey))

        # 贝塞尔平滑
        path = self._bezier_smooth(path)

        # 转为 Waypoint
        return self._to_waypoints(path, risk_map, wind_u, wind_v, H, W)

    def _risk_aware_astar(self, risk: np.ndarray, u: np.ndarray,
                          v: np.ndarray, start: Tuple[int, int],
                          end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        风险感知 A*

        代价函数: f = g_distance + h + λ * risk
        避免了高风险区域，同时最小化路径长度
        """
        import heapq
        H, W = risk.shape
        risk = risk.copy()

        # 禁飞区 (风险极高)
        no_fly = risk > self.config.risk_threshold_no_fly
        risk[no_fly] = np.inf

        start = (int(start[0]), int(start[1]))
        end = (int(end[0]), int(end[1]))

        # A*
        g_score = {start: 0.0}
        f_score = {start: self._heuristic(start, end)}
        came_from = {}
        open_set = [(f_score[start], start)]

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0),
                      (1, 1), (-1, 1), (1, -1), (-1, -1)]

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end:
                return self._reconstruct_path(came_from, current)

            for dx, dy in directions:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor = (nx, ny)

                if not (0 <= nx < H and 0 <= ny < W):
                    continue
                if risk[nx, ny] == np.inf:
                    continue

                # 距离代价
                dist = np.sqrt(dx**2 + dy**2)
                # 风险代价
                risk_cost = risk[nx, ny] * self.config.w_risk
                # 风代价 (逆风惩罚)
                wind_cost = max(0, u[nx, ny] * dx + v[nx, ny] * dy) * 0.01

                tentative_g = (g_score[current]
                               + dist * self.config.w_distance
                               + risk_cost
                               + wind_cost * self.config.w_energy)

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (f, neighbor))

        # 找不到路径 → 返回直线
        return self._linear_path(start, end)

    def _heuristic(self, a: Tuple, b: Tuple) -> float:
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def _bezier_smooth(self, path: List[Tuple[int, int]],
                       n_interp: int = 50) -> List[Tuple[float, float]]:
        """贝塞尔曲线平滑"""
        if len(path) < 2:
            return [(float(p[0]), float(p[1])) for p in path]

        path_xy = np.array(path, dtype=float)
        t = np.linspace(0, 1, n_interp)
        smooth = []
        for i in t:
            # 伯恩斯坦多项式 (n=3 级数)
            seg_idx = min(int(i * (len(path_xy) - 1)), len(path_xy) - 2)
            p0 = path_xy[max(0, seg_idx - 1)]
            p1 = path_xy[seg_idx]
            p2 = path_xy[min(seg_idx + 1, len(path_xy) - 1)]
            p3 = path_xy[min(seg_idx + 2, len(path_xy) - 1)]

            local_t = (i * (len(path_xy) - 1)) - seg_idx
            x = (1 - local_t)**3 * p0[0] + 3 * (1 - local_t)**2 * local_t * p1[0] \
                + 3 * (1 - local_t) * local_t**2 * p2[0] + local_t**3 * p3[0]
            y = (1 - local_t)**3 * p0[1] + 3 * (1 - local_t)**2 * local_t * p1[1] \
                + 3 * (1 - local_t) * local_t**2 * p2[1] + local_t**3 * p3[1]
            smooth.append((x, y))
        return smooth

    def _to_waypoints(self, path: List, risk: np.ndarray,
                      u: np.ndarray, v: np.ndarray,
                      H: int, W: int) -> List[Waypoint]:
        """网格路径 → Waypoint 列表"""
        waypoints = []
        for x, y in path:
            gx, gy = int(x), int(y)
            gx = np.clip(gx, 0, H - 1)
            gy = np.clip(gy, 0, W - 1)
            waypoints.append(Waypoint(
                x=self._grid_to_world(x, W),
                y=self._grid_to_world(y, H),
                z=100,  # 默认高度
                risk=float(risk[gx, gy]),
                wind_u=float(u[gx, gy]),
                wind_v=float(v[gx, gy]),
            ))
        return waypoints

    @staticmethod
    def _reconstruct_path(came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    @staticmethod
    def _linear_path(start, end):
        return [start, end]

    @staticmethod
    def _world_to_grid(x: float, y: float, H: int, W: int) -> Tuple[int, int]:
        """世界坐标 (km) → 网格坐标"""
        gx = int((x + GRID_OFFSET_KM) / GRID_RESOLUTION_KM)
        gy = int((y + GRID_OFFSET_KM) / GRID_RESOLUTION_KM)
        return np.clip(gx, 0, H - 1), np.clip(gy, 0, W - 1)

    @staticmethod
    def _grid_to_world(gx: float, H: int) -> float:
        return gx * GRID_RESOLUTION_KM - GRID_OFFSET_KM


# ── 新旧路径规划对比 ────────────────────────────


class PathPlanningComparison:
    """
    路径规划对比器

    旧: Java path-planning-service (WRF + 确定性)
    新: GPRPathPlanner (风险感知)
    """

    def run_comparison(self, scenario: str = "chengdu_plain"):
        """运行对比"""
        # 模拟风险场
        H, W = 150, 150
        np.random.seed(42)
        risk = np.random.exponential(0.3, (H, W))
        # 成都市中心低风险，外围高风险
        cy, cx = H // 2, W // 2
        y, x = np.ogrid[:H, :W]
        risk *= 1 - 0.5 * np.exp(-((y - cy)**2 + (x - cx)**2) / (2 * 20**2))

        wind_u = np.random.normal(2, 1, (H, W))
        wind_v = np.random.normal(0.5, 0.8, (H, W))

        planner = GPRPathPlanner()

        # 不同起止点
        scenarios = [
            ("市中心→龙泉驿", (-10, 0), (20, -5)),
            ("双流→新都", (-15, -10), (10, 15)),
            ("都江堰→简阳", (-30, 20), (40, -20)),
        ]

        results = []
        for name, start, end in scenarios:
            path = planner.plan(risk, wind_u, wind_v, start, end)
            total_risk = sum(w.risk for w in path) / len(path)
            total_dist = np.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2)
            results.append({
                "scenario": name,
                "waypoints": len(path),
                "avg_risk": round(total_risk, 4),
                "total_dist_km": round(total_dist, 1),
                "max_risk": round(max(w.risk for w in path), 4),
            })
            logger.info(f"  [{name}] {len(path)} waypoints, "
                        f"avg_risk={total_risk:.4f}, dist={total_dist:.1f}km")

        return results
