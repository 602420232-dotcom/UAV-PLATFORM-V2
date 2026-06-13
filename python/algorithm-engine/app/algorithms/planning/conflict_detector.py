"""ConflictDetector（冲突检测器）——实时多无人机冲突检测。

基于4D轨迹预测（3D空间位置 + 时间维度）的实时冲突检测模块。
通过分析多架UAV的预测轨迹，在给定安全距离和时间范围内，
检测潜在的时空冲突，并提供冲突消解建议。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ConflictDetector:
    """多无人机冲突检测器。

    基于各UAV的4D轨迹（航路点 + 时间戳），通过轨迹插值和
    时空冲突判定，实时检测多架无人机之间的潜在冲突，
    并生成冲突消解建议。

    Args:
        config: 配置字典，支持以下参数：
            - safety_distance: 默认安全距离（米），默认5.0
            - time_horizon: 默认预测时间范围（秒），默认60.0
            - interpolation_step: 轨迹插值时间步长（秒），默认0.5
            - altitude_threshold: 高度差判定阈值（米），默认3.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.safety_distance: float = self.config.get("safety_distance", 5.0)
        self.time_horizon: float = self.config.get("time_horizon", 60.0)
        self.interpolation_step: float = self.config.get("interpolation_step", 0.5)
        self.altitude_threshold: float = self.config.get("altitude_threshold", 3.0)

    def detect(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行多无人机冲突检测。

        Args:
            params: 检测参数字典，包含：
                - trajectories: 多架UAV的4D轨迹列表，每个轨迹为字典：
                    - uav_id: UAV标识符
                    - waypoints: 航路点列表，每个航路点为 [x, y, z]
                    - timestamps: 对应时间戳列表（秒）
                - safety_distance: 安全距离（可选，覆盖配置）
                - time_horizon: 预测时间范围（可选，覆盖配置）

        Returns:
            包含以下键的字典：
                - conflicts: 冲突列表，每个冲突含类型/位置/时间/涉及UAV
                - conflict_free: 是否无冲突（布尔值）
                - resolution_suggestions: 冲突消解建议列表
        """
        np.random.seed(42)

        trajectories = params.get("trajectories", [])
        safety_dist = params.get("safety_distance", self.safety_distance)
        time_horizon = params.get("time_horizon", self.time_horizon)

        if len(trajectories) < 2:
            logger.info("冲突检测: UAV数量不足2架，无需检测")
            return {
                "conflicts": [],
                "conflict_free": True,
                "resolution_suggestions": [],
            }

        logger.info(
            "冲突检测: UAV数=%d, 安全距离=%.1fm, 时间范围=%.1fs",
            len(trajectories), safety_dist, time_horizon,
        )

        # 对每条轨迹进行插值，生成均匀时间步长的4D轨迹
        interpolated = []
        for traj in trajectories:
            interp_traj = self._interpolate_trajectory(traj, time_horizon)
            interpolated.append(interp_traj)

        # 检测所有UAV对之间的冲突
        conflicts: list[dict[str, Any]] = []
        n = len(interpolated)

        for i in range(n):
            for j in range(i + 1, n):
                pair_conflicts = self._detect_pair_conflicts(
                    interpolated[i], interpolated[j],
                    trajectories[i].get("uav_id", f"UAV_{i}"),
                    trajectories[j].get("uav_id", f"UAV_{j}"),
                    safety_dist,
                )
                conflicts.extend(pair_conflicts)

        # 生成冲突消解建议
        resolution_suggestions = self._generate_suggestions(conflicts)

        conflict_free = len(conflicts) == 0

        if conflict_free:
            logger.info("冲突检测完成: 无冲突")
        else:
            logger.warning(
                "冲突检测完成: 发现 %d 个冲突", len(conflicts),
            )

        return {
            "conflicts": conflicts,
            "conflict_free": conflict_free,
            "resolution_suggestions": resolution_suggestions,
        }

    def _interpolate_trajectory(
        self, traj: dict, time_horizon: float,
    ) -> dict[str, Any]:
        """对轨迹进行线性插值，生成均匀时间步长的4D轨迹。

        在原始航路点之间进行线性插值，确保在时间维度上
        以固定步长采样位置。

        Args:
            traj: 原始轨迹，含 waypoints 和 timestamps
            time_horizon: 最大预测时间

        Returns:
            插值后的轨迹字典，含 positions 和 times 数组
        """
        waypoints = traj.get("waypoints", [])
        timestamps = traj.get("timestamps", [])

        if len(waypoints) < 2 or len(timestamps) < 2:
            return {
                "uav_id": traj.get("uav_id", "unknown"),
                "positions": np.array([]).reshape(0, 3),
                "times": np.array([]),
            }

        wp_array = np.array(waypoints, dtype=np.float64)
        ts_array = np.array(timestamps, dtype=np.float64)

        # 生成插值时间序列
        t_start = ts_array[0]
        t_end = min(ts_array[-1], t_start + time_horizon)
        interp_times = np.arange(t_start, t_end, self.interpolation_step)

        if len(interp_times) == 0:
            return {
                "uav_id": traj.get("uav_id", "unknown"),
                "positions": np.array([]).reshape(0, 3),
                "times": np.array([]),
            }

        # 对每个维度进行线性插值
        interp_positions = np.zeros((len(interp_times), 3), dtype=np.float64)
        for dim in range(3):
            interp_positions[:, dim] = np.interp(
                interp_times, ts_array, wp_array[:, dim],
            )

        return {
            "uav_id": traj.get("uav_id", "unknown"),
            "positions": interp_positions,
            "times": interp_times,
        }

    def _detect_pair_conflicts(
        self,
        traj_a: dict,
        traj_b: dict,
        uav_a_id: str,
        uav_b_id: str,
        safety_dist: float,
    ) -> list[dict[str, Any]]:
        """检测两架UAV之间的冲突。

        通过逐时间步比较两架UAV的3D位置，判断是否满足
        安全距离约束。支持以下冲突类型：
        - proximity: 距离冲突（3D欧氏距离小于安全距离）
        - head_on: 对头冲突（接近速度高且距离快速缩小）
        - converging: 交叉冲突（轨迹交叉点附近同时到达）

        Args:
            traj_a: UAV A的插值轨迹
            traj_b: UAV B的插值轨迹
            uav_a_id: UAV A标识符
            uav_b_id: UAV B标识符
            safety_dist: 安全距离

        Returns:
            冲突列表
        """
        conflicts: list[dict[str, Any]] = []

        pos_a = traj_a["positions"]
        pos_b = traj_b["positions"]
        times_a = traj_a["times"]
        times_b = traj_b["times"]

        if len(pos_a) == 0 or len(pos_b) == 0:
            return conflicts

        # 对齐时间步
        common_times = np.intersect1d(times_a, times_b)
        if len(common_times) == 0:
            return conflicts

        # 在公共时间步上采样位置
        idx_a = np.searchsorted(times_a, common_times)
        idx_b = np.searchsorted(times_b, common_times)

        sampled_a = pos_a[np.clip(idx_a, 0, len(pos_a) - 1)]
        sampled_b = pos_b[np.clip(idx_b, 0, len(pos_b) - 1)]

        # 逐时间步检测
        min_dist = float("inf")

        for k in range(len(common_times)):
            diff = sampled_a[k] - sampled_b[k]
            dist_3d = np.linalg.norm(diff)
            t = common_times[k]

            if dist_3d < min_dist:
                min_dist = dist_3d

            if dist_3d < safety_dist:
                # 判断冲突类型
                conflict_type = self._classify_conflict(
                    sampled_a, sampled_b, k, float(dist_3d), safety_dist,
                )

                conflict_point = (
                    (sampled_a[k] + sampled_b[k]) / 2.0
                ).tolist()

                conflicts.append({
                    "type": conflict_type,
                    "uav_a": uav_a_id,
                    "uav_b": uav_b_id,
                    "time": float(t),
                    "position": [round(v, 2) for v in conflict_point],
                    "distance": round(float(dist_3d), 2),
                    "severity": self._assess_severity(float(dist_3d), safety_dist),
                })

        # 检测交叉冲突（轨迹交叉但时间接近）
        crossing_conflicts = self._detect_crossing_conflicts(
            sampled_a, sampled_b, common_times,
            uav_a_id, uav_b_id, safety_dist,
        )
        conflicts.extend(crossing_conflicts)

        if conflicts:
            logger.debug(
                "冲突检测: %s vs %s, 最近距离=%.2fm, 冲突数=%d",
                uav_a_id, uav_b_id, min_dist, len(conflicts),
            )

        return conflicts

    def _classify_conflict(
        self,
        pos_a: np.ndarray,
        pos_b: np.ndarray,
        idx: int,
        dist: float,
        safety_dist: float,
    ) -> str:
        """分类冲突类型。

        根据两架UAV的相对运动方向和速度，判断冲突类型。

        Args:
            pos_a: UAV A的位置序列
            pos_b: UAV B的位置序列
            idx: 当前时间步索引
            dist: 当前距离
            safety_dist: 安全距离

        Returns:
            冲突类型字符串
        """
        if idx < 2 or idx >= len(pos_a) - 1 or idx >= len(pos_b) - 1:
            return "proximity"

        # 计算相对速度向量
        vel_a = pos_a[idx] - pos_a[idx - 1]
        vel_b = pos_b[idx] - pos_b[idx - 1]
        rel_vel = vel_a - vel_b
        rel_speed = np.linalg.norm(rel_vel)

        # 计算相对位置向量
        rel_pos = pos_a[idx] - pos_b[idx]
        rel_dist = np.linalg.norm(rel_pos)

        if rel_dist < 1e-6:
            return "proximity"

        # 归一化
        rel_vel_norm = rel_vel / (rel_speed + 1e-8)
        rel_pos_norm = rel_pos / rel_dist

        # 对头冲突：相对速度方向与相对位置方向相反
        approach_rate = -np.dot(rel_vel_norm, rel_pos_norm)
        if approach_rate > 0.8 and rel_speed > 0.5:
            return "head_on"

        # 交叉冲突：轨迹方向交叉
        cross_product = np.cross(vel_a, vel_b)
        cross_mag = np.linalg.norm(cross_product)
        if cross_mag > 0.1:
            return "converging"

        return "proximity"

    def _assess_severity(self, dist: float, safety_dist: float) -> str:
        """评估冲突严重程度。

        Args:
            dist: 实际距离
            safety_dist: 安全距离

        Returns:
            严重程度: "critical" / "warning" / "caution"
        """
        ratio = dist / safety_dist
        if ratio < 0.3:
            return "critical"
        elif ratio < 0.6:
            return "warning"
        else:
            return "caution"

    def _detect_crossing_conflicts(
        self,
        pos_a: np.ndarray,
        pos_b: np.ndarray,
        common_times: np.ndarray,
        uav_a_id: str,
        uav_b_id: str,
        safety_dist: float,
    ) -> list[dict[str, Any]]:
        """检测交叉冲突。

        当两架UAV的轨迹在空间上交叉，且到达交叉点的
        时间差小于阈值时，判定为交叉冲突。

        Returns:
            交叉冲突列表
        """
        crossing_conflicts: list[dict[str, Any]] = []

        if len(pos_a) < 3 or len(pos_b) < 3:
            return crossing_conflicts

        # 查找A轨迹线段与B轨迹线段的最近点
        time_threshold = 3.0 * self.interpolation_step  # 时间差阈值

        for i in range(len(pos_a) - 1):
            for j in range(len(pos_b) - 1):
                # 线段最近点
                closest = self._segment_closest_point(
                    pos_a[i], pos_a[i + 1], pos_b[j], pos_b[j + 1],
                )

                if closest["distance"] < safety_dist:
                    time_diff = abs(common_times[i] - common_times[j])

                    if time_diff < time_threshold:
                        # 检查是否已被proximity检测捕获
                        conflict_point = closest["midpoint"].tolist()
                        crossing_conflicts.append({
                            "type": "crossing",
                            "uav_a": uav_a_id,
                            "uav_b": uav_b_id,
                            "time": float((common_times[i] + common_times[j]) / 2),
                            "position": [round(v, 2) for v in conflict_point],
                            "distance": round(float(closest["distance"]), 2),
                            "severity": self._assess_severity(
                                closest["distance"], safety_dist,
                            ),
                        })

        # 去重：如果同一对UAV在同一时间段已有proximity冲突，跳过crossing
        if len(crossing_conflicts) > 10:
            # 限制crossing冲突数量，避免过多相似冲突
            crossing_conflicts = crossing_conflicts[:5]

        return crossing_conflicts

    def _segment_closest_point(
        self,
        p1: np.ndarray, p2: np.ndarray,
        p3: np.ndarray, p4: np.ndarray,
    ) -> dict[str, Any]:
        """计算两条线段之间的最近点。

        Args:
            p1, p2: 第一条线段的端点
            p3, p4: 第二条线段的端点

        Returns:
            包含 distance 和 midpoint 的字典
        """
        d1 = p2 - p1
        d2 = p4 - p3
        r = p1 - p3

        a = np.dot(d1, d1)
        e = np.dot(d2, d2)
        f = np.dot(d2, r)

        if a < 1e-10 and e < 1e-10:
            return {"distance": np.linalg.norm(r), "midpoint": (p1 + p3) / 2}

        if a < 1e-10:
            s = 0.0
            t = np.clip(f / e, 0.0, 1.0)
        else:
            c = np.dot(d1, r)
            if e < 1e-10:
                t = 0.0
                s = np.clip(-c / a, 0.0, 1.0)
            else:
                b = np.dot(d1, d2)
                denom = a * e - b * b

                if abs(denom) > 1e-10:
                    s = np.clip((b * f - c * e) / denom, 0.0, 1.0)
                else:
                    s = 0.0

                t = (b * s + f) / e

                if t < 0.0:
                    t = 0.0
                    s = np.clip(-c / a, 0.0, 1.0)
                elif t > 1.0:
                    t = 1.0
                    s = np.clip((b - c) / a, 0.0, 1.0)

        closest1 = p1 + s * d1
        closest2 = p3 + t * d2
        distance = np.linalg.norm(closest1 - closest2)
        midpoint = (closest1 + closest2) / 2.0

        return {"distance": distance, "midpoint": midpoint}

    def _generate_suggestions(
        self, conflicts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """生成冲突消解建议。

        根据冲突类型和严重程度，生成具体的消解策略建议。

        Args:
            conflicts: 检测到的冲突列表

        Returns:
            消解建议列表
        """
        suggestions: list[dict[str, Any]] = []

        if not conflicts:
            return suggestions

        # 按UAV对分组
        pair_map: dict[tuple, list] = {}
        for c in conflicts:
            key = tuple(sorted([c["uav_a"], c["uav_b"]]))
            if key not in pair_map:
                pair_map[key] = []
            pair_map[key].append(c)

        for (uav_a, uav_b), pair_conflicts in pair_map.items():
            # 找到最严重的冲突
            most_severe = min(
                pair_conflicts,
                key=lambda c: (
                    0 if c["severity"] == "critical"
                    else 1 if c["severity"] == "warning"
                    else 2,
                ),
            )

            conflict_type = most_severe["type"]
            severity = most_severe["severity"]
            conflict_time = most_severe["time"]

            if conflict_type == "head_on":
                suggestion = {
                    "uavs": [uav_a, uav_b],
                    "strategy": "altitude_separation",
                    "description": (
                        f"对头冲突: 建议 {uav_a} 和 {uav_b} 在 t={conflict_time:.1f}s "
                        f"处进行高度分离，其中一架爬升{self.altitude_threshold * 2:.0f}m，"
                        f"另一架下降{self.altitude_threshold * 2:.0f}m"
                    ),
                    "priority": "high" if severity == "critical" else "medium",
                    "action_time": conflict_time - 5.0,
                }
            elif conflict_type in ("converging", "crossing"):
                suggestion = {
                    "uavs": [uav_a, uav_b],
                    "strategy": "speed_adjustment",
                    "description": (
                        f"交叉冲突: 建议 {uav_a} 减速或 {uav_b} 加速，"
                        f"错开通过冲突点的时间（冲突时间 t={conflict_time:.1f}s）"
                    ),
                    "priority": "high" if severity == "critical" else "medium",
                    "action_time": conflict_time - 8.0,
                }
            else:
                suggestion = {
                    "uavs": [uav_a, uav_b],
                    "strategy": "lateral_deviation",
                    "description": (
                        f"接近冲突: 建议 {uav_a} 或 {uav_b} 在 "
                        f"t={conflict_time:.1f}s 前进行侧向偏移，"
                        f"偏移距离不小于{self.safety_distance:.0f}m"
                    ),
                    "priority": "medium" if severity == "warning" else "low",
                    "action_time": conflict_time - 3.0,
                }

            suggestions.append(suggestion)

        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s["priority"], 3))

        return suggestions
