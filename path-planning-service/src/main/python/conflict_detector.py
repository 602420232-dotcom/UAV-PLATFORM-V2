#!/usr/bin/env python3
"""
多无人机路径冲突检测与消解

支持:
- 时空冲突检测 (4D)
- 优先级消解
- 路径调整建议
"""
from typing import List, Tuple, Optional, Dict
import math
import logging

logger = logging.getLogger(__name__)


class ConflictPoint:
    """冲突点"""
    def __init__(self, time: float, position: Tuple[float, float],
                 drone_ids: Tuple[str, str], separation: float):
        self.time = time
        self.position = position
        self.drone_ids = drone_ids
        self.separation = separation

    def __repr__(self) -> str:
        return (f"ConflictPoint(time={self.time:.1f}, pos={self.position}, "
                f"drones={self.drone_ids}, sep={self.separation:.1f})")


class ConflictDetector:
    """
    多无人机路径冲突检测器

    检测多个无人机路径之间的时空冲突，并给出消解建议。
    """

    def __init__(self, min_separation: float = 5.0, time_step: float = 1.0):
        """
        Args:
            min_separation: 最小安全间距（米）
            time_step: 时间步长（秒）
        """
        self.min_separation = min_separation
        self.time_step = time_step

    def detect_conflicts(self,
                         drone_paths: Dict[str, List[Tuple[float, float]]],
                         drone_speeds: Optional[Dict[str, float]] = None) -> List[ConflictPoint]:
        """
        检测多无人机路径间的时空冲突

        Args:
            drone_paths: 无人机ID到路径点列表的映射
                        路径点格式: [(x1, y1), (x2, y2), ...]
            drone_speeds: 无人机ID到速度的映射，None则默认10m/s

        Returns:
            冲突点列表
        """
        conflicts = []
        drone_ids = list(drone_paths.keys())

        # 遍历所有无人机对
        for i in range(len(drone_ids)):
            for j in range(i + 1, len(drone_ids)):
                id_a = drone_ids[i]
                id_b = drone_ids[j]
                path_a = drone_paths[id_a]
                path_b = drone_paths[id_b]

                if not path_a or not path_b:
                    continue

                # 采样路径点进行时空冲突检测
                max_len = min(len(path_a), len(path_b))
                for t in range(max_len):
                    pos_a = path_a[t]
                    pos_b = path_b[t]

                    # 计算距离
                    separation = math.sqrt(
                        (pos_a[0] - pos_b[0]) ** 2 +
                        (pos_a[1] - pos_b[1]) ** 2
                    )

                    if separation < self.min_separation:
                        conflict = ConflictPoint(
                            time=t * self.time_step,
                            position=(
                                (pos_a[0] + pos_b[0]) / 2,
                                (pos_a[1] + pos_b[1]) / 2
                            ),
                            drone_ids=(id_a, id_b),
                            separation=separation
                        )
                        conflicts.append(conflict)

        return conflicts

    def resolve_conflicts(self,
                          conflicts: List[ConflictPoint],
                          drone_priorities: Optional[Dict[str, int]] = None) -> List[Dict]:
        """
        消解冲突，给出调整建议

        Args:
            conflicts: 冲突点列表
            drone_priorities: 无人机ID到优先级的映射（数字越小优先级越高）

        Returns:
            调整建议列表
        """
        suggestions = []
        handled = set()

        for conflict in conflicts:
            key = tuple(sorted(conflict.drone_ids))
            if key in handled:
                continue

            id_a, id_b = conflict.drone_ids

            # 确定优先级
            if drone_priorities:
                pri_a = drone_priorities.get(id_a, 0)
                pri_b = drone_priorities.get(id_b, 0)
                yield_drone = id_b if pri_a <= pri_b else id_a
                priority_drone = id_a if yield_drone == id_b else id_b
            else:
                yield_drone = id_b
                priority_drone = id_a

            suggestion = {
                'conflict_time': conflict.time,
                'conflict_position': conflict.position,
                'separation': conflict.separation,
                'priority_drone': priority_drone,
                'yield_drone': yield_drone,
                'suggestion': f"无人机 {yield_drone} 在时间 {conflict.time:.1f}s 时减速或绕行，"
                              f"让无人机 {priority_drone} 优先通过",
                'required_separation': self.min_separation - conflict.separation,
                'adjustment_options': [
                    f"{yield_drone} 提前减速等待 {self.time_step * 2:.0f}s",
                    f"{yield_drone} 向右偏移 {self.min_separation - conflict.separation:.1f}m",
                ]
            }
            suggestions.append(suggestion)
            handled.add(key)

        return suggestions

    def analyze_formation(self,
                          drone_paths: Dict[str, List[Tuple[float, float]]]) -> Dict:
        """
        分析编队保持情况

        Args:
            drone_paths: 无人机ID到路径点列表的映射

        Returns:
            编队分析结果
        """
        if len(drone_paths) < 2:
            return {'error': '需要至少2架无人机进行编队分析'}

        drone_ids = list(drone_paths.keys())
        separations_over_time = []

        max_len = min(len(p) for p in drone_paths.values())
        for t in range(max_len):
            time_seps = []
            for i in range(len(drone_ids)):
                for j in range(i + 1, len(drone_ids)):
                    pos_a = drone_paths[drone_ids[i]][t]
                    pos_b = drone_paths[drone_ids[j]][t]
                    sep = math.sqrt(
                        (pos_a[0] - pos_b[0]) ** 2 +
                        (pos_a[1] - pos_b[1]) ** 2
                    )
                    time_seps.append(sep)
            if time_seps:
                separations_over_time.append({
                    'time': t * self.time_step,
                    'mean': sum(time_seps) / len(time_seps),
                    'min': min(time_seps),
                    'max': max(time_seps),
                    'std': math.sqrt(sum((s - sum(time_seps)/len(time_seps))**2 for s in time_seps) / len(time_seps))
                })

        avg_seps = [s['mean'] for s in separations_over_time]
        return {
            'drone_count': len(drone_ids),
            'analysis_duration': max_len * self.time_step if max_len > 0 else 0,
            'average_separation': sum(avg_seps) / len(avg_seps) if avg_seps else 0,
            'min_separation': min(sep['min'] for sep in separations_over_time) if separations_over_time else 0,
            'max_separation': max(sep['max'] for sep in separations_over_time) if separations_over_time else 0,
            'separation_stability': min(sep['std'] for sep in separations_over_time) if separations_over_time else 0,
            'time_points': len(separations_over_time),
            'details': separations_over_time
        }
