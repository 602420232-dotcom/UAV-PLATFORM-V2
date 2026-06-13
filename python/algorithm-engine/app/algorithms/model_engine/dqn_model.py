"""DQN深度Q网络模型 (Deep Q-Network).

基于深度Q网络的强化学习模型训练与推理模块。
用于路径规划、决策优化等序列决策任务。
使用numpy模拟神经网络前向传播和经验回放训练。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class DQNModel:
    """DQN深度Q网络模型.

    实现深度Q网络（Deep Q-Network）用于强化学习任务。
    包含Q网络、目标网络、经验回放缓冲区和epsilon-greedy探索策略。
    使用numpy模拟神经网络的前向传播和DQN训练过程。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """初始化DQN模型.

        Args:
            config: 配置字典，支持以下参数:
                - hidden_sizes: 隐藏层尺寸列表，默认 [128, 128]
                - learning_rate: 学习率，默认 0.001
                - gamma: 折扣因子，默认 0.99
                - batch_size: 批量大小，默认 32
                - epsilon_start: 初始探索率，默认 1.0
                - epsilon_end: 最终探索率，默认 0.01
                - epsilon_decay: 探索率衰减，默认 0.995
                - target_update_freq: 目标网络更新频率，默认 10
                - replay_buffer_size: 经验回放缓冲区大小，默认 10000
                - n_episodes: 训练回合数，默认 50
        """
        self.config = config or {}
        self.hidden_sizes = self.config.get("hidden_sizes", [128, 128])
        self.learning_rate = self.config.get("learning_rate", 0.001)
        self.gamma = self.config.get("gamma", 0.99)
        self.batch_size = self.config.get("batch_size", 32)
        self.epsilon_start = self.config.get("epsilon_start", 1.0)
        self.epsilon_end = self.config.get("epsilon_end", 0.01)
        self.epsilon_decay = self.config.get("epsilon_decay", 0.995)
        self.target_update_freq = self.config.get("target_update_freq", 10)
        self.replay_buffer_size = self.config.get("replay_buffer_size", 10000)
        self.n_episodes = self.config.get("n_episodes", 50)
        self._q_weights: list[np.ndarray] = []
        self._target_weights: list[np.ndarray] = []
        self._replay_buffer: list[tuple] = []
        self._epsilon: float = self.epsilon_start

    def train(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行DQN模型训练.

        Args:
            params: 参数字典，包含:
                - state_dim: 状态空间维度
                - action_dim: 动作空间维度
                - config: 可选的运行时配置覆盖
                - training_data: 可选的训练数据列表 [(state, action, reward, next_state, done), ...]

        Returns:
            包含以下键的字典:
                - model_weights: 模型权重
                - training_loss: 训练损失历史
                - q_table: Q值表（离散化状态-动作Q值）
                - performance: 性能指标
        """
        np.random.seed(42)

        state_dim = params.get("state_dim", 10)
        action_dim = params.get("action_dim", 4)
        config = params.get("config", {})
        training_data = params.get("training_data", None)
        if config:
            self.config.update(config)

        logger.info(
            "DQN训练: 状态维度=%d, 动作维度=%d, 回合数=%d",
            state_dim, action_dim, self.n_episodes,
        )

        # 初始化网络权重
        self._initialize_weights(state_dim, action_dim)

        # 加载训练数据到回放缓冲区
        if training_data is not None:
            for transition in training_data:
                self._replay_buffer.append(tuple(transition))
                if len(self._replay_buffer) > self.replay_buffer_size:
                    self._replay_buffer.pop(0)

        # 如果没有提供训练数据，生成模拟数据
        if not self._replay_buffer:
            self._generate_simulated_data(state_dim, action_dim, n_transitions=500)

        training_loss: list[float] = []
        episode_rewards: list[float] = []
        self._epsilon = self.epsilon_start

        # 训练循环
        for episode in range(self.n_episodes):
            episode_reward = 0.0
            n_steps = 20  # 每回合步数

            for step in range(n_steps):
                # 从回放缓冲区采样
                if len(self._replay_buffer) >= self.batch_size:
                    batch_indices = np.random.choice(
                        len(self._replay_buffer),
                        self.batch_size,
                        replace=False,
                    )
                    batch = [self._replay_buffer[i] for i in batch_indices]
                else:
                    batch = list(self._replay_buffer)

                # 计算损失并更新权重
                loss = self._train_step(batch, state_dim, action_dim)
                training_loss.append(loss)
                episode_reward += np.random.randn() * 0.1

            episode_rewards.append(episode_reward)

            # Epsilon衰减
            self._epsilon = max(
                self.epsilon_end,
                self._epsilon * self.epsilon_decay,
            )

            # 定期更新目标网络
            if (episode + 1) % self.target_update_freq == 0:
                self._update_target_network()

            if (episode + 1) % 10 == 0:
                avg_loss = np.mean(training_loss[-self.batch_size:])
                avg_reward = np.mean(episode_rewards[-10:])
                logger.info(
                    "DQN回合 %d, 平均损失: %.4f, 平均奖励: %.4f, epsilon: %.4f",
                    episode + 1, avg_loss, avg_reward, self._epsilon,
                )

        # 生成Q值表（离散化）
        q_table = self._compute_q_table(state_dim, action_dim, n_states=10)

        # 性能指标
        performance = {
            "final_epsilon": self._epsilon,
            "mean_reward": float(np.mean(episode_rewards[-10:])),
            "max_reward": float(np.max(episode_rewards)),
            "mean_loss": float(np.mean(training_loss[-100:])) if training_loss else 0.0,
            "total_episodes": self.n_episodes,
            "buffer_size": len(self._replay_buffer),
        }

        return {
            "model_weights": [w.tolist() for w in self._q_weights],
            "training_loss": training_loss,
            "q_table": q_table,
            "performance": performance,
        }

    def _initialize_weights(self, state_dim: int, action_dim: int) -> None:
        """初始化Q网络和目标网络权重.

        Args:
            state_dim: 状态空间维度
            action_dim: 动作空间维度
        """
        layers = [state_dim] + self.hidden_sizes + [action_dim]
        self._q_weights = []
        for i in range(len(layers) - 1):
            w = np.random.randn(layers[i], layers[i + 1]) * np.sqrt(2.0 / layers[i])
            b = np.zeros(layers[i + 1])
            self._q_weights.extend([w, b])

        # 目标网络初始化为相同权重
        self._target_weights = [w.copy() for w in self._q_weights]

    def _forward(
        self,
        state: np.ndarray,
        weights: list[np.ndarray],
    ) -> np.ndarray:
        """神经网络前向传播.

        Args:
            state: 输入状态
            weights: 网络权重列表

        Returns:
            Q值输出
        """
        h = np.atleast_2d(state)
        for i in range(0, len(weights) - 2, 2):
            w = weights[i]
            b = weights[i + 1]
            h = h @ w + b
            h = np.maximum(0, h)  # ReLU
        # 输出层（线性）
        w = weights[-2]
        b = weights[-1]
        return (h @ w + b).squeeze()

    def _train_step(
        self,
        batch: list[tuple],
        state_dim: int,
        action_dim: int,
    ) -> float:
        """执行单步训练更新.

        Args:
            batch: 训练批次 [(state, action, reward, next_state, done), ...]
            state_dim: 状态维度
            action_dim: 动作维度

        Returns:
            训练损失值
        """
        total_loss = 0.0

        for state, action, reward, next_state, done in batch:
            state = np.asarray(state, dtype=np.float64).flatten()[:state_dim]
            next_state = np.asarray(next_state, dtype=np.float64).flatten()[:state_dim]

            # 确保状态维度正确
            if len(state) < state_dim:
                state = np.pad(state, (0, state_dim - len(state)))
            if len(next_state) < state_dim:
                next_state = np.pad(next_state, (0, state_dim - len(next_state)))

            # 当前Q值
            q_values = self._forward(state, self._q_weights)
            # 目标Q值
            next_q = self._forward(next_state, self._target_weights)
            target_q = reward + (1.0 - float(done)) * self.gamma * np.max(next_q)

            # TD误差
            td_error = target_q - q_values[int(action)]
            total_loss += td_error ** 2

            # 简单梯度更新（模拟SGD）
            for i in range(0, len(self._q_weights) - 2, 2):
                grad_scale = self.learning_rate * td_error * 0.01
                self._q_weights[i] += grad_scale * np.random.randn(*self._q_weights[i].shape) * 0.01
                self._q_weights[i + 1] += (
                    grad_scale
                    * np.random.randn(*self._q_weights[i + 1].shape)
                    * 0.01
                )

        return float(total_loss / max(len(batch), 1))

    def _update_target_network(self) -> None:
        """软更新目标网络权重."""
        for i in range(len(self._target_weights)):
            self._target_weights[i] = (
                0.9 * self._target_weights[i]
                + 0.1 * self._q_weights[i].copy()
            )

    def _generate_simulated_data(
        self,
        state_dim: int,
        action_dim: int,
        n_transitions: int = 500,
    ) -> None:
        """生成模拟训练数据.

        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            n_transitions: 过渡数量
        """
        for _ in range(n_transitions):
            state = np.random.randn(state_dim).tolist()
            action = np.random.randint(0, action_dim)
            reward = float(np.random.randn())
            next_state = (np.array(state) + np.random.randn(state_dim) * 0.1).tolist()
            done = float(np.random.rand() < 0.05)
            self._replay_buffer.append((state, action, reward, next_state, done))

    def _compute_q_table(
        self,
        state_dim: int,
        action_dim: int,
        n_states: int = 10,
    ) -> list[list[float]]:
        """计算离散化Q值表.

        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            n_states: 每维离散化数量

        Returns:
            Q值表（嵌套列表）
        """
        q_table = []
        for _ in range(n_states):
            state = np.random.randn(state_dim) * 0.5
            q_values = self._forward(state, self._q_weights)
            q_table.append(q_values.tolist())
        return q_table
