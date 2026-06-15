"""三次样条插值路径规划算法。

使用三次样条函数对路径控制点进行平滑插值。
生成通过所有控制点的二阶连续可导平滑曲线，
适用于需要生成平滑飞行轨迹的场景。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class CubicSplinePlanner:
    """三次样条插值路径规划器。

    给定一组路径控制点，使用三次样条函数生成
    通过所有控制点的平滑曲线。保证：
    - 插值性：曲线通过所有控制点
    - 一阶连续：曲线在控制点处切线连续
    - 二阶连续：曲线在控制点处曲率连续

    Args:
        config: 配置字典，支持以下参数：
            - n_interpolation: 每段插值点数，默认20
            - boundary_condition: 边界条件类型，默认"natural"（自然边界）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.n_interpolation: int = self.config.get("n_interpolation", 20)
        self.boundary_condition: str = self.config.get("boundary_condition", "natural")

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行三次样条插值路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - waypoints: 中间路径控制点列表（可选）

        Returns:
            包含 path（平滑路径点列表）和 cost（路径长度）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        waypoints = params.get("waypoints", [])

        logger.info(
            "三次样条规划: 起点=%s, 终点=%s, 控制点=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            len(waypoints) + 2,
        )

        rows, cols = grid_size

        # 构建控制点序列
        if waypoints and len(waypoints) > 0:
            wp_array = np.array(waypoints, dtype=float)
            control_points = np.vstack([start.reshape(1, 2), wp_array, goal.reshape(1, 2)])
        else:
            control_points = np.array([start, goal], dtype=float)

        n = len(control_points)

        if n < 2:
            return {"path": [start.tolist()], "cost": 0.0}

        if n == 2:
            # 两点之间直接线性插值
            path = self._linear_interpolation(control_points[0], control_points[1])
            cost = float(np.linalg.norm(control_points[1] - control_points[0]))
            return {"path": path, "cost": cost}

        # 计算参数化变量（累积弧长参数化）
        t = self._compute_parameters(control_points)

        # 分别对x和y方向进行三次样条插值
        x_coords = control_points[:, 0]
        y_coords = control_points[:, 1]

        spline_x = self._compute_cubic_spline(t, x_coords)
        spline_y = self._compute_cubic_spline(t, y_coords)

        # 采样样条曲线
        path = self._sample_spline(spline_x, spline_y, t)

        # 计算路径代价
        cost = self._path_cost(path)

        logger.info(
            "三次样条规划完成: 代价=%.2f, 路径点=%d",
            cost,
            len(path),
        )
        return {
            "path": path,
            "cost": cost,
            "n_control_points": n,
            "n_spline_points": len(path),
        }

    def _compute_parameters(self, points: np.ndarray) -> np.ndarray:
        """计算累积弧长参数。"""
        n = len(points)
        t = np.zeros(n)
        for i in range(1, n):
            t[i] = t[i - 1] + float(np.linalg.norm(points[i] - points[i - 1]))
        # 归一化到[0, 1]
        if t[-1] > 1e-6:
            t = t / t[-1]
        return t

    def _compute_cubic_spline(
        self,
        t: np.ndarray,
        y: np.ndarray,
    ) -> list[tuple[float, float, float, float]]:
        """计算三次样条系数。

        返回每段的系数列表 [(a_i, b_i, c_i, d_i), ...]
        其中 S_i(t) = a_i + b_i*(t-t_i) + c_i*(t-t_i)^2 + d_i*(t-t_i)^3
        """
        n = len(t) - 1
        h = np.diff(t)

        # 构建三对角方程组求解二阶导数
        # 自然边界条件：M[0] = M[n] = 0
        A = np.zeros((n + 1, n + 1))
        b = np.zeros(n + 1)

        for i in range(1, n):
            A[i, i - 1] = h[i - 1]
            A[i, i] = 2 * (h[i - 1] + h[i])
            A[i, i + 1] = h[i]
            b[i] = 3 * (
                (y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1]
            )

        if self.boundary_condition == "natural":
            A[0, 0] = 1.0
            A[n, n] = 1.0
        else:
            # 夹持边界条件
            A[0, 0] = 2 * h[0]
            A[0, 1] = h[0]
            b[0] = 3 * (y[1] - y[0]) / h[0]
            A[n, n - 1] = h[n - 1]
            A[n, n] = 2 * h[n - 1]
            b[n] = 3 * (y[n] - y[n - 1]) / h[n - 1]

        # 求解三对角方程组（Thomas算法）
        M = self._solve_tridiagonal(A, b)

        # 计算每段的样条系数
        splines = []
        for i in range(n):
            a_i = y[i]
            b_i = (y[i + 1] - y[i]) / h[i] - h[i] * (2 * M[i] + M[i + 1]) / 3
            c_i = M[i]
            d_i = (M[i + 1] - M[i]) / (3 * h[i])
            splines.append((a_i, b_i, c_i, d_i))

        return splines

    def _solve_tridiagonal(
        self,
        A: np.ndarray,
        b: np.ndarray,
    ) -> np.ndarray:
        """Thomas算法求解三对角方程组。"""
        n = len(b)
        c = np.zeros(n)
        d = np.zeros(n)
        x = np.zeros(n)

        # 前向消元
        c[0] = A[0, 1] / A[0, 0] if A[0, 0] != 0 else 0
        d[0] = b[0] / A[0, 0] if A[0, 0] != 0 else 0

        for i in range(1, n):
            denom = A[i, i] - A[i, i - 1] * c[i - 1]
            if abs(denom) < 1e-12:
                denom = 1e-12
            if i < n - 1:
                c[i] = A[i, i + 1] / denom
            d[i] = (b[i] - A[i, i - 1] * d[i - 1]) / denom

        # 回代
        x[n - 1] = d[n - 1]
        for i in range(n - 2, -1, -1):
            x[i] = d[i] - c[i] * x[i + 1]

        return x

    def _sample_spline(
        self,
        spline_x: list[tuple],
        spline_y: list[tuple],
        t: np.ndarray,
    ) -> list[list[int]]:
        """采样样条曲线。"""
        path = []
        n_segments = len(spline_x)

        for i in range(n_segments):
            for j in range(self.n_interpolation):
                s = j / self.n_interpolation
                dt = t[i + 1] - t[i]
                local_t = s * dt

                a_x, b_x, c_x, d_x = spline_x[i]
                a_y, b_y, c_y, d_y = spline_y[i]

                px = a_x + b_x * local_t + c_x * local_t**2 + d_x * local_t**3
                py = a_y + b_y * local_t + c_y * local_t**2 + d_y * local_t**3

                path.append([int(round(px)), int(round(py))])

        # 添加最后一个点
        a_x, b_x, c_x, d_x = spline_x[-1]
        a_y, b_y, c_y, d_y = spline_y[-1]
        dt = t[-1] - t[-2]
        px = a_x + b_x * dt + c_x * dt**2 + d_x * dt**3
        py = a_y + b_y * dt + c_y * dt**2 + d_y * dt**3
        path.append([int(round(px)), int(round(py))])

        return path

    def _linear_interpolation(
        self,
        start: np.ndarray,
        goal: np.ndarray,
    ) -> list[list[int]]:
        """线性插值。"""
        dist = np.linalg.norm(goal - start)
        n_points = max(int(dist / 0.5), 2)
        points = np.linspace(start, goal, n_points)
        return [[int(round(p[0])), int(round(p[1]))] for p in points]

    def _path_cost(self, path: list) -> float:
        """计算路径代价。"""
        if len(path) < 2:
            return 0.0
        cost = 0.0
        for i in range(len(path) - 1):
            dx = path[i + 1][0] - path[i][0]
            dy = path[i + 1][1] - path[i][1]
            cost += math.sqrt(dx**2 + dy**2)
        return cost


# 需要math模块
import math
