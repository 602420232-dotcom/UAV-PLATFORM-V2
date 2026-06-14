"""多无人机冲突消解器 — 基于优先级/博弈论/协商策略的冲突消解.

支持三种消解策略：优先级策略（按UAV优先级排序让低优先级避让）、
博弈论策略（基于纳什均衡求解最优策略组合）、协商策略（迭代协商
寻找帕累托最优解）。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class MultiUAVConflictResolver:
    """多无人机冲突消解器.

    检测并消解多架无人机之间的飞行冲突，支持优先级、博弈论和协商
    三种消解策略，为每架无人机生成消解动作。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.safety_distance = self.config.get("safety_distance", 10.0)
        self.max_negotiation_rounds = self.config.get(
            "max_negotiation_rounds",
            10,
        )
        self.conflict_horizon = self.config.get("conflict_horizon", 60.0)
        self.default_strategy = self.config.get("default_strategy", "priority")

    def resolve(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行多无人机冲突消解.

        Args:
            params: 消解参数字典，包含:
                - uav_states: 各UAV状态列表，每个状态包含:
                    id, position [x,y,z], velocity [vx,vy,vz],
                    priority, heading, speed
                - conflicts: 冲突列表，每个冲突包含:
                    uav_ids (冲突UAV ID对), conflict_point,
                    time_to_conflict, severity
                - strategy: 消解策略 (priority/game_theory/negotiation)
                - constraints: 约束条件字典 (可选)

        Returns:
            包含消解结果的字典:
                - resolved_states: 消解后各UAV状态
                - resolution_actions: 消解动作列表
                - remaining_conflicts: 剩余未消解冲突
        """
        np.random.seed(42)

        uav_states = params.get("uav_states", [])
        conflicts = params.get("conflicts", [])
        strategy = params.get("strategy", self.default_strategy)
        constraints = params.get("constraints", {})

        logger.info(
            "开始冲突消解: UAV数量=%d, 冲突数量=%d, 策略=%s",
            len(uav_states),
            len(conflicts),
            strategy,
        )

        if not conflicts:
            logger.info("无冲突需要消解")
            return {
                "resolved_states": uav_states,
                "resolution_actions": [],
                "remaining_conflicts": [],
            }

        if strategy == "priority":
            resolved, actions = self._priority_resolution(
                uav_states,
                conflicts,
                constraints,
            )
        elif strategy == "game_theory":
            resolved, actions = self._game_theory_resolution(
                uav_states,
                conflicts,
                constraints,
            )
        elif strategy == "negotiation":
            resolved, actions = self._negotiation_resolution(
                uav_states,
                conflicts,
                constraints,
            )
        else:
            logger.warning("未知策略 '%s'，回退到优先级策略", strategy)
            resolved, actions = self._priority_resolution(
                uav_states,
                conflicts,
                constraints,
            )

        remaining = self._check_remaining_conflicts(resolved)

        logger.info(
            "冲突消解完成: 消解动作数=%d, 剩余冲突=%d",
            len(actions),
            len(remaining),
        )

        return {
            "resolved_states": resolved,
            "resolution_actions": actions,
            "remaining_conflicts": remaining,
        }

    def _priority_resolution(
        self,
        uav_states: list[dict[str, Any]],
        conflicts: list[dict[str, Any]],
        constraints: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """优先级策略消解.

        按UAV优先级排序，低优先级UAV执行避让动作。
        """
        state_map = {s["id"]: s.copy() for s in uav_states}
        actions: list[dict[str, Any]] = []

        sorted_conflicts = sorted(
            conflicts,
            key=lambda c: c.get("severity", 0.5),
            reverse=True,
        )

        for conflict in sorted_conflicts:
            uav_ids = conflict.get("uav_ids", [])
            if len(uav_ids) < 2:
                continue

            involved = [state_map[uid] for uid in uav_ids if uid in state_map]
            involved.sort(key=lambda s: s.get("priority", 0), reverse=True)

            higher = involved[0]
            lower = involved[1]

            deviation = self._compute_deviation(lower, higher, constraints)
            action = {
                "uav_id": lower["id"],
                "type": "deviation",
                "deviation_vector": deviation.tolist(),
                "reason": f"避让高优先级UAV {higher['id']}",
                "conflict_id": conflict.get("id", -1),
            }
            actions.append(action)

            new_pos = np.array(lower["position"]) + deviation
            state_map[lower["id"]]["position"] = new_pos.tolist()

        resolved = list(state_map.values())
        return resolved, actions

    def _game_theory_resolution(
        self,
        uav_states: list[dict[str, Any]],
        conflicts: list[dict[str, Any]],
        constraints: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """博弈论策略消解.

        基于简化的纳什均衡求解，为冲突UAV对寻找最优策略组合。
        """
        state_map = {s["id"]: s.copy() for s in uav_states}
        actions: list[dict[str, Any]] = []

        for conflict in conflicts:
            uav_ids = conflict.get("uav_ids", [])
            if len(uav_ids) < 2:
                continue

            id_a, id_b = uav_ids[0], uav_ids[1]
            if id_a not in state_map or id_b not in state_map:
                continue

            pos_a = np.array(state_map[id_a]["position"])
            pos_b = np.array(state_map[id_b]["position"])

            relative_pos = pos_b - pos_a
            distance = np.linalg.norm(relative_pos)

            if distance < 1e-6:
                direction = np.array([1.0, 0.0, 0.0])
            else:
                direction = relative_pos / distance

            payoff_matrix = self._build_payoff_matrix(
                direction,
                float(distance),
                constraints,
            )
            strategy_a, strategy_b = self._solve_nash_equilibrium(payoff_matrix)

            deviation_a = self._strategy_to_deviation(
                strategy_a,
                direction,
                constraints,
            )
            deviation_b = self._strategy_to_deviation(
                strategy_b,
                -direction,
                constraints,
            )

            actions.append(
                {
                    "uav_id": id_a,
                    "type": "game_theory_deviation",
                    "deviation_vector": deviation_a.tolist(),
                    "strategy_index": int(strategy_a),
                    "reason": f"博弈论消解: 与UAV {id_b}的纳什均衡策略",
                    "conflict_id": conflict.get("id", -1),
                }
            )
            actions.append(
                {
                    "uav_id": id_b,
                    "type": "game_theory_deviation",
                    "deviation_vector": deviation_b.tolist(),
                    "strategy_index": int(strategy_b),
                    "reason": f"博弈论消解: 与UAV {id_a}的纳什均衡策略",
                    "conflict_id": conflict.get("id", -1),
                }
            )

            state_map[id_a]["position"] = (pos_a + deviation_a).tolist()
            state_map[id_b]["position"] = (pos_b + deviation_b).tolist()

        resolved = list(state_map.values())
        return resolved, actions

    def _negotiation_resolution(
        self,
        uav_states: list[dict[str, Any]],
        conflicts: list[dict[str, Any]],
        constraints: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """协商策略消解.

        通过迭代协商，各UAV逐步调整航向，寻找帕累托最优解。
        """
        state_map = {s["id"]: s.copy() for s in uav_states}
        actions: list[dict[str, Any]] = []

        for conflict in conflicts:
            uav_ids = conflict.get("uav_ids", [])
            if len(uav_ids) < 2:
                continue

            id_a, id_b = uav_ids[0], uav_ids[1]
            if id_a not in state_map or id_b not in state_map:
                continue

            deviation_a = np.zeros(3)
            deviation_b = np.zeros(3)

            for round_idx in range(self.max_negotiation_rounds):
                pos_a = np.array(state_map[id_a]["position"]) + deviation_a
                pos_b = np.array(state_map[id_b]["position"]) + deviation_b
                distance = np.linalg.norm(pos_b - pos_a)

                if distance > self.safety_distance * 1.5:
                    break

                adjustment_a = self._negotiation_step(
                    pos_a,
                    pos_b,
                    id_a,
                    constraints,
                    round_idx,
                )
                adjustment_b = self._negotiation_step(
                    pos_b,
                    pos_a,
                    id_b,
                    constraints,
                    round_idx,
                )

                deviation_a += adjustment_a
                deviation_b += adjustment_b

            actions.append(
                {
                    "uav_id": id_a,
                    "type": "negotiation_deviation",
                    "deviation_vector": deviation_a.tolist(),
                    "negotiation_rounds": round_idx + 1,
                    "reason": f"协商消解: 与UAV {id_b}经{round_idx + 1}轮协商",
                    "conflict_id": conflict.get("id", -1),
                }
            )
            actions.append(
                {
                    "uav_id": id_b,
                    "type": "negotiation_deviation",
                    "deviation_vector": deviation_b.tolist(),
                    "negotiation_rounds": round_idx + 1,
                    "reason": f"协商消解: 与UAV {id_a}经{round_idx + 1}轮协商",
                    "conflict_id": conflict.get("id", -1),
                }
            )

            state_map[id_a]["position"] = (
                np.array(state_map[id_a]["position"]) + deviation_a
            ).tolist()
            state_map[id_b]["position"] = (
                np.array(state_map[id_b]["position"]) + deviation_b
            ).tolist()

        resolved = list(state_map.values())
        return resolved, actions

    def _compute_deviation(
        self,
        lower_uav: dict[str, Any],
        higher_uav: dict[str, Any],
        constraints: dict[str, Any],
    ) -> np.ndarray:
        """计算低优先级UAV的避让偏移量."""
        pos_lower = np.array(lower_uav["position"])
        pos_higher = np.array(higher_uav["position"])
        relative = pos_lower - pos_higher
        distance = np.linalg.norm(relative)

        if distance < 1e-6:
            relative = np.array([1.0, 0.0, 0.0])
            distance = 1.0

        direction = relative / distance
        max_deviation = constraints.get("max_deviation", self.safety_distance)
        deviation_magnitude = min(
            self.safety_distance * 1.2 - distance * 0.5,
            max_deviation,
        )
        deviation_magnitude = max(deviation_magnitude, 0.0)

        return direction * deviation_magnitude

    def _build_payoff_matrix(
        self,
        direction: np.ndarray,
        distance: float,
        constraints: dict[str, Any],
    ) -> np.ndarray:
        """构建简化的博弈收益矩阵.

        返回形状为 (n_actions_a, n_actions_b, 2) 的收益矩阵。
        """
        n_actions = 5
        payoff = np.zeros((n_actions, n_actions, 2))

        lateral = np.array([-direction[1], direction[0], 0.0])
        vertical = np.array([0.0, 0.0, 1.0])

        actions_a = [
            np.zeros(3),
            lateral * 0.5,
            -lateral * 0.5,
            vertical * 0.3,
            -vertical * 0.3,
        ]
        actions_b = [
            np.zeros(3),
            -lateral * 0.5,
            lateral * 0.5,
            -vertical * 0.3,
            vertical * 0.3,
        ]

        for i, da in enumerate(actions_a):
            for j, db in enumerate(actions_b):
                new_dist = distance + np.linalg.norm(da - db)
                cost_a = -new_dist + 0.1 * np.linalg.norm(da) ** 2
                cost_b = -new_dist + 0.1 * np.linalg.norm(db) ** 2
                payoff[i, j, 0] = cost_a
                payoff[i, j, 1] = cost_b

        return payoff

    def _solve_nash_equilibrium(
        self,
        payoff: np.ndarray,
    ) -> tuple[int, int]:
        """求解简化纳什均衡（纯策略近似）.

        遍历所有策略组合，寻找帕累托最优的纯策略均衡。
        """
        n_a, n_b, _ = payoff.shape
        best_score = -float("inf")
        best_i, best_j = 0, 0

        for i in range(n_a):
            for j in range(n_b):
                combined = payoff[i, j, 0] + payoff[i, j, 1]
                if combined > best_score:
                    best_score = combined
                    best_i, best_j = i, j

        return best_i, best_j

    def _strategy_to_deviation(
        self,
        strategy_idx: int,
        direction: np.ndarray,
        constraints: dict[str, Any],
    ) -> np.ndarray:
        """将策略索引转换为实际偏移向量."""
        lateral = np.array([-direction[1], direction[0], 0.0])
        vertical = np.array([0.0, 0.0, 1.0])
        max_dev = constraints.get("max_deviation", self.safety_distance * 0.5)

        strategies = [
            np.zeros(3),
            lateral * max_dev,
            -lateral * max_dev,
            vertical * max_dev * 0.6,
            -vertical * max_dev * 0.6,
        ]

        idx = min(strategy_idx, len(strategies) - 1)
        return strategies[idx]

    def _negotiation_step(
        self,
        own_pos: np.ndarray,
        other_pos: np.ndarray,
        own_id: Any,
        constraints: dict[str, Any],
        round_idx: int,
    ) -> np.ndarray:
        """单轮协商步进，计算调整量."""
        relative = own_pos - other_pos
        distance = np.linalg.norm(relative)

        if distance < 1e-6:
            return np.zeros(3)

        direction = relative / distance
        step_size = constraints.get(
            "negotiation_step_size",
            self.safety_distance * 0.15,
        )
        decay = 1.0 / (1.0 + round_idx * 0.3)

        if distance < self.safety_distance:
            adjustment = direction * step_size * decay
        else:
            adjustment = direction * step_size * decay * 0.3

        return adjustment

    def _check_remaining_conflicts(
        self,
        resolved_states: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """检查消解后是否仍存在冲突."""
        remaining: list[dict[str, Any]] = []

        for i in range(len(resolved_states)):
            for j in range(i + 1, len(resolved_states)):
                pos_i = np.array(resolved_states[i]["position"])
                pos_j = np.array(resolved_states[j]["position"])
                distance = np.linalg.norm(pos_i - pos_j)

                if distance < self.safety_distance:
                    remaining.append(
                        {
                            "uav_ids": [
                                resolved_states[i]["id"],
                                resolved_states[j]["id"],
                            ],
                            "distance": float(distance),
                            "severity": float(
                                1.0 - distance / self.safety_distance,
                            ),
                        }
                    )

        return remaining
