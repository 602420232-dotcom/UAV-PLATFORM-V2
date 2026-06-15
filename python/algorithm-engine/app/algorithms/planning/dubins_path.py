"""Dubins曲线路径规划算法。

生成考虑最小转弯半径约束的最短路径。
Dubins曲线由至多三段组成：直线段（L）和圆弧段（R或L），
共有六种组合：LSL, RSR, LSR, RSL, RLR, LRL。
适用于固定翼UAV等具有最小转弯半径约束的飞行器。
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class DubinsPathPlanner:
    """Dubins曲线路径规划器。

    给定起点位姿（位置+航向角）和终点位姿，
    计算满足最小转弯半径约束的最短路径。
    路径由直线段和最大曲率圆弧段组成。

    Args:
        config: 配置字典，支持以下参数：
            - min_turn_radius: 最小转弯半径，默认2.0
            - step_size: 路径采样步长，默认0.1
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.min_turn_radius: float = self.config.get("min_turn_radius", 2.0)
        self.step_size: float = self.config.get("step_size", 0.1)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行Dubins曲线路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 [x, y]
                - goal: 终点坐标 [x, y]
                - start_heading: 起始航向角（弧度），默认0
                - goal_heading: 终止航向角（弧度），默认0
                - grid_size: 网格尺寸 (int, int)

        Returns:
            包含 path（路径点列表）和 cost（路径长度）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", [0, 0]), dtype=float)
        goal = np.array(params.get("goal", [10, 10]), dtype=float)
        start_heading = params.get("start_heading", 0.0)
        goal_heading = params.get("goal_heading", 0.0)

        logger.info(
            "Dubins曲线规划: 起点=%s, 终点=%s, 最小转弯半径=%.1f",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.min_turn_radius,
        )

        # 归一化到起点坐标系
        dx = goal[0] - start[0]
        dy = goal[1] - start[1]
        dist = math.sqrt(dx**2 + dy**2)

        if dist < 1e-6:
            return {"path": [start.tolist()], "cost": 0.0}

        # 归一化角度
        theta = math.atan2(dy, dx) - start_heading
        phi = goal_heading - start_heading
        d = dist / self.min_turn_radius

        # 尝试所有6种Dubins路径类型
        best_path_type = None
        best_length = float("inf")
        best_params = None

        path_types = [
            ("LSL", self._dubins_lsl),
            ("RSR", self._dubins_rsr),
            ("LSR", self._dubins_lsr),
            ("RSL", self._dubins_rsl),
            ("RLR", self._dubins_rlr),
            ("LRL", self._dubins_lrl),
        ]

        for name, func in path_types:
            result = func(d, theta, phi)
            if result is not None:
                length = result[0] * self.min_turn_radius
                if length < best_length:
                    best_length = length
                    best_path_type = name
                    best_params = result

        if best_params is None:
            logger.warning("Dubins曲线计算失败，退化为直线")
            path = self._straight_line(start, goal)
            return {"path": path, "cost": float(np.linalg.norm(goal - start))}

        # 采样Dubins曲线路径
        path = self._sample_dubins_path(
            start, start_heading, best_path_type, best_params
        )

        logger.info(
            "Dubins曲线规划完成: 类型=%s, 长度=%.2f, 路径点=%d",
            best_path_type,
            best_length,
            len(path),
        )
        return {
            "path": path,
            "cost": best_length,
            "path_type": best_path_type,
        }

    def _dubins_lsl(
        self, d: float, theta: float, phi: float
    ) -> tuple[float, float, float] | None:
        """LSL类型Dubins曲线。"""
        p_sq = 2 + d**2 - 2 * math.cos(theta - phi) + 2 * d * (math.sin(theta) - math.sin(phi))
        if p_sq < 0:
            return None
        p = math.sqrt(p_sq)
        tmp = math.atan2(math.cos(phi) - math.cos(theta), d + math.sin(theta) - math.sin(phi))
        t = (-theta + tmp) % (2 * math.pi)
        q = (phi - tmp) % (2 * math.pi)
        return (t, p, q)

    def _dubins_rsr(
        self, d: float, theta: float, phi: float
    ) -> tuple[float, float, float] | None:
        """RSR类型Dubins曲线。"""
        p_sq = 2 + d**2 - 2 * math.cos(theta - phi) + 2 * d * (math.sin(phi) - math.sin(theta))
        if p_sq < 0:
            return None
        p = math.sqrt(p_sq)
        tmp = math.atan2(math.cos(theta) - math.cos(phi), d - math.sin(theta) + math.sin(phi))
        t = (theta - tmp) % (2 * math.pi)
        q = (-phi + tmp) % (2 * math.pi)
        return (t, p, q)

    def _dubins_lsr(
        self, d: float, theta: float, phi: float
    ) -> tuple[float, float, float] | None:
        """LSR类型Dubins曲线。"""
        p_sq = -2 + d**2 + 2 * math.cos(theta - phi) + 2 * d * (math.sin(theta) + math.sin(phi))
        if p_sq < 0:
            return None
        p = math.sqrt(p_sq)
        tmp = math.atan2(-math.cos(theta) - math.cos(phi), d + math.sin(theta) + math.sin(phi)) - math.atan2(-2.0, p)
        t = (-theta + tmp) % (2 * math.pi)
        q = (-phi + tmp) % (2 * math.pi)
        return (t, p, q)

    def _dubins_rsl(
        self, d: float, theta: float, phi: float
    ) -> tuple[float, float, float] | None:
        """RSL类型Dubins曲线。"""
        p_sq = -2 + d**2 + 2 * math.cos(theta - phi) - 2 * d * (math.sin(theta) + math.sin(phi))
        if p_sq < 0:
            return None
        p = math.sqrt(p_sq)
        tmp = math.atan2(math.cos(theta) + math.cos(phi), d - math.sin(theta) - math.sin(phi)) - math.atan2(2.0, p)
        t = (theta - tmp) % (2 * math.pi)
        q = (phi - tmp) % (2 * math.pi)
        return (t, p, q)

    def _dubins_rlr(
        self, d: float, theta: float, phi: float
    ) -> tuple[float, float, float] | None:
        """RLR类型Dubins曲线。"""
        tmp = (6 - d**2 + 2 * math.cos(theta - phi) + 2 * d * (math.sin(theta) - math.sin(phi))) / 8
        if abs(tmp) > 1:
            return None
        p = (2 * math.pi - math.acos(tmp)) % (2 * math.pi)
        t = (theta - math.atan2(math.cos(theta) - math.cos(phi), d - math.sin(theta) + math.sin(phi)) + p / 2) % (2 * math.pi)
        q = (theta - phi - t + p) % (2 * math.pi)
        return (t, p, q)

    def _dubins_lrl(
        self, d: float, theta: float, phi: float
    ) -> tuple[float, float, float] | None:
        """LRL类型Dubins曲线。"""
        tmp = (6 - d**2 + 2 * math.cos(theta - phi) + 2 * d * (math.sin(phi) - math.sin(theta))) / 8
        if abs(tmp) > 1:
            return None
        p = (2 * math.pi - math.acos(tmp)) % (2 * math.pi)
        t = (-theta - math.atan2(math.cos(theta) - math.cos(phi), d + math.sin(theta) - math.sin(phi)) + p / 2) % (2 * math.pi)
        q = (phi - theta - t + p) % (2 * math.pi)
        return (t, p, q)

    def _sample_dubins_path(
        self,
        start: np.ndarray,
        start_heading: float,
        path_type: str,
        params: tuple[float, float, float],
    ) -> list[list[float]]:
        """采样Dubins曲线路径点。"""
        t, p, q = params
        path = []
        total_length = (t + p + q) * self.min_turn_radius
        n_steps = max(int(total_length / self.step_size), 10)

        for i in range(n_steps + 1):
            s = (i / n_steps) * (t + p + q)
            x, y, heading = self._dubins_point(start, start_heading, path_type, t, p, q, s)
            path.append([float(x), float(y)])

        return [[int(round(px)), int(round(py))] for px, py in path]

    def _dubins_point(
        self,
        start: np.ndarray,
        start_heading: float,
        path_type: str,
        t: float,
        p: float,
        q: float,
        s: float,
    ) -> tuple[float, float, float]:
        """计算Dubins曲线上某一点的位姿。"""
        x, y, heading = start[0], start[1], start_heading

        if s < t:
            # 第一段
            seg = s
            if path_type[0] == "L":
                x += self.min_turn_radius * math.sin(heading + seg) - self.min_turn_radius * math.sin(heading)
                y += -self.min_turn_radius * math.cos(heading + seg) + self.min_turn_radius * math.cos(heading)
                heading += seg
            else:
                x += -self.min_turn_radius * math.sin(heading - seg) + self.min_turn_radius * math.sin(heading)
                y += self.min_turn_radius * math.cos(heading - seg) - self.min_turn_radius * math.cos(heading)
                heading -= seg
        elif s < t + p:
            # 第二段（直线）
            seg = s - t
            x += self.min_turn_radius * math.cos(heading) * seg
            y += self.min_turn_radius * math.sin(heading) * seg
        else:
            # 第三段
            seg = s - t - p
            if path_type[2] == "L":
                x += self.min_turn_radius * math.sin(heading + seg) - self.min_turn_radius * math.sin(heading)
                y += -self.min_turn_radius * math.cos(heading + seg) + self.min_turn_radius * math.cos(heading)
                heading += seg
            else:
                x += -self.min_turn_radius * math.sin(heading - seg) + self.min_turn_radius * math.sin(heading)
                y += self.min_turn_radius * math.cos(heading - seg) - self.min_turn_radius * math.cos(heading)
                heading -= seg

        return x, y, heading

    def _straight_line(
        self,
        start: np.ndarray,
        goal: np.ndarray,
    ) -> list[list[int]]:
        """生成直线路径。"""
        dist = np.linalg.norm(goal - start)
        n_points = max(int(dist / self.step_size), 2)
        points = np.linspace(start, goal, n_points)
        return [[int(round(p[0])), int(round(p[1]))] for p in points]
