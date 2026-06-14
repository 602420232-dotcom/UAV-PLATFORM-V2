"""DQN（Deep Q-Network）深度强化学习路径规划算法。

基于深度Q网络的无模型强化学习算法，通过经验回放和目标网络
在网格环境中学习最优路径策略。智能体以当前位置为状态，
以移动方向为动作，通过与环境交互收集转移样本，
使用均方误差损失训练Q网络逼近最优动作价值函数。

注意：本实现使用numpy模拟神经网络前向传播，不依赖PyTorch，
适合作为算法注册和接口验证使用。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class DQNPlanner:
    """DQN深度强化学习路径规划器。

    使用深度Q网络在网格环境中学习从起点到终点的最优路径策略。
    采用经验回放缓冲区打破样本相关性，目标网络稳定训练过程。
    网络结构为多层全连接网络，使用numpy实现前向传播。

    Args:
        config: 配置字典，支持以下参数：
            - hidden_size: 隐藏层神经元数量，默认64
            - num_hidden_layers: 隐藏层数量，默认2
            - learning_rate: 学习率，默认0.001
            - batch_size: 批量采样大小，默认32
            - gamma: 折扣因子，默认0.99
            - target_update_freq: 目标网络更新频率（步数），默认100
            - buffer_size: 经验回放缓冲区容量，默认10000
            - epsilon_start: 探索率初始值，默认1.0
            - epsilon_end: 探索率最小值，默认0.01
            - epsilon_decay: 探索率衰减系数，默认0.995
            - num_episodes: 训练回合数，默认200
            - max_steps_per_episode: 每回合最大步数，默认200
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.hidden_size: int = self.config.get("hidden_size", 64)
        self.num_hidden_layers: int = self.config.get("num_hidden_layers", 2)
        self.learning_rate: float = self.config.get("learning_rate", 0.001)
        self.batch_size: int = self.config.get("batch_size", 32)
        self.gamma: float = self.config.get("gamma", 0.99)
        self.target_update_freq: int = self.config.get("target_update_freq", 100)
        self.buffer_size: int = self.config.get("buffer_size", 10000)
        self.epsilon_start: float = self.config.get("epsilon_start", 1.0)
        self.epsilon_end: float = self.config.get("epsilon_end", 0.01)
        self.epsilon_decay: float = self.config.get("epsilon_decay", 0.995)
        self.num_episodes: int = self.config.get("num_episodes", 200)
        self.max_steps_per_episode: int = self.config.get(
            "max_steps_per_episode",
            200,
        )

        # 动作空间：8方向移动
        self.actions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]
        self.num_actions = len(self.actions)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行DQN路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]

        Returns:
            包含以下字段的字典：
                - path: 路径点列表 list[list[int]]
                - q_values: 各状态的平均Q值分布 list[float]
                - total_reward: 最终路径的总奖励 float
                - convergence: 收敛信息 dict
        """
        np.random.seed(42)

        raw_start = params.get("start", (0, 0))
        raw_goal = params.get("goal", (10, 10))
        start: tuple[int, int] = (int(raw_start[0]), int(raw_start[1]))
        goal: tuple[int, int] = (int(raw_goal[0]), int(raw_goal[1]))
        grid_size = tuple(params.get("grid_size", (50, 50)))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        logger.info(
            "DQN规划: 起点=%s, 终点=%s, 网格=%s, 障碍物=%d, 回合=%d",
            start,
            goal,
            grid_size,
            len(obstacles),
            self.num_episodes,
        )

        rows, cols = grid_size
        state_dim = 4  # [x, y, goal_x, goal_y] 归一化

        # 初始化Q网络和目标网络权重
        q_weights = self._init_network(state_dim)
        target_weights = [w.copy() for w in q_weights]

        # 经验回放缓冲区
        replay_buffer: list[tuple] = []

        epsilon = self.epsilon_start
        episode_rewards: list[float] = []
        total_steps = 0
        best_path: list[list[int]] = []
        best_reward = float("-inf")

        for episode in range(self.num_episodes):
            state = np.array(
                [start[0] / rows, start[1] / cols, goal[0] / rows, goal[1] / cols],
                dtype=np.float64,
            )
            path_trace = [list(start)]
            total_reward = 0.0

            for step in range(self.max_steps_per_episode):
                # 当前位置（反归一化）
                pos_x = int(np.clip(state[0] * rows, 0, rows - 1))
                pos_y = int(np.clip(state[1] * cols, 0, cols - 1))

                # 到达终点
                if (pos_x, pos_y) == goal:
                    total_reward += 100.0
                    break

                # epsilon-greedy策略选择动作
                if np.random.rand() < epsilon:
                    action_idx = np.random.randint(self.num_actions)
                else:
                    q_vals = self._forward(state, q_weights)
                    action_idx = int(np.argmax(q_vals))

                # 执行动作
                dx, dy = self.actions[action_idx]
                next_x = int(np.clip(pos_x + dx, 0, rows - 1))
                next_y = int(np.clip(pos_y + dy, 0, cols - 1))

                # 计算奖励
                reward = -1.0  # 步长惩罚
                if (next_x, next_y) in obstacles:
                    reward = -10.0
                    next_x, next_y = pos_x, pos_y  # 碰撞后原地不动
                elif (next_x, next_y) == goal:
                    reward = 100.0
                else:
                    # 接近目标的奖励
                    old_dist = abs(pos_x - goal[0]) + abs(pos_y - goal[1])
                    new_dist = abs(next_x - goal[0]) + abs(next_y - goal[1])
                    reward += (old_dist - new_dist) * 0.5

                next_state = np.array(
                    [next_x / rows, next_y / cols, goal[0] / rows, goal[1] / cols],
                    dtype=np.float64,
                )

                # 存入经验回放缓冲区
                replay_buffer.append(
                    (state, action_idx, reward, next_state, False),
                )
                if len(replay_buffer) > self.buffer_size:
                    replay_buffer.pop(0)

                state = next_state
                total_reward += reward
                total_steps += 1

                if (next_x, next_y) != (pos_x, pos_y):
                    path_trace.append([next_x, next_y])

                # 从回放缓冲区采样训练
                if len(replay_buffer) >= self.batch_size:
                    q_weights = self._train_step(
                        replay_buffer,
                        q_weights,
                        target_weights,
                    )

                # 更新目标网络
                if total_steps % self.target_update_freq == 0:
                    target_weights = [w.copy() for w in q_weights]

            episode_rewards.append(total_reward)

            # 记录最优路径
            if total_reward > best_reward and len(path_trace) > 1:
                best_reward = total_reward
                best_path = path_trace

            # 衰减探索率
            epsilon = max(self.epsilon_end, epsilon * self.epsilon_decay)

            if episode % 50 == 0:
                avg_reward = np.mean(episode_rewards[-50:]) if episode_rewards else 0
                logger.debug(
                    "回合 %d: 总奖励=%.2f, 平均奖励=%.2f, epsilon=%.4f",
                    episode,
                    total_reward,
                    avg_reward,
                    epsilon,
                )

        # 使用训练好的网络提取最终路径
        final_path = self._extract_path(
            q_weights,
            start,
            goal,
            rows,
            cols,
            obstacles,
        )
        if len(final_path) > len(best_path):
            final_path = best_path

        # 计算最终路径的Q值分布
        q_value_distribution = self._compute_q_distribution(
            q_weights,
            final_path,
            rows,
            cols,
        )

        # 计算最终路径总奖励
        final_reward = self._evaluate_path_reward(
            final_path,
            goal,
            obstacles,
        )

        # 收敛信息
        convergence = {
            "episode_rewards": episode_rewards,
            "avg_reward_last_10": float(
                np.mean(episode_rewards[-10:]) if episode_rewards else 0,
            ),
            "avg_reward_last_50": float(
                np.mean(episode_rewards[-50:]) if episode_rewards else 0,
            ),
            "final_epsilon": epsilon,
            "total_steps": total_steps,
            "num_episodes": self.num_episodes,
        }

        logger.info(
            "DQN规划完成: 路径长度=%d, 总奖励=%.2f, 平均奖励(后50)=%.2f",
            len(final_path),
            final_reward,
            convergence["avg_reward_last_50"],
        )

        return {
            "path": final_path,
            "q_values": q_value_distribution,
            "total_reward": final_reward,
            "convergence": convergence,
        }

    def _init_network(self, input_dim: int) -> list[np.ndarray]:
        """初始化网络权重和偏置。

        创建多层全连接网络的参数列表，使用Xavier初始化。
        网络结构: input_dim -> hidden_size * num_hidden_layers -> num_actions

        Args:
            input_dim: 输入维度。

        Returns:
            权重和偏置交替的列表 [W1, b1, W2, b2, ...]。
        """
        weights = []
        prev_size = input_dim

        for _ in range(self.num_hidden_layers):
            w = np.random.randn(prev_size, self.hidden_size) * np.sqrt(
                2.0 / prev_size,
            )
            b = np.zeros(self.hidden_size)
            weights.extend([w, b])
            prev_size = self.hidden_size

        # 输出层
        w = np.random.randn(prev_size, self.num_actions) * np.sqrt(
            2.0 / prev_size,
        )
        b = np.zeros(self.num_actions)
        weights.extend([w, b])

        return weights

    def _forward(
        self,
        x: np.ndarray,
        weights: list[np.ndarray],
    ) -> np.ndarray:
        """网络前向传播。

        Args:
            x: 输入向量。
            weights: 网络权重列表。

        Returns:
            输出Q值向量。
        """
        h = x.copy()
        num_layers = len(weights) // 2

        for i in range(num_layers):
            w = weights[2 * i]
            b = weights[2 * i + 1]
            h = h @ w + b
            if i < num_layers - 1:
                # 隐藏层使用ReLU激活
                h = np.maximum(0, h)

        return h

    def _train_step(
        self,
        replay_buffer: list[tuple],
        q_weights: list[np.ndarray],
        target_weights: list[np.ndarray],
    ) -> list[np.ndarray]:
        """执行一步训练更新。

        从经验回放缓冲区随机采样一个批次，计算目标Q值，
        使用梯度下降更新Q网络权重。

        Args:
            replay_buffer: 经验回放缓冲区。
            q_weights: 当前Q网络权重。
            target_weights: 目标网络权重。

        Returns:
            更新后的Q网络权重。
        """
        indices = np.random.choice(
            len(replay_buffer),
            self.batch_size,
            replace=False,
        )
        batch = [replay_buffer[i] for i in indices]

        new_weights = [w.copy() for w in q_weights]

        for state, action_idx, reward, next_state, done in batch:
            # 当前Q值
            q_values = self._forward(state, q_weights)
            target_q = q_values.copy()

            # 目标Q值（使用目标网络）
            if done:
                target_q[action_idx] = reward
            else:
                next_q = self._forward(next_state, target_weights)
                target_q[action_idx] = reward + self.gamma * np.max(next_q)

            # 计算梯度并更新权重（简化版梯度下降）
            td_error = target_q - q_values
            new_weights = self._update_weights(
                new_weights,
                state,
                td_error,
                action_idx,
            )

        return new_weights

    def _update_weights(
        self,
        weights: list[np.ndarray],
        state: np.ndarray,
        td_error: np.ndarray,
        action_idx: int,
    ) -> list[np.ndarray]:
        """根据TD误差更新网络权重。

        使用简化的反向传播，仅对选中动作对应的输出神经元
        进行梯度传播。

        Args:
            weights: 当前网络权重。
            state: 输入状态。
            td_error: TD误差向量。
            action_idx: 执行的动作索引。

        Returns:
            更新后的网络权重。
        """
        new_weights = [w.copy() for w in weights]
        num_layers = len(weights) // 2

        # 前向传播保存中间激活值
        activations = [state.copy()]
        h = state.copy()
        for i in range(num_layers):
            w = weights[2 * i]
            b = weights[2 * i + 1]
            h = h @ w + b
            if i < num_layers - 1:
                h = np.maximum(0, h)
            activations.append(h.copy())

        # 反向传播（简化：仅传播选中动作的梯度）
        grad = np.zeros(self.num_actions)
        grad[action_idx] = td_error[action_idx]

        for i in range(num_layers - 1, -1, -1):
            w = weights[2 * i]
            b = weights[2 * i + 1]
            prev_h = activations[i]

            # 计算权重梯度
            grad_w = np.outer(prev_h, grad)
            grad_b = grad.copy()

            # 更新权重
            new_weights[2 * i] = w + self.learning_rate * grad_w
            new_weights[2 * i + 1] = b + self.learning_rate * grad_b

            # 传播梯度到上一层
            if i > 0:
                grad = w @ grad
                # ReLU导数
                relu_mask = (activations[i] > 0).astype(float)
                grad = grad * relu_mask

        return new_weights

    def _extract_path(
        self,
        weights: list[np.ndarray],
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[list[int]]:
        """使用训练好的Q网络提取贪心路径。

        Args:
            weights: 训练好的Q网络权重。
            start: 起点。
            goal: 终点。
            rows: 网格行数。
            cols: 网格列数。
            obstacles: 障碍物集合。

        Returns:
            路径点列表。
        """
        path = [list(start)]
        current = start
        visited = {start}
        max_steps = rows * cols

        for _ in range(max_steps):
            if current == goal:
                break

            state = np.array(
                [current[0] / rows, current[1] / cols, goal[0] / rows, goal[1] / cols],
                dtype=np.float64,
            )
            q_vals = self._forward(state, weights)

            # 按Q值排序尝试每个动作
            sorted_actions = np.argsort(q_vals)[::-1]

            moved = False
            for action_idx in sorted_actions:
                dx, dy = self.actions[int(action_idx)]
                nx = int(np.clip(current[0] + dx, 0, rows - 1))
                ny = int(np.clip(current[1] + dy, 0, cols - 1))

                # fmt: off
                if (
                    (nx, ny) not in obstacles
                    and (nx, ny) not in visited
                    and 0 <= nx < rows
                    and 0 <= ny < cols
                ):
                    # fmt: on
                    current = (nx, ny)
                    path.append([nx, ny])
                    visited.add(current)
                    moved = True
                    break

            if not moved:
                break

        return path

    def _compute_q_distribution(
        self,
        weights: list[np.ndarray],
        path: list[list[int]],
        rows: int,
        cols: int,
    ) -> list[float]:
        """计算路径上各状态的平均Q值分布。

        Args:
            weights: Q网络权重。
            path: 路径点列表。
            rows: 网格行数。
            cols: 网格列数。

        Returns:
            各路径点的平均Q值列表。
        """
        if not path:
            return []

        q_values = []
        for point in path:
            state = np.array(
                [point[0] / rows, point[1] / cols, point[0] / rows, point[1] / cols],
                dtype=np.float64,
            )
            q_vals = self._forward(state, weights)
            q_values.append(float(np.mean(q_vals)))

        return q_values

    def _evaluate_path_reward(
        self,
        path: list[list[int]],
        goal: tuple[int, int],
        obstacles: set,
    ) -> float:
        """评估路径的总奖励。

        Args:
            path: 路径点列表。
            goal: 终点。
            obstacles: 障碍物集合。

        Returns:
            路径总奖励。
        """
        if not path:
            return float("-inf")

        reward = 0.0
        for i, point in enumerate(path):
            pos = (point[0], point[1])
            if pos in obstacles:
                reward -= 10.0
            elif pos == goal:
                reward += 100.0
            else:
                reward -= 1.0

        # 路径长度奖励（越短越好）
        reward -= len(path) * 0.1

        return reward
