"""
多机协同冲突消解算法


场景:
  N 架无人机在同一空域执行任务, 每架有自己的 MPC 规划。
  当多条路径在时空上发生冲突时, 需要协调。


方法:
  优先级分层 + 速度调节 + 高度分离


策略:
  1. 检测冲突: 检查任意两架无人机的时空轨迹是否相交
  2. 优先级分配: 紧急任务 > 普通配送 > 勘查
  3. 冲突消解:
     a. 低优先级调整速度 (快/慢通过)
     b. 高度层分离 (50m 间隔)
     c. 临时航向偏移
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import IntEnum


class MissionPriority(IntEnum):
    EMERGENCY = 0       # 最高: 应急救援
    CARGO = 1           # 中: 物流配送
    SURVEY = 2          # 低: 巡检/勘查
    OBSERVATION = 3     # 最低: 数据采集


@dataclass
class UAVAgent:
    """无人机代理"""
    id: str
    priority: MissionPriority = MissionPriority.CARGO
    x: float = 0.0
    y: float = 0.0
    z: float = 100.0           # 当前高度
    target_z: float = 100.0    # 目标高度
    speed: float = 10.0        # m/s
    heading: float = 0.0       # rad
    path: List[Tuple[float, float, float]] = field(default_factory=list)


@dataclass
class Conflict:
    """检测到的冲突"""
    uav_a: str
    uav_b: str
    time_to_conflict_s: float   # 距冲突还有多少秒
    conflict_pos: Tuple[float, float]  # 冲突位置 (x, y)
    horizontal_distance: float
    vertical_distance: float


@dataclass
class ConflictConfig:
    """冲突消解配置"""
    # 冲突检测
    horizontal_threshold_m: float = 200.0   # 水平距离 < 200m 算冲突
    vertical_threshold_m: float = 30.0      # 垂直距离 < 30m 算冲突
    time_horizon_s: float = 60.0            # 预测未来 60s

    # 消解参数
    altitude_separation_m: float = 50.0     # 高度层间隔
    speed_adjustment_max: float = 5.0       # m/s 最大速度调整
    course_deviation_deg: float = 15.0      # 最大航向偏移 (度)
    resolution_timeout_s: float = 10.0      # 消解超时

    # 优先级
    priority_time_advantage_s: float = 30.0  # 高优先级获得 30s 时间优势


class MultiUAVConflictResolver:
    """
    多机冲突消解器

    用法:
        resolver = MultiUAVConflictResolver()
        conflicts = resolver.detect_conflicts(agents)
        adjusted_agents = resolver.resolve(agents, conflicts)
    """

    def __init__(self, config: Optional[ConflictConfig] = None):
        self.config = config or ConflictConfig()

    # ── 冲突检测 ─────────────────────────────

    def detect_conflicts(self, agents: List[UAVAgent]) -> List[Conflict]:
        """
        检测所有无人机之间的潜在冲突

        Args:
            agents: 所有无人机状态

        Returns:
            conflicts: 按紧迫程度排序的冲突列表
        """
        conflicts = []
        n = len(agents)

        for i in range(n):
            for j in range(i + 1, n):
                a, b = agents[i], agents[j]
                conflict = self._check_pair(a, b)
                if conflict:
                    conflicts.append(conflict)

        # 按紧迫程度排序
        conflicts.sort(key=lambda c: c.time_to_conflict_s)
        return conflicts

    def _check_pair(self, a: UAVAgent, b: UAVAgent) -> Optional[Conflict]:
        """检查一对无人机"""
        # 位置差
        dx = a.x - b.x
        dy = a.y - b.y
        dz = a.z - b.z
        horizontal = np.sqrt(dx**2 + dy**2) * 1000  # km → m

        # 速度差
        dvx = a.speed * np.cos(a.heading) - b.speed * np.cos(b.heading)
        dvy = a.speed * np.sin(a.heading) - b.speed * np.sin(b.heading)
        rel_speed = np.sqrt(dvx**2 + dvy**2)

        # 估算碰撞时间
        time_to_conflict = (horizontal - self.config.horizontal_threshold_m) \
            / max(rel_speed, 0.1)

        if (horizontal < self.config.horizontal_threshold_m
                and abs(dz) < self.config.vertical_threshold_m
                and 0 < time_to_conflict < self.config.time_horizon_s):
            conflict_pos = ((a.x + b.x) / 2, (a.y + b.y) / 2)
            return Conflict(
                uav_a=a.id, uav_b=b.id,
                time_to_conflict_s=time_to_conflict,
                conflict_pos=conflict_pos,
                horizontal_distance=horizontal,
                vertical_distance=abs(dz),
            )
        return None

    # ── 冲突消解 ─────────────────────────────

    def resolve(self, agents: List[UAVAgent],
                conflicts: List[Conflict]) -> List[UAVAgent]:
        """
        消解所有冲突

        策略 (按优先级尝试):
          1. 高度层分离
          2. 速度调节
          3. 航向偏移
        """
        adjusted = {a.id: a for a in agents}
        resolved = set()

        for conflict in conflicts:
            pair_key = f"{conflict.uav_a}_{conflict.uav_b}"
            if pair_key in resolved:
                continue

            a = adjusted[conflict.uav_a]
            b = adjusted[conflict.uav_b]

            # 方法1: 高度层分离
            if self._resolve_by_altitude(a, b, conflict):
                resolved.add(pair_key)
                continue

            # 方法2: 速度调节
            if self._resolve_by_speed(a, b, conflict):
                resolved.add(pair_key)
                continue

            # 方法3: 航向偏移 (最后手段)
            self._resolve_by_course(a, b, conflict)
            resolved.add(pair_key)

        return list(adjusted.values())

    def _resolve_by_altitude(self, a: UAVAgent, b: UAVAgent,
                             conflict: Conflict) -> bool:
        """高度层分离"""
        c = self.config

        # 高优先级保持高度, 低优先级调整
        if a.priority < b.priority:
            high, low = a, b
        else:
            high, low = b, a

        # 检查能否调整低优先级高度
        new_z = high.z + c.altitude_separation_m
        if 50 <= new_z <= 500:
            low.target_z = new_z
            return True

        # 往下调
        new_z = high.z - c.altitude_separation_m
        if 50 <= new_z <= 500:
            low.target_z = new_z
            return True

        return False

    def _resolve_by_speed(self, a: UAVAgent, b: UAVAgent,
                          conflict: Conflict) -> bool:
        """速度调节"""
        c = self.config

        # 低优先级减速 / 高优先级加速
        if a.priority < b.priority:
            high, low = a, b
        else:
            high, low = b, a  # noqa: F841

        # 让低优先级减速让行
        low.speed = max(5, low.speed - c.speed_adjustment_max)
        return True

    def _resolve_by_course(self, a: UAVAgent, b: UAVAgent,
                           conflict: Conflict):
        """航向偏移"""
        c = self.config

        # 低优先级向右偏转
        if a.priority < b.priority:
            a.heading += np.radians(c.course_deviation_deg)
        else:
            b.heading += np.radians(c.course_deviation_deg)

    # ── 队形保持 ─────────────────────────────

    def maintain_formation(self, agents: List[UAVAgent],
                           formation: str = "line") -> List[UAVAgent]:
        """编队队形保持"""
        if len(agents) < 2:
            return agents

        if formation == "line":
            # 一字纵队: 间隔 100m
            for i in range(1, len(agents)):
                agents[i].x = agents[0].x - i * 0.1 * np.cos(agents[0].heading)
                agents[i].y = agents[0].y - i * 0.1 * np.sin(agents[0].heading)

        elif formation == "triangle":
            # 三角队形
            spacing = 0.1
            for i in range(1, min(len(agents), 4)):
                angle = np.pi / 6 * (i - 1) - np.pi / 6
                agents[i].x = agents[0].x + spacing * np.cos(agents[0].heading + angle)
                agents[i].y = agents[0].y + spacing * np.sin(agents[0].heading + angle)

        return agents
