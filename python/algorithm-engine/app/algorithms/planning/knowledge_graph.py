"""基于知识图谱的路径规划算法。

利用历史飞行数据、空域规则、气象知识等构建知识图谱，
通过图推理辅助路径规划决策，输出带有推理链和置信度的规划结果。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class KnowledgeGraphPlanner:
    """知识图谱路径规划器。

    基于知识图谱的路径规划，将历史飞行数据、空域规则、气象知识等
    组织为图结构，通过规则匹配和推理链生成路径规划建议。
    规划结果附带完整的推理过程和置信度评估。

    Args:
        config: 配置字典，支持以下参数：
            - rule_confidence_threshold: 规则置信度阈值，默认0.5
            - max_reasoning_depth: 最大推理深度，默认3
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.rule_confidence_threshold: float = self.config.get(
            "rule_confidence_threshold",
            0.5,
        )
        self.max_reasoning_depth: int = self.config.get("max_reasoning_depth", 3)

        # 内置规则库
        self._builtin_rules = [
            {
                "id": "R001",
                "name": "避障规则",
                "condition": "obstacle_nearby",
                "action": "detour",
                "confidence": 0.95,
                "priority": 1,
            },
            {
                "id": "R002",
                "name": "高风险区域规避",
                "condition": "high_risk_zone",
                "action": "avoid",
                "confidence": 0.90,
                "priority": 1,
            },
            {
                "id": "R003",
                "name": "逆风减速",
                "condition": "headwind",
                "action": "reduce_speed",
                "confidence": 0.85,
                "priority": 2,
            },
            {
                "id": "R004",
                "name": "顺风加速",
                "condition": "tailwind",
                "action": "increase_speed",
                "confidence": 0.80,
                "priority": 3,
            },
            {
                "id": "R005",
                "name": "低能见度减速",
                "condition": "low_visibility",
                "action": "reduce_speed",
                "confidence": 0.88,
                "priority": 2,
            },
            {
                "id": "R006",
                "name": "禁飞区绕行",
                "condition": "no_fly_zone",
                "action": "detour",
                "confidence": 0.99,
                "priority": 1,
            },
        ]

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行基于知识图谱的路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 [x, y]
                - goal: 终点坐标 [x, y]
                - grid_size: 网格尺寸 [rows, cols]
                - obstacles: 障碍物列表 list[list[int]]
                - knowledge_base: 知识库条目列表 list[dict]，每个条目含：
                    - id: 条目ID
                    - type: 类型（rule/fact/experience）
                    - content: 内容
                    - confidence: 置信度
                - query_context: 查询上下文字典，含：
                    - weather: 天气信息
                    - time_of_day: 时段
                    - uav_type: 无人机类型

        Returns:
            包含以下键的字典：
                - path: 规划路径
                - reasoning_chain: 推理链
                - applied_rules: 应用的规则列表
                - confidence: 总体置信度
        """
        np.random.seed(42)

        start = params.get("start", [0, 0])
        goal = params.get("goal", [10, 10])
        grid_size = params.get("grid_size", [50, 50])
        obstacles = set(map(tuple, params.get("obstacles", [])))
        knowledge_base = params.get("knowledge_base", [])
        query_context = params.get("query_context", {})

        rows, cols = grid_size

        logger.info(
            "知识图谱规划: 起点=%s, 终点=%s, 知识库条目=%d",
            start,
            goal,
            len(knowledge_base),
        )

        start_grid = self._world_to_grid(start, rows, cols)
        goal_grid = self._world_to_grid(goal, rows, cols)

        # 合并内置规则和外部知识库
        all_rules = self._builtin_rules.copy()
        for entry in knowledge_base:
            if entry.get("type") == "rule":
                all_rules.append(
                    {
                        "id": entry.get("id", "K001"),
                        "name": entry.get("content", entry.get("name", "未知规则")),
                        "condition": entry.get("condition", "custom"),
                        "action": entry.get("action", "advise"),
                        "confidence": entry.get("confidence", 0.7),
                        "priority": entry.get("priority", 2),
                    }
                )

        # 推理阶段：匹配适用的规则
        reasoning_chain: list[dict[str, Any]] = []
        applied_rules: list[dict[str, Any]] = []
        cost_modifiers: dict[str, float] = {}

        # 分析查询上下文
        weather = query_context.get("weather", {})
        time_of_day = query_context.get("time_of_day", "day")
        uav_type = query_context.get("uav_type", "multirotor")

        # 推理链步骤1：环境分析
        reasoning_chain.append(
            {
                "step": 1,
                "type": "analysis",
                "content": f"环境分析: 天气={weather}, 时段={time_of_day}, 机型={uav_type}",
                "confidence": 0.9,
            }
        )

        # 推理链步骤2：规则匹配
        matched_rules = self._match_rules(
            all_rules,
            obstacles,
            weather,
            query_context,
            rows,
            cols,
        )
        reasoning_chain.append(
            {
                "step": 2,
                "type": "rule_matching",
                "content": f"规则匹配: 匹配到 {len(matched_rules)} 条适用规则",
                "matched_rules": [r["id"] for r in matched_rules],
                "confidence": 0.85,
            }
        )

        # 推理链步骤3：规则应用与代价调整
        for rule in matched_rules:
            if rule["confidence"] >= self.rule_confidence_threshold:
                applied_rules.append(rule)
                modifier = self._get_cost_modifier(rule)
                cost_modifiers[rule["condition"]] = modifier
                reasoning_chain.append(
                    {
                        "step": len(reasoning_chain) + 1,
                        "type": "rule_application",
                        "content": f"应用规则 [{rule['id']}] {rule['name']}: {rule['action']}",
                        "rule": rule,
                        "cost_modifier": modifier,
                        "confidence": rule["confidence"],
                    }
                )

        # 推理链步骤4：路径规划
        path = self._plan_with_knowledge(
            start_grid,
            goal_grid,
            rows,
            cols,
            obstacles,
            cost_modifiers,
        )
        reasoning_chain.append(
            {
                "step": len(reasoning_chain) + 1,
                "type": "planning",
                "content": f"路径规划完成: 路径长度={len(path)}个航点",
                "confidence": 0.8 if path else 0.0,
            }
        )

        # 推理链步骤5：置信度评估
        if applied_rules:
            rule_confidences = [r["confidence"] for r in applied_rules]
            overall_confidence = float(np.mean(rule_confidences))
        else:
            overall_confidence = 0.7  # 无规则匹配时使用默认置信度

        reasoning_chain.append(
            {
                "step": len(reasoning_chain) + 1,
                "type": "confidence_evaluation",
                "content": f"总体置信度: {overall_confidence:.4f}",
                "confidence": overall_confidence,
            }
        )

        # 计算路径代价
        path_cost = 0.0
        for i in range(len(path) - 1):
            path_cost += float(
                np.linalg.norm(
                    np.array(path[i + 1]) - np.array(path[i]),
                )
            )

        logger.info(
            "知识图谱规划完成: 路径代价=%.2f, 置信度=%.4f, 应用规则=%d条",
            path_cost,
            overall_confidence,
            len(applied_rules),
        )

        return {
            "path": path,
            "reasoning_chain": reasoning_chain,
            "applied_rules": applied_rules,
            "confidence": overall_confidence,
            "cost": path_cost,
        }

    def _world_to_grid(
        self,
        pos: list,
        rows: int,
        cols: int,
    ) -> tuple[int, int]:
        """世界坐标转网格坐标。"""
        gx = int(pos[0] + rows / 2)
        gy = int(pos[1] + cols / 2)
        return (max(0, min(gx, rows - 1)), max(0, min(gy, cols - 1)))

    def _grid_to_world(
        self,
        pos: tuple[int, int],
        rows: int,
        cols: int,
    ) -> list[int]:
        """网格坐标转世界坐标。"""
        return [pos[0] - rows // 2, pos[1] - cols // 2]

    def _match_rules(
        self,
        rules: list[dict],
        obstacles: set,
        weather: dict,
        context: dict,
        rows: int,
        cols: int,
    ) -> list[dict]:
        """根据当前环境匹配适用的规则。"""
        matched = []

        for rule in rules:
            condition = rule.get("condition", "")
            applicable = False

            if condition == "obstacle_nearby" and obstacles:
                applicable = True
            elif condition == "high_risk_zone":
                applicable = len(obstacles) > 5
            elif condition == "headwind":
                wind_dir = weather.get("wind_direction", 0)
                applicable = 90 <= wind_dir <= 270
            elif condition == "tailwind":
                wind_dir = weather.get("wind_direction", 0)
                applicable = wind_dir < 90 or wind_dir > 270
            elif condition == "low_visibility":
                visibility = weather.get("visibility", 10)
                applicable = visibility < 5.0
            elif condition == "no_fly_zone":
                applicable = len(obstacles) > 10
            elif condition == "custom":
                applicable = True

            if applicable:
                matched.append(rule)

        # 按优先级排序
        matched.sort(key=lambda r: r.get("priority", 99))
        return matched

    def _get_cost_modifier(self, rule: dict) -> float:
        """获取规则对应的代价修正值。"""
        action = rule.get("action", "")
        if action == "detour":
            return 2.0
        elif action == "avoid":
            return 3.0
        elif action == "reduce_speed":
            return 0.5
        elif action == "increase_speed":
            return -0.2
        return 0.0

    def _plan_with_knowledge(
        self,
        start_grid: tuple[int, int],
        goal_grid: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        cost_modifiers: dict[str, float],
    ) -> list[list[int]]:
        """结合知识规则进行路径规划。"""
        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start_grid))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start_grid: 0.0}

        # 计算总代价修正
        total_modifier = sum(cost_modifiers.values()) if cost_modifiers else 0.0
        modifier_factor = max(0.1, 1.0 + abs(total_modifier) * 0.01)

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal_grid:
                return self._reconstruct_path(came_from, current, rows, cols)

            for neighbor in self._get_neighbors(current, rows, cols, obstacles):
                base_cost = 1.0

                # 应用知识规则修正代价
                for condition, modifier in cost_modifiers.items():
                    if condition == "obstacle_nearby":
                        # 靠近障碍物的节点代价增加
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            adj = (neighbor[0] + dx, neighbor[1] + dy)
                            if adj in obstacles:
                                base_cost += abs(modifier) * 0.5
                    elif condition == "high_risk_zone":
                        base_cost += abs(modifier) * 0.1

                step_cost = base_cost * modifier_factor
                tentative_g = g_score[current] + step_cost

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = float(abs(neighbor[0] - goal_grid[0]) + abs(neighbor[1] - goal_grid[1]))
                    heapq.heappush(open_set, (tentative_g + h, neighbor))

        return []

    def _get_neighbors(
        self,
        pos: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[tuple[int, int]]:
        """获取有效邻居节点（4连通）。"""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in obstacles:
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """从目标回溯重建路径。"""
        path = [self._grid_to_world(current, rows, cols)]
        while current in came_from:
            current = came_from[current]
            path.append(self._grid_to_world(current, rows, cols))
        path.reverse()
        return path
