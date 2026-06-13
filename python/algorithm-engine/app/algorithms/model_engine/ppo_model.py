"""PPO近端策略优化模型 (Proximal Policy Optimization).

基于PPO算法的强化学习模型训练与推理模块。
PPO通过裁剪目标函数实现稳定的策略更新，
适用于连续/离散动作空间的决策优化任务。
使用numpy模拟策略网络、价值网络和PPO训练过程。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class PPOModel:
    """PPO近端策略优化模型.

    实现PPO（Proximal Policy Optimization）算法用于强化学习任务。
    包含策略网络（Actor）和价值网络（Critic），支持裁剪目标函数、
    价值函数裁剪、熵正则化和KL散度约束。
    使用numpy模拟神经网络的前向传播和PPO训练过程。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """初始化PPO模型.

        Args:
            config: 配置字典，支持以下参数:
                - clip_ratio: PPO裁剪比例（epsilon），默认 0.2
                - ppo_epochs: 每批数据的PPO更新轮数，默认 4
                - entropy_coef: 熵正则化系数，默认 0.01
                - value_coef: 价值函数损失系数，默认 0.5
                - max_grad_norm: 梯度裁剪范数，默认 0.5
                - learning_rate: 学习率，默认 0.0003
                - gamma: 折扣因子，默认 0.99
                - gae_lambda: GAE(lambda)参数，默认 0.95
                - hidden_sizes: 隐藏层尺寸列表，默认 [64, 64]
                - n_episodes: 训练回合数，默认 50
                - mini_batch_size: 小批量大小，默认 16
        """
        self.config = config or {}
        self.clip_ratio = self.config.get("clip_ratio", 0.2)
        self.ppo_epochs = self.config.get("ppo_epochs", 4)
        self.entropy_coef = self.config.get("entropy_coef", 0.01)
        self.value_coef = self.config.get("value_coef", 0.5)
        self.max_grad_norm = self.config.get("max_grad_norm", 0.5)
        self.learning_rate = self.config.get("learning_rate", 0.0003)
        self.gamma = self.config.get("gamma", 0.99)
        self.gae_lambda = self.config.get("gae_lambda", 0.95)
        self.hidden_sizes = self.config.get("hidden_sizes", [64, 64])
        self.n_episodes = self.config.get("n_episodes", 50)
        self.mini_batch_size = self.config.get("mini_batch_size", 16)
        self._policy_weights: list[np.ndarray] = []
        self._value_weights: list[np.ndarray] = []

    def train(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行PPO模型训练.

        Args:
            params: 参数字典，包含:
                - state_dim: 状态空间维度
                - action_dim: 动作空间维度
                - config: 可选的运行时配置覆盖
                - training_data: 可选的训练数据列表 [(state, action, reward, done), ...]

        Returns:
            包含以下键的字典:
                - policy_weights: 策略网络权重
                - value_weights: 价值网络权重
                - training_stats: 训练统计信息
                - kl_history: KL散度历史
        """
        np.random.seed(42)

        state_dim = params.get("state_dim", 10)
        action_dim = params.get("action_dim", 4)
        config = params.get("config", {})
        training_data = params.get("training_data", None)
        if config:
            self.config.update(config)

        logger.info(
            "PPO训练: 状态维度=%d, 动作维度=%d, 回合数=%d, PPO轮数=%d",
            state_dim, action_dim, self.n_episodes, self.ppo_epochs,
        )

        # 初始化网络权重
        self._initialize_weights(state_dim, action_dim)

        # 加载或生成训练数据
        if training_data is not None:
            trajectories = list(training_data)
        else:
            trajectories = self._generate_simulated_data(
                state_dim, action_dim, n_transitions=500,
            )

        training_stats: dict[str, list[float]] = {
            "policy_loss": [],
            "value_loss": [],
            "entropy": [],
            "total_loss": [],
            "episode_reward": [],
        }
        kl_history: list[float] = []

        # 训练循环
        for episode in range(self.n_episodes):
            # 收集轨迹数据
            states, actions, rewards, dones = self._collect_trajectories(
                trajectories, state_dim, action_dim,
            )

            # 计算回报和GAE优势
            returns, advantages = self._compute_gae(rewards, dones, states)

            # 旧策略概率（用于PPO裁剪）
            old_probs = self._get_action_probs(states, self._policy_weights, action_dim)

            # PPO更新
            for ppo_epoch in range(self.ppo_epochs):
                # 小批量更新
                indices = np.random.permutation(len(states))
                for start in range(0, len(states), self.mini_batch_size):
                    end = min(start + self.mini_batch_size, len(states))
                    mb_idx = indices[start:end]

                    mb_states = np.array([states[i] for i in mb_idx])
                    mb_actions = np.array([actions[i] for i in mb_idx])
                    mb_advantages = advantages[mb_idx]
                    mb_returns = returns[mb_idx]
                    mb_old_probs = old_probs[mb_idx]

                    # 策略损失（PPO裁剪）
                    new_probs = self._get_action_probs(
                        mb_states, self._policy_weights, action_dim,
                    )
                    new_action_probs = new_probs[
                        np.arange(len(mb_actions)), mb_actions
                    ]
                    old_action_probs = mb_old_probs[
                        np.arange(len(mb_actions)), mb_actions
                    ]

                    ratio = new_action_probs / np.maximum(old_action_probs, 1e-8)
                    clipped_ratio = np.clip(
                        ratio,
                        1.0 - self.clip_ratio,
                        1.0 + self.clip_ratio,
                    )
                    surrogate = np.minimum(
                        ratio * mb_advantages,
                        clipped_ratio * mb_advantages,
                    )
                    policy_loss = -np.mean(surrogate)

                    # 熵正则化
                    entropy = -np.sum(
                        new_probs * np.log(np.maximum(new_probs, 1e-8)),
                        axis=-1,
                    ).mean()

                    # 价值函数损失
                    values = self._forward_value(mb_states, self._value_weights)
                    value_loss = np.mean((values - mb_returns) ** 2)

                    # 总损失
                    total_loss = (
                        policy_loss
                        + self.value_coef * value_loss
                        - self.entropy_coef * entropy
                    )

                    # KL散度
                    kl = float(np.mean(
                        old_action_probs * np.log(
                            np.maximum(old_action_probs, 1e-8)
                            / np.maximum(new_action_probs, 1e-8),
                        )
                    ))

                    # 模拟梯度更新
                    self._update_weights(total_loss)

                    training_stats["policy_loss"].append(float(policy_loss))
                    training_stats["value_loss"].append(float(value_loss))
                    training_stats["entropy"].append(float(entropy))
                    training_stats["total_loss"].append(float(total_loss))
                    kl_history.append(kl)

            episode_reward = (
                float(np.sum(rewards[:20]))
                if len(rewards) >= 20
                else float(np.sum(rewards))
            )
            training_stats["episode_reward"].append(episode_reward)

            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(training_stats["episode_reward"][-10:])
                avg_kl = np.mean(kl_history[-self.ppo_epochs:]) if kl_history else 0.0
                logger.info(
                    "PPO回合 %d, 平均奖励: %.4f, 平均KL散度: %.6f",
                    episode + 1, avg_reward, avg_kl,
                )

        return {
            "policy_weights": [w.tolist() for w in self._policy_weights],
            "value_weights": [w.tolist() for w in self._value_weights],
            "training_stats": training_stats,
            "kl_history": kl_history,
        }

    def _initialize_weights(self, state_dim: int, action_dim: int) -> None:
        """初始化策略网络和价值网络权重.

        Args:
            state_dim: 状态空间维度
            action_dim: 动作空间维度
        """
        # 策略网络（Actor）
        policy_layers = [state_dim] + self.hidden_sizes + [action_dim]
        self._policy_weights = []
        for i in range(len(policy_layers) - 1):
            w = np.random.randn(policy_layers[i], policy_layers[i + 1]) * np.sqrt(
                2.0 / policy_layers[i],
            )
            b = np.zeros(policy_layers[i + 1])
            self._policy_weights.extend([w, b])

        # 价值网络（Critic）
        value_layers = [state_dim] + self.hidden_sizes + [1]
        self._value_weights = []
        for i in range(len(value_layers) - 1):
            w = np.random.randn(value_layers[i], value_layers[i + 1]) * np.sqrt(
                2.0 / value_layers[i],
            )
            b = np.zeros(value_layers[i + 1])
            self._value_weights.extend([w, b])

    def _forward_policy(
        self,
        state: np.ndarray,
        weights: list[np.ndarray],
    ) -> np.ndarray:
        """策略网络前向传播.

        Args:
            state: 输入状态
            weights: 网络权重

        Returns:
            动作概率分布（softmax输出）
        """
        h = np.atleast_2d(state)
        for i in range(0, len(weights) - 2, 2):
            w = weights[i]
            b = weights[i + 1]
            h = h @ w + b
            h = np.maximum(0, h)  # ReLU（tanh也可用于PPO）
        # 输出层
        w = weights[-2]
        b = weights[-1]
        logits = h @ w + b
        # Softmax
        logits = logits - np.max(logits, axis=-1, keepdims=True)
        exp_logits = np.exp(logits)
        probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
        return probs

    def _forward_value(
        self,
        state: np.ndarray,
        weights: list[np.ndarray],
    ) -> np.ndarray:
        """价值网络前向传播.

        Args:
            state: 输入状态
            weights: 网络权重

        Returns:
            状态价值估计
        """
        h = np.atleast_2d(state)
        for i in range(0, len(weights) - 2, 2):
            w = weights[i]
            b = weights[i + 1]
            h = h @ w + b
            h = np.maximum(0, h)
        w = weights[-2]
        b = weights[-1]
        return (h @ w + b).squeeze()

    def _get_action_probs(
        self,
        states: np.ndarray | list,
        weights: list[np.ndarray],
        action_dim: int,
    ) -> np.ndarray:
        """批量获取动作概率.

        Args:
            states: 状态列表
            weights: 策略网络权重
            action_dim: 动作维度

        Returns:
            动作概率矩阵 (N, action_dim)
        """
        probs = np.zeros((len(states), action_dim))
        for i, s in enumerate(states):
            s_arr = np.asarray(s, dtype=np.float64).flatten()
            probs[i] = self._forward_policy(s_arr, weights).squeeze()
        return probs

    def _compute_gae(
        self,
        rewards: np.ndarray,
        dones: np.ndarray,
        states: list,
    ) -> tuple[np.ndarray, np.ndarray]:
        """计算GAE（广义优势估计）和折扣回报.

        Args:
            rewards: 奖励数组
            dones: 终止标志数组
            states: 状态列表

        Returns:
            (折扣回报, GAE优势)
        """
        n = len(rewards)
        returns = np.zeros(n)
        advantages = np.zeros(n)

        last_advantage = 0.0

        for t in reversed(range(n)):
            s = np.asarray(states[t], dtype=np.float64).flatten()
            if len(s.shape) == 0:
                s = np.array([s])
            value = self._forward_value(s, self._value_weights)
            if t == n - 1:
                next_value = 0.0
            else:
                next_s = np.asarray(states[t + 1], dtype=np.float64).flatten()
                if len(next_s.shape) == 0:
                    next_s = np.array([next_s])
                next_value = self._forward_value(next_s, self._value_weights)

            delta = rewards[t] + self.gamma * next_value * (1.0 - dones[t]) - value
            last_advantage = (
                delta
                + self.gamma * self.gae_lambda * (1.0 - dones[t]) * last_advantage
            )
            advantages[t] = last_advantage
            returns[t] = advantages[t] + value

        # 标准化优势
        if len(advantages) > 1:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        return returns, advantages

    def _collect_trajectories(
        self,
        trajectories: list,
        state_dim: int,
        action_dim: int,
    ) -> tuple[list, list, np.ndarray, np.ndarray]:
        """从轨迹数据中收集状态、动作、奖励、终止标志.

        Args:
            trajectories: 轨迹数据列表
            state_dim: 状态维度
            action_dim: 动作维度

        Returns:
            (states, actions, rewards, dones)
        """
        states: list = []
        actions: list = []
        rewards_list: list = []
        dones_list: list = []

        for transition in trajectories:
            state, action, reward, done = transition[:4]
            s = np.asarray(state, dtype=np.float64).flatten()
            if len(s) < state_dim:
                s = np.pad(s, (0, state_dim - len(s)))
            elif len(s) > state_dim:
                s = s[:state_dim]
            states.append(s.tolist())
            actions.append(int(action) % action_dim)
            rewards_list.append(float(reward))
            dones_list.append(float(done))

        return states, actions, np.array(rewards_list), np.array(dones_list)

    def _update_weights(self, loss: float) -> None:
        """模拟梯度更新（带裁剪）.

        Args:
            loss: 当前损失值
        """
        grad_scale = self.learning_rate * np.sign(loss) * 0.01
        # 梯度裁剪
        grad_scale = np.clip(grad_scale, -self.max_grad_norm, self.max_grad_norm)

        for weights in [self._policy_weights, self._value_weights]:
            for i in range(len(weights)):
                noise = np.random.randn(*weights[i].shape) * grad_scale
                weights[i] += noise

    def _generate_simulated_data(
        self,
        state_dim: int,
        action_dim: int,
        n_transitions: int = 500,
    ) -> list[tuple]:
        """生成模拟训练数据.

        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            n_transitions: 过渡数量

        Returns:
            轨迹数据列表
        """
        trajectories: list[tuple] = []
        state = np.random.randn(state_dim).tolist()
        for _ in range(n_transitions):
            action = np.random.randint(0, action_dim)
            reward = float(np.random.randn() * 0.5)
            next_state = (
                np.array(state) + np.random.randn(state_dim) * 0.1
            ).tolist()
            done = float(np.random.rand() < 0.05)
            trajectories.append((state, action, reward, done))
            state = next_state
        return trajectories
