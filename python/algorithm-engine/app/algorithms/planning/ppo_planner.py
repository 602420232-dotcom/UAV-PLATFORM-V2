"""PPO（Proximal Policy Optimization）近端策略优化路径规划算法。

基于PPO策略梯度方法的强化学习算法，通过裁剪目标函数限制策略更新幅度，
使用广义优势估计（GAE）平衡偏差与方差，实现稳定高效的策略优化。
智能体在网格环境中学习从起点到终点的最优移动策略。

注意：本实现使用numpy模拟神经网络前向传播，不依赖PyTorch，
适合作为算法注册和接口验证使用。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class PPOPlanner:
    """PPO近端策略优化路径规划器。

    使用PPO算法在网格环境中学习最优路径策略。策略网络输出各动作的概率分布，
    通过裁剪目标函数限制每次策略更新的幅度，防止策略崩溃。
    使用GAE（广义优势估计）计算优势函数，提高训练稳定性。

    Args:
        config: 配置字典，支持以下参数：
            - hidden_size: 隐藏层神经元数量，默认64
            - num_hidden_layers: 隐藏层数量，默认2
            - learning_rate: 学习率，默认0.0003
            - clip_ratio: PPO裁剪比例epsilon，默认0.2
            - ppo_epochs: 每批数据的训练轮数，默认4
            - gamma: 折扣因子，默认0.99
            - gae_lambda: GAE lambda参数，默认0.95
            - entropy_coef: 熵正则化系数，默认0.01
            - value_coef: 价值函数损失系数，默认0.5
            - max_grad_norm: 梯度裁剪范数，默认0.5
            - num_episodes: 训练回合数，默认200
            - max_steps_per_episode: 每回合最大步数，默认200
            - mini_batch_size: 小批量大小，默认64
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.hidden_size: int = self.config.get("hidden_size", 64)
        self.num_hidden_layers: int = self.config.get("num_hidden_layers", 2)
        self.learning_rate: float = self.config.get("learning_rate", 0.0003)
        self.clip_ratio: float = self.config.get("clip_ratio", 0.2)
        self.ppo_epochs: int = self.config.get("ppo_epochs", 4)
        self.gamma: float = self.config.get("gamma", 0.99)
        self.gae_lambda: float = self.config.get("gae_lambda", 0.95)
        self.entropy_coef: float = self.config.get("entropy_coef", 0.01)
        self.value_coef: float = self.config.get("value_coef", 0.5)
        self.max_grad_norm: float = self.config.get("max_grad_norm", 0.5)
        self.num_episodes: int = self.config.get("num_episodes", 200)
        self.max_steps_per_episode: int = self.config.get(
            "max_steps_per_episode", 200,
        )
        self.mini_batch_size: int = self.config.get("mini_batch_size", 64)

        # 动作空间：8方向移动
        self.actions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ]
        self.num_actions = len(self.actions)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行PPO路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]

        Returns:
            包含以下字段的字典：
                - path: 路径点列表 list[list[int]]
                - policy_probs: 各路径点的策略概率分布 list[list[float]]
                - total_reward: 最终路径的总奖励 float
                - kl_divergence: 训练过程中的KL散度信息 dict
        """
        np.random.seed(42)

        raw_start = params.get("start", (0, 0))
        raw_goal = params.get("goal", (10, 10))
        start: tuple[int, int] = (int(raw_start[0]), int(raw_start[1]))
        goal: tuple[int, int] = (int(raw_goal[0]), int(raw_goal[1]))
        grid_size = tuple(params.get("grid_size", (50, 50)))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        logger.info(
            "PPO规划: 起点=%s, 终点=%s, 网格=%s, 障碍物=%d, 回合=%d",
            start, goal, grid_size, len(obstacles), self.num_episodes,
        )

        rows, cols = grid_size
        state_dim = 4  # [x, y, goal_x, goal_y] 归一化

        # 初始化策略网络和价值网络
        policy_weights = self._init_network(state_dim, output_dim=self.num_actions)
        value_weights = self._init_network(state_dim, output_dim=1)

        episode_rewards: list[float] = []
        kl_history: list[float] = []
        best_path: list[list[int]] = []
        best_reward = float("-inf")

        for episode in range(self.num_episodes):
            # 收集轨迹数据
            trajectory = self._collect_trajectory(
                policy_weights, start, goal, rows, cols, obstacles,
            )

            if not trajectory:
                episode_rewards.append(-self.max_steps_per_episode)
                continue

            # 计算GAE优势
            states, actions, rewards, next_states, dones = zip(*trajectory)
            advantages, returns = self._compute_gae(rewards, dones)

            # 标准化优势
            if len(advantages) > 1:
                advantages = (advantages - np.mean(advantages)) / (
                    np.std(advantages) + 1e-8
                )

            # PPO更新
            old_policy_probs = []
            for s in states:
                probs = self._policy_forward(s, policy_weights)
                old_policy_probs.append(probs.copy())

            episode_kl = 0.0
            for _ in range(self.ppo_epochs):
                # 随机打乱数据
                indices = np.random.permutation(len(states))

                for start_idx in range(0, len(states), self.mini_batch_size):
                    end_idx = min(start_idx + self.mini_batch_size, len(states))
                    batch_indices = indices[start_idx:end_idx]

                    batch_states = [states[i] for i in batch_indices]
                    batch_actions = [actions[i] for i in batch_indices]
                    batch_advantages = advantages[batch_indices]
                    batch_returns = returns[batch_indices]
                    batch_old_probs = [old_policy_probs[i] for i in batch_indices]

                    # 计算KL散度
                    kl = self._compute_kl_divergence(
                        batch_states, batch_old_probs, policy_weights,
                    )
                    episode_kl += kl

                    # 更新策略网络
                    policy_weights = self._update_policy(
                        policy_weights, batch_states, batch_actions,
                        batch_advantages, batch_old_probs,
                    )

                    # 更新价值网络
                    value_weights = self._update_value(
                        value_weights, batch_states, batch_returns,
                    )

            episode_kl /= max(1, self.ppo_epochs)
            kl_history.append(episode_kl)

            total_reward = sum(rewards)
            episode_rewards.append(total_reward)

            # 记录最优路径
            path_trace = self._trajectory_to_path(
                trajectory, start, rows, cols,
            )
            if total_reward > best_reward and len(path_trace) > 1:
                best_reward = total_reward
                best_path = path_trace

            if episode % 50 == 0:
                avg_reward = np.mean(episode_rewards[-50:]) if episode_rewards else 0
                logger.debug(
                    "回合 %d: 总奖励=%.2f, 平均奖励=%.2f, KL=%.6f",
                    episode, total_reward, avg_reward, episode_kl,
                )

        # 使用训练好的策略网络提取最终路径
        final_path = self._extract_policy_path(
            policy_weights, start, goal, rows, cols, obstacles,
        )
        if len(final_path) <= 1 and best_path:
            final_path = best_path

        # 计算路径上各点的策略概率
        policy_probs = self._compute_policy_distribution(
            policy_weights, final_path, rows, cols,
        )

        # 计算最终路径总奖励
        final_reward = self._evaluate_path_reward(
            final_path, goal, obstacles,
        )

        # KL散度信息
        kl_divergence = {
            "kl_history": kl_history,
            "mean_kl": float(np.mean(kl_history)) if kl_history else 0.0,
            "max_kl": float(np.max(kl_history)) if kl_history else 0.0,
            "final_kl": float(kl_history[-1]) if kl_history else 0.0,
        }

        logger.info(
            "PPO规划完成: 路径长度=%d, 总奖励=%.2f, 平均KL=%.6f",
            len(final_path), final_reward, kl_divergence["mean_kl"],
        )

        return {
            "path": final_path,
            "policy_probs": policy_probs,
            "total_reward": final_reward,
            "kl_divergence": kl_divergence,
        }

    def _init_network(
        self, input_dim: int, output_dim: int = 1,
    ) -> list[np.ndarray]:
        """初始化网络权重和偏置。

        创建多层全连接网络的参数列表，使用Xavier初始化。
        网络结构: input_dim -> hidden_size * num_hidden_layers -> output_dim

        Args:
            input_dim: 输入维度。
            output_dim: 输出维度。

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
        w = np.random.randn(prev_size, output_dim) * np.sqrt(
            2.0 / prev_size,
        )
        b = np.zeros(output_dim)
        weights.extend([w, b])

        return weights

    def _policy_forward(
        self, x: np.ndarray, weights: list[np.ndarray],
    ) -> np.ndarray:
        """策略网络前向传播，输出动作概率分布。

        Args:
            x: 输入状态向量。
            weights: 策略网络权重。

        Returns:
            动作概率分布（经过softmax归一化）。
        """
        h = x.copy()
        num_layers = len(weights) // 2

        for i in range(num_layers):
            w = weights[2 * i]
            b = weights[2 * i + 1]
            h = h @ w + b
            if i < num_layers - 1:
                h = np.tanh(h)  # 策略网络隐藏层使用tanh

        # softmax输出动作概率
        h = h - np.max(h)  # 数值稳定性
        exp_h = np.exp(h)
        probs = exp_h / (np.sum(exp_h) + 1e-8)

        return probs

    def _value_forward(
        self, x: np.ndarray, weights: list[np.ndarray],
    ) -> float:
        """价值网络前向传播，输出状态价值估计。

        Args:
            x: 输入状态向量。
            weights: 价值网络权重。

        Returns:
            状态价值标量。
        """
        h = x.copy()
        num_layers = len(weights) // 2

        for i in range(num_layers):
            w = weights[2 * i]
            b = weights[2 * i + 1]
            h = h @ w + b
            if i < num_layers - 1:
                h = np.maximum(0, h)  # 价值网络隐藏层使用ReLU

        return float(h[0])

    def _collect_trajectory(
        self,
        policy_weights: list[np.ndarray],
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[tuple]:
        """使用当前策略收集一条轨迹数据。

        Args:
            policy_weights: 策略网络权重。
            start: 起点。
            goal: 终点。
            rows: 网格行数。
            cols: 网格列数。
            obstacles: 障碍物集合。

        Returns:
            轨迹数据列表 [(state, action, reward, next_state, done), ...]。
        """
        trajectory = []
        pos_x, pos_y = start
        visited = {start}

        for _ in range(self.max_steps_per_episode):
            state = np.array(
                [pos_x / rows, pos_y / cols,
                 goal[0] / rows, goal[1] / cols],
                dtype=np.float64,
            )

            # 采样动作
            probs = self._policy_forward(state, policy_weights)
            action_idx = int(np.random.choice(self.num_actions, p=probs))

            # 执行动作
            dx, dy = self.actions[action_idx]
            next_x = int(np.clip(pos_x + dx, 0, rows - 1))
            next_y = int(np.clip(pos_y + dy, 0, cols - 1))

            # 计算奖励
            reward = -1.0
            done = False
            if (next_x, next_y) in obstacles:
                reward = -10.0
                next_x, next_y = pos_x, pos_y
            elif (next_x, next_y) == goal:
                reward = 100.0
                done = True
            else:
                old_dist = abs(pos_x - goal[0]) + abs(pos_y - goal[1])
                new_dist = abs(next_x - goal[0]) + abs(next_y - goal[1])
                reward += (old_dist - new_dist) * 0.5

            next_state = np.array(
                [next_x / rows, next_y / cols,
                 goal[0] / rows, goal[1] / cols],
                dtype=np.float64,
            )

            trajectory.append((state, action_idx, reward, next_state, done))
            pos_x, pos_y = next_x, next_y
            visited.add((pos_x, pos_y))

            if done:
                break

        return trajectory

    def _compute_gae(
        self,
        rewards: tuple,
        dones: tuple,
    ) -> tuple[np.ndarray, np.ndarray]:
        """计算广义优势估计（GAE）。

        Args:
            rewards: 奖励序列。
            dones: 终止标志序列。

        Returns:
            (advantages, returns) 优势估计和回报。
        """
        n = len(rewards)
        advantages = np.zeros(n, dtype=np.float64)
        returns = np.zeros(n, dtype=np.float64)

        gae = 0.0
        last_value = 0.0

        for t in reversed(range(n)):
            if dones[t]:
                delta = rewards[t] - last_value
                gae = delta
            else:
                delta = rewards[t] + self.gamma * last_value - last_value
                gae = delta + self.gamma * self.gae_lambda * gae

            advantages[t] = gae
            last_value = rewards[t] + self.gamma * last_value
            returns[t] = advantages[t] + last_value - rewards[t]

        return advantages, returns

    def _compute_kl_divergence(
        self,
        states: list,
        old_probs: list,
        policy_weights: list[np.ndarray],
    ) -> float:
        """计算新旧策略之间的平均KL散度。

        Args:
            states: 状态列表。
            old_probs: 旧策略概率列表。
            policy_weights: 当前策略网络权重。

        Returns:
            平均KL散度。
        """
        total_kl = 0.0
        for state, old_p in zip(states, old_probs):
            new_p = self._policy_forward(state, policy_weights)
            # 避免除零
            old_p_safe = np.clip(old_p, 1e-8, 1.0)
            new_p_safe = np.clip(new_p, 1e-8, 1.0)
            kl = np.sum(old_p_safe * np.log(old_p_safe / new_p_safe))
            total_kl += kl

        return total_kl / max(len(states), 1)

    def _update_policy(
        self,
        policy_weights: list[np.ndarray],
        states: list,
        actions: list,
        advantages: np.ndarray,
        old_probs: list,
    ) -> list[np.ndarray]:
        """使用PPO裁剪目标函数更新策略网络。

        Args:
            policy_weights: 当前策略网络权重。
            states: 批量状态。
            actions: 批量动作。
            advantages: 批量优势。
            old_probs: 旧策略概率。

        Returns:
            更新后的策略网络权重。
        """
        new_weights = [w.copy() for w in policy_weights]

        for i, (state, action_idx) in enumerate(zip(states, actions)):
            old_p = old_probs[i]
            new_p = self._policy_forward(state, new_weights)

            # 重要性采样比率
            ratio = new_p[action_idx] / (old_p[action_idx] + 1e-8)

            # PPO裁剪目标
            adv = advantages[i]
            surrogate1 = ratio * adv
            surrogate2 = np.clip(ratio, 1.0 - self.clip_ratio,
                                 1.0 + self.clip_ratio) * adv
            policy_loss = -np.minimum(surrogate1, surrogate2)

            # 熵正则化
            entropy = -np.sum(new_p * np.log(new_p + 1e-8))
            policy_loss -= self.entropy_coef * entropy

            # 简化梯度更新
            grad_direction = -policy_loss
            new_weights = self._policy_gradient_step(
                new_weights, state, grad_direction, action_idx,
            )

        return new_weights

    def _policy_gradient_step(
        self,
        weights: list[np.ndarray],
        state: np.ndarray,
        loss_grad: float,
        action_idx: int,
    ) -> list[np.ndarray]:
        """执行策略网络的单步梯度更新。

        Args:
            weights: 当前权重。
            state: 输入状态。
            loss_grad: 损失梯度。
            action_idx: 动作索引。

        Returns:
            更新后的权重。
        """
        new_weights = [w.copy() for w in weights]
        num_layers = len(weights) // 2

        # 前向传播保存激活值
        activations = [state.copy()]
        h = state.copy()
        pre_activations = []

        for i in range(num_layers):
            w = weights[2 * i]
            b = weights[2 * i + 1]
            h = h @ w + b
            pre_activations.append(h.copy())
            if i < num_layers - 1:
                h = np.tanh(h)
            activations.append(h.copy())

        # 反向传播
        # softmax + 交叉熵梯度（简化）
        output = activations[-1]
        grad = output.copy()
        grad[action_idx] -= 1.0  # dL/dlogits
        grad *= loss_grad

        for i in range(num_layers - 1, -1, -1):
            w = weights[2 * i]
            b = weights[2 * i + 1]
            prev_h = activations[i]

            grad_w = np.outer(prev_h, grad)
            grad_b = grad.copy()

            # 梯度裁剪
            grad_norm = np.sqrt(np.sum(grad_w ** 2) + np.sum(grad_b ** 2))
            if grad_norm > self.max_grad_norm:
                scale = self.max_grad_norm / (grad_norm + 1e-8)
                grad_w *= scale
                grad_b *= scale

            new_weights[2 * i] = w + self.learning_rate * grad_w
            new_weights[2 * i + 1] = b + self.learning_rate * grad_b

            if i > 0:
                grad = w @ grad
                # tanh导数
                tanh_grad = 1.0 - pre_activations[i - 1] ** 2
                grad = grad * tanh_grad

        return new_weights

    def _update_value(
        self,
        value_weights: list[np.ndarray],
        states: list,
        returns: np.ndarray,
    ) -> list[np.ndarray]:
        """更新价值网络。

        Args:
            value_weights: 价值网络权重。
            states: 批量状态。
            returns: 批量回报。

        Returns:
            更新后的价值网络权重。
        """
        new_weights = [w.copy() for w in value_weights]

        for state, target in zip(states, returns):
            pred = self._value_forward(state, new_weights)
            error = pred - target

            # 简化梯度更新
            new_weights = self._value_gradient_step(
                new_weights, state, error,
            )

        return new_weights

    def _value_gradient_step(
        self,
        weights: list[np.ndarray],
        state: np.ndarray,
        error: float,
    ) -> list[np.ndarray]:
        """执行价值网络的单步梯度更新。

        Args:
            weights: 当前权重。
            state: 输入状态。
            error: 价值预测误差。

        Returns:
            更新后的权重。
        """
        new_weights = [w.copy() for w in weights]
        num_layers = len(weights) // 2

        # 前向传播保存激活值
        activations = [state.copy()]
        h = state.copy()

        for i in range(num_layers):
            w = weights[2 * i]
            b = weights[2 * i + 1]
            h = h @ w + b
            if i < num_layers - 1:
                h = np.maximum(0, h)
            activations.append(h.copy())

        # 反向传播
        grad = np.array([error * self.value_coef])

        for i in range(num_layers - 1, -1, -1):
            w = weights[2 * i]
            b = weights[2 * i + 1]
            prev_h = activations[i]

            grad_w = np.outer(prev_h, grad)
            grad_b = grad.copy()

            new_weights[2 * i] = w + self.learning_rate * grad_w
            new_weights[2 * i + 1] = b + self.learning_rate * grad_b

            if i > 0:
                grad = w @ grad
                relu_mask = (activations[i] > 0).astype(float)
                grad = grad * relu_mask

        return new_weights

    def _trajectory_to_path(
        self,
        trajectory: list[tuple],
        start: tuple[int, int],
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """将轨迹数据转换为路径点列表。

        Args:
            trajectory: 轨迹数据。
            start: 起点。
            rows: 网格行数。
            cols: 网格列数。

        Returns:
            路径点列表。
        """
        path = [list(start)]
        for state, action_idx, reward, next_state, done in trajectory:
            next_x = int(np.clip(next_state[0] * rows, 0, rows - 1))
            next_y = int(np.clip(next_state[1] * cols, 0, cols - 1))
            if [next_x, next_y] != path[-1]:
                path.append([next_x, next_y])
        return path

    def _extract_policy_path(
        self,
        policy_weights: list[np.ndarray],
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[list[int]]:
        """使用训练好的策略网络提取贪心路径。

        Args:
            policy_weights: 策略网络权重。
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
                [current[0] / rows, current[1] / cols,
                 goal[0] / rows, goal[1] / cols],
                dtype=np.float64,
            )
            probs = self._policy_forward(state, policy_weights)

            # 按概率排序尝试动作
            sorted_actions = np.argsort(probs)[::-1]

            moved = False
            for action_idx in sorted_actions:
                dx, dy = self.actions[int(action_idx)]
                nx = int(np.clip(current[0] + dx, 0, rows - 1))
                ny = int(np.clip(current[1] + dy, 0, cols - 1))

                if ((nx, ny) not in obstacles
                        and (nx, ny) not in visited
                        and 0 <= nx < rows and 0 <= ny < cols):
                    current = (nx, ny)
                    path.append([nx, ny])
                    visited.add(current)
                    moved = True
                    break

            if not moved:
                break

        return path

    def _compute_policy_distribution(
        self,
        policy_weights: list[np.ndarray],
        path: list[list[int]],
        rows: int,
        cols: int,
    ) -> list[list[float]]:
        """计算路径上各状态的动作策略概率分布。

        Args:
            policy_weights: 策略网络权重。
            path: 路径点列表。
            rows: 网格行数。
            cols: 网格列数。

        Returns:
            各路径点的动作概率分布列表。
        """
        if not path:
            return []

        policy_probs = []
        for point in path:
            state = np.array(
                [point[0] / rows, point[1] / cols,
                 point[0] / rows, point[1] / cols],
                dtype=np.float64,
            )
            probs = self._policy_forward(state, policy_weights)
            policy_probs.append([float(p) for p in probs])

        return policy_probs

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
        for point in path:
            pos = (point[0], point[1])
            if pos in obstacles:
                reward -= 10.0
            elif pos == goal:
                reward += 100.0
            else:
                reward -= 1.0

        reward -= len(path) * 0.1
        return reward
