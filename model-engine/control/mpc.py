"""
滚动时域优化 (MPC) — 系统"大脑"


原理:
  每个时间步:
    1. 获取当前状态 (位置 + 气象 + 风险)
    2. 预测未来 N 步的风险场演变
    3. 在预测时域内求解最优路径
    4. 只执行第一步
    5. 下一个时间步重复


优势:
  - 可应对突发天气变化
  - 滚动优化天然支持动态重规划
  - 计算量可控 (时域长度 N)
"""
import logging
import time
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

from path_planning.cost_function import RiskCostFunction, CostConfig
from path_planning.planner import GPRPathPlanner

logger = logging.getLogger(__name__)


class MPCStatus(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REACHED = "reached"
    FAILED = "failed"
    EMERGENCY = "emergency"


@dataclass
class MPCConfig:
    """MPC 配置"""
    horizon_steps: int = 6             # 预测时域 (每步=10min → 1小时)
    step_interval_s: int = 600         # 10分钟
    replan_frequency: int = 1          # 每几步重规划一次
    max_iterations: int = 100

    # 约束
    max_speed: float = 15.0            # m/s
    max_acceleration: float = 2.0      # m/s²
    max_climb_rate: float = 3.0        # m/s
    min_altitude: float = 50.0         # m
    max_altitude: float = 500.0        # m

    # 终止条件
    arrival_threshold_km: float = 0.5
    battery_warning_level: float = 0.2
    emergency_timeout_s: float = 30.0

    # 优化参数
    optimization_iters: int = 50
    convergence_tolerance: float = 0.01

    # 预测模型
    wind_persistence_weight: float = 0.7   # 持续性假设权重 (未来风场 ≈ 当前风场 × 权重)


@dataclass
class UAVState:
    """无人机当前状态"""
    x: float                # km
    y: float
    z: float                # m 高度
    vx: float = 0.0         # m/s
    vy: float = 0.0
    heading: float = 0.0    # rad
    battery: float = 1.0    # 0-1
    status: MPCStatus = MPCStatus.IDLE


@dataclass
class MPCTrajectory:
    """MPC 规划的轨迹"""
    waypoints: List[np.ndarray]     # 未来路径
    costs: List[float]              # 每步代价
    total_cost: float
    expected_arrival_s: float
    risk_profile: List[float]       # 风险变化


class ModelPredictiveController:
    """
    滚动时域优化控制器

    流程:
      1. init(uav_state, goal, env)
      2. 循环 loop():
           a. predict_future_state()
           b. predict_future_risk()
           c. optimize_trajectory()
           d. execute_first_step()
           e. wait_until_next_step()
    """

    def __init__(self, config: Optional[MPCConfig] = None,
                 cost_config: Optional[CostConfig] = None):
        self.config = config or MPCConfig()
        self.cost_fn = RiskCostFunction(cost_config)
        self.planner = GPRPathPlanner()

        self.uav: Optional[UAVState] = None
        self.goal: Optional[Tuple[float, float]] = None
        self.trajectory: Optional[MPCTrajectory] = None
        self.start_time: float = 0.0
        self.iteration: int = 0

        # 预测缓存
        self._predicted_risk: List[np.ndarray] = []
        self._predicted_wind: List[Tuple[np.ndarray, np.ndarray]] = []

    def init(self, uav: UAVState, goal: Tuple[float, float]):
        """初始化 MPC"""
        self.uav = uav
        self.goal = goal
        self.start_time = time.time()
        self.iteration = 0
        uav.status = MPCStatus.PLANNING
        logger.info(f"[MPC] 初始化: 起点({uav.x:.1f}, {uav.y:.1f}) → 目标({goal[0]:.1f}, {goal[1]:.1f})")

    def loop(self, risk_map: np.ndarray, wind_u: np.ndarray,
             wind_v: np.ndarray, tke: Optional[np.ndarray] = None,
             restricted: Optional[np.ndarray] = None,
             precipitation: Optional[np.ndarray] = None) -> MPCStatus:
        """
        MPC 主循环 — 一次重规划

        Args:
            全部环境场 (随时间更新)
        Returns:
            当前状态
        """
        if self.uav is None or self.goal is None:
            raise RuntimeError("MPC 未初始化")

        self.iteration += 1
        c = self.config

        # 0. 检查终止/紧急条件
        status = self._check_termination(risk_map)
        if status in (MPCStatus.REACHED, MPCStatus.FAILED, MPCStatus.EMERGENCY):
            self.uav.status = status
            return status

        # 1. 预测未来环境场 (持续性假设 + 衰减)
        horizon = c.horizon_steps
        self._predict_environment(risk_map, wind_u, wind_v, horizon)

        # 2. 预测未来无人机状态
        predicted_states = self._predict_states(horizon)

        # 3. 滚动优化: 在预测时域内求解最优轨迹
        traj = self._optimize_trajectory(
            predicted_states, horizon,
            tke, restricted, precipitation
        )
        self.trajectory = traj

        # 4. 执行第一步
        if traj.waypoints:
            self._execute_step(traj.waypoints[0])

        logger.info(f"[MPC] iter={self.iteration}, "
                    f"pos=({self.uav.x:.1f},{self.uav.y:.1f}), "
                    f"cost={traj.total_cost:.3f}, "
                    f"arrival={traj.expected_arrival_s:.0f}s")

        return MPCStatus.EXECUTING

    # ── 环境预测 ─────────────────────────────

    def _predict_environment(self, risk: np.ndarray,
                             wind_u: np.ndarray, wind_v: np.ndarray,
                             horizon: int):
        """预测未来 N 步的环境场 (持续性衰减假设)"""
        c = self.config
        self._predicted_risk = [risk]
        self._predicted_wind = [(wind_u, wind_v)]

        for step in range(1, horizon):
            decay = c.wind_persistence_weight ** step
            # 风险场随时间趋于均值 (不确定性增大)
            risk_next = risk * decay + risk.mean() * (1 - decay)
            risk_next += np.random.normal(0, 0.05 * risk.std(), risk.shape)
            self._predicted_risk.append(np.clip(risk_next, 0, 1))

            # 风场持续性衰减
            u_next = wind_u * decay
            v_next = wind_v * decay
            self._predicted_wind.append((u_next, v_next))

    def _predict_states(self, horizon: int) -> List[UAVState]:
        """预测未来状态 (匀速直线外推)"""
        if self.uav is None:
            return []

        states = [self.uav]
        for _ in range(horizon):
            last = states[-1]
            dt = self.config.step_interval_s
            next_state = UAVState(
                x=last.x + last.vx * dt / 1000,
                y=last.y + last.vy * dt / 1000,
                z=last.z,
                vx=last.vx, vy=last.vy, heading=last.heading,
                battery=last.battery - 0.02,  # 简化放电
                status=MPCStatus.PLANNING,
            )
            states.append(next_state)
        return states

    # ── 轨迹优化 ─────────────────────────────

    def _optimize_trajectory(self, predicted_states: List[UAVState],
                             horizon: int, tke, restricted,
                             precip) -> MPCTrajectory:
        """在预测时域内优化轨迹"""
        if self.uav is None or self.goal is None:
            return MPCTrajectory([], [], 0, 0, [])

        waypoints = []
        costs = []
        risk_profile = []

        # 在每步的预测环境场上做局部路径规划
        current_pos = np.array([self.uav.x, self.uav.y])

        for step in range(horizon):
            risk_step = self._predicted_risk[step] if step < len(
                self._predicted_risk) else self._predicted_risk[-1]
            wind_u_step, wind_v_step = (
                self._predicted_wind[step] if step < len(self._predicted_wind)
                else self._predicted_wind[-1]
            )

            # 每步的目标: 朝着最终目标移动，同时避开高风险
            progress = (step + 1) / horizon
            sub_goal = (
                current_pos[0] + (self.goal[0] - current_pos[0]) * progress * 0.5,
                current_pos[1] + (self.goal[1] - current_pos[1]) * progress * 0.5,
            )

            # 用 A* 规划局部路径
            local_path = self.planner._risk_aware_astar(
                risk_step, wind_u_step, wind_v_step,
                (int(current_pos[0] + 37.5), int(current_pos[1] + 37.5)),
                (int(sub_goal[0] + 37.5), int(sub_goal[1] + 37.5)),
            )

            if local_path and len(local_path) > 1:
                # 只取第一步
                next_wp = local_path[min(3, len(local_path) - 1)]
                waypoints.append(np.array([next_wp[0] - 37.5, next_wp[1] - 37.5]))
                current_pos = waypoints[-1]

                # 计算代价
                p = waypoints[-1]
                gx, gy = int(p[0] + 37.5), int(p[1] + 37.5)
                gx = np.clip(gx, 0, risk_step.shape[0] - 1)
                gy = np.clip(gy, 0, risk_step.shape[1] - 1)
                risk_profile.append(float(risk_step[gx, gy]))

                pred_state = (predicted_states[step]
                              if step < len(predicted_states)
                              else predicted_states[-1])

                cost = self.cost_fn.edge_cost(
                    np.array([pred_state.y + 37.5, pred_state.x + 37.5]),
                    np.array(next_wp, dtype=float), wind_u_step, wind_v_step,
                    risk_step, tke, restricted, precip,
                )
                costs.append(cost)

        total_cost = sum(costs)
        dist_remaining = np.sqrt(
            (current_pos[0] - self.goal[0])**2
            + (current_pos[1] - self.goal[1])**2
        )
        eta = dist_remaining / 15 * 3600  # 15m/s 巡航

        return MPCTrajectory(
            waypoints=waypoints, costs=costs, total_cost=total_cost,
            expected_arrival_s=eta, risk_profile=risk_profile,
        )

    def _execute_step(self, waypoint: np.ndarray):
        """执行第一步"""
        if self.uav is None:
            return
        self.uav.status = MPCStatus.EXECUTING
        # 更新位置
        dx = waypoint[0] - self.uav.x
        dy = waypoint[1] - self.uav.y
        dist = np.sqrt(dx**2 + dy**2)
        if dist > 0.1:
            self.uav.vx = dx / max(dist, 0.001) * self.config.max_speed
            self.uav.vy = dy / max(dist, 0.001) * self.config.max_speed
            self.uav.heading = np.arctan2(dy, dx)
        self.uav.x = waypoint[0]
        self.uav.y = waypoint[1]
        self.uav.battery -= 0.01

    # ── 检查 ─────────────────────────────────

    def _check_termination(self, risk_map: np.ndarray) -> MPCStatus:
        """检查是否到达或需要紧急处理"""
        if self.uav is None or self.goal is None:
            return MPCStatus.FAILED

        dist_to_goal = np.sqrt(
            (self.uav.x - self.goal[0])**2
            + (self.uav.y - self.goal[1])**2
        )
        if dist_to_goal < self.config.arrival_threshold_km:
            return MPCStatus.REACHED

        if self.uav.battery < self.config.battery_warning_level:
            return MPCStatus.EMERGENCY

        if self.iteration >= self.config.max_iterations:
            return MPCStatus.FAILED

        # 当前位置是否在禁飞区
        if risk_map is not None:
            gx = int(np.clip(self.uav.x + 37.5, 0, risk_map.shape[0] - 1))
            gy = int(np.clip(self.uav.y + 37.5, 0, risk_map.shape[1] - 1))
            if risk_map[gx, gy] > 0.95:
                return MPCStatus.EMERGENCY

        return MPCStatus.IDLE
