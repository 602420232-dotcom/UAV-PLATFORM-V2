#!/usr/bin/env python3
"""
强化学习路径规划
使用DQN和PPO算法进行路径规划优化
"""

import numpy as np
import json
import sys
import os
import logging
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Flatten, Input
from tensorflow.keras.optimizers import Adam
from collections import deque
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DQNPlanner:
    """
    DQN路径规划器
    """
    def __init__(self, state_size=6, action_size=4, model_path=None):
        """
        初始化DQN规划器
        :param state_size: 状态空间大小
        :param action_size: 动作空间大小
        :param model_path: 模型保存路径
        """
        self.state_size = state_size
        self.action_size = action_size
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.model_path, exist_ok=True)
        
        # 经验回放缓冲区
        self.memory = deque(maxlen=10000)
        
        # 超参数
        self.gamma = 0.95  # 折扣因子
        self.epsilon = 1.0  # 探索率
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        
        # 创建模型
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
    
    def _build_model(self):
        """
        构建DQN模型
        """
        model = Sequential()
        model.add(Input(shape=(self.state_size,)))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model
    
    def update_target_model(self):
        """
        更新目标网络
        """
        self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, state, action, reward, next_state, done):
        """
        存储经验
        """
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        """
        选择动作
        """
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(np.array([state]), verbose=0)
        return np.argmax(act_values[0])
    
    def replay(self, batch_size=32):
        """
        经验回放
        """
        minibatch = random.sample(self.memory, min(len(self.memory), batch_size))
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(self.target_model.predict(np.array([next_state]), verbose=0)[0])
            target_f = self.model.predict(np.array([state]), verbose=0)
            target_f[0][action] = target
            self.model.fit(np.array([state]), target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def train(self, env, episodes=1000, batch_size=32):
        """
        训练模型
        """
        for e in range(episodes):
            state = env.reset()
            state = np.reshape(state, [1, self.state_size])
            done = False
            score = 0
            
            while not done:
                action = self.act(state[0])
                next_state, reward, done, _ = env.step(action)
                next_state = np.reshape(next_state, [1, self.state_size])
                self.remember(state[0], action, reward, next_state[0], done)
                state = next_state
                score += reward
                
                if len(self.memory) > batch_size:
                    self.replay(batch_size)
            
            if e % 10 == 0:
                self.update_target_model()
                logger.info(f"Episode: {e}, Score: {score}, Epsilon: {self.epsilon:.4f}")
        
        # 保存模型
        model_path = os.path.join(self.model_path, 'dqn_model.h5')
        self.model.save(model_path)
        logger.info(f"DQN模型保存成功: {model_path}")
    
    def load_model(self):
        """
        加载模型
        """
        model_path = os.path.join(self.model_path, 'dqn_model.h5')
        if os.path.exists(model_path):
            self.model = load_model(model_path)
            self.target_model = load_model(model_path)
            logger.info(f"DQN模型加载成功: {model_path}")
        else:
            logger.warning(f"DQN模型文件不存在: {model_path}")
    
    def plan(self, state):
        """
        执行路径规划
        """
        state = np.reshape(state, [1, self.state_size])
        act_values = self.model.predict(state, verbose=0)
        return np.argmax(act_values[0])

class PPOPlanner:
    """
    PPO路径规划器
    """
    def __init__(self, state_size=6, action_size=4, model_path=None):
        """
        初始化PPO规划器
        :param state_size: 状态空间大小
        :param action_size: 动作空间大小
        :param model_path: 模型保存路径
        """
        self.state_size = state_size
        self.action_size = action_size
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.model_path, exist_ok=True)
        
        # 超参数
        self.gamma = 0.99
        self.lam = 0.95
        self.clip_epsilon = 0.2
        self.learning_rate = 3e-4
        self.batch_size = 64
        self.epochs = 4
        
        # 创建模型
        self.actor = self._build_actor()
        self.critic = self._build_critic()
    
    def _build_actor(self):
        """
        构建Actor模型
        """
        model = Sequential()
        model.add(Input(shape=(self.state_size,)))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(self.action_size, activation='softmax'))
        model.compile(loss='categorical_crossentropy', optimizer=Adam(learning_rate=self.learning_rate))
        return model
    
    def _build_critic(self):
        """
        构建Critic模型
        """
        model = Sequential()
        model.add(Input(shape=(self.state_size,)))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(1, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model
    
    def get_action(self, state):
        """
        获取动作
        """
        state = np.reshape(state, [1, self.state_size])
        probs = self.actor.predict(state, verbose=0)[0]
        return np.random.choice(self.action_size, p=probs), probs
    
    def train(self, env, episodes=1000):
        """
        训练模型
        """
        for e in range(episodes):
            state = env.reset()
            done = False
            score = 0
            states = []
            actions = []
            old_probs = []
            rewards = []
            values = []
            
            while not done:
                action, prob = self.get_action(state)
                next_state, reward, done, _ = env.step(action)
                
                # 获取状态值
                value = self.critic.predict(np.reshape(state, [1, self.state_size]), verbose=0)[0][0]
                
                states.append(state)
                actions.append(action)
                old_probs.append(prob)
                rewards.append(reward)
                values.append(value)
                
                state = next_state
                score += reward
            
            # 计算GAE
            returns = []
            advantages = []
            last_value = self.critic.predict(np.reshape(state, [1, self.state_size]), verbose=0)[0][0]
            G = last_value
            for i in reversed(range(len(rewards))):
                G = rewards[i] + self.gamma * G
                returns.insert(0, G)
                td_error = rewards[i] + self.gamma * last_value - values[i]
                advantages.insert(0, td_error)
                last_value = values[i]
            
            # 归一化优势
            advantages = np.array(advantages)
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
            
            # 训练模型
            for _ in range(self.epochs):
                indices = np.arange(len(states))
                np.random.shuffle(indices)
                
                for start in range(0, len(states), self.batch_size):
                    end = start + self.batch_size
                    batch_indices = indices[start:end]
                    
                    batch_states = np.array([states[i] for i in batch_indices])
                    batch_actions = np.array([actions[i] for i in batch_indices])
                    batch_old_probs = np.array([old_probs[i] for i in batch_indices])
                    batch_returns = np.array([returns[i] for i in batch_indices])
                    batch_advantages = np.array([advantages[i] for i in batch_indices])
                    
                    # 训练Actor
                    with tf.GradientTape() as tape:
                        new_probs = self.actor(batch_states)
                        action_masks = tf.one_hot(batch_actions, self.action_size)
                        old_action_probs = tf.reduce_sum(batch_old_probs * action_masks, axis=1)
                        new_action_probs = tf.reduce_sum(new_probs * action_masks, axis=1)
                        
                        ratio = new_action_probs / old_action_probs
                        surr1 = ratio * batch_advantages
                        surr2 = tf.clip_by_value(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                        actor_loss = -tf.reduce_mean(tf.minimum(surr1, surr2))
                    
                    actor_grads = tape.gradient(actor_loss, self.actor.trainable_variables)
                    self.actor.optimizer.apply_gradients(zip(actor_grads, self.actor.trainable_variables))
                    
                    # 训练Critic
                    with tf.GradientTape() as tape:
                        values = self.critic(batch_states)
                        critic_loss = tf.reduce_mean(tf.square(batch_returns - values))
                    
                    critic_grads = tape.gradient(critic_loss, self.critic.trainable_variables)
                    self.critic.optimizer.apply_gradients(zip(critic_grads, self.critic.trainable_variables))
            
            if e % 10 == 0:
                logger.info(f"Episode: {e}, Score: {score}")
        
        # 保存模型
        actor_path = os.path.join(self.model_path, 'ppo_actor.h5')
        critic_path = os.path.join(self.model_path, 'ppo_critic.h5')
        self.actor.save(actor_path)
        self.critic.save(critic_path)
        logger.info(f"PPO模型保存成功: {actor_path}, {critic_path}")
    
    def load_model(self):
        """
        加载模型
        """
        actor_path = os.path.join(self.model_path, 'ppo_actor.h5')
        critic_path = os.path.join(self.model_path, 'ppo_critic.h5')
        
        if os.path.exists(actor_path) and os.path.exists(critic_path):
            self.actor = load_model(actor_path)
            self.critic = load_model(critic_path)
            logger.info(f"PPO模型加载成功: {actor_path}, {critic_path}")
        else:
            logger.warning(f"PPO模型文件不存在: {actor_path}, {critic_path}")
    
    def plan(self, state):
        """
        执行路径规划
        """
        state = np.reshape(state, [1, self.state_size])
        probs = self.actor.predict(state, verbose=0)[0]
        return np.argmax(probs)

class PathPlanningEnv:
    """
    路径规划环境
    """
    def __init__(self, start, goal, obstacles, no_fly_zones):
        """
        初始化环境
        :param start: 起始位置
        :param goal: 目标位置
        :param obstacles: 障碍物
        :param no_fly_zones: 禁飞区
        """
        self.start = start
        self.goal = goal
        self.obstacles = obstacles
        self.no_fly_zones = no_fly_zones
        self.current_position = start
        self.step_count = 0
        self.max_steps = 100
    
    def reset(self):
        """
        重置环境
        """
        self.current_position = self.start
        self.step_count = 0
        return self._get_state()
    
    def _get_state(self):
        """
        获取状态
        """
        # 状态包括：当前位置、目标位置、到最近障碍物的距离
        state = list(self.current_position)
        state.extend(self.goal)
        
        # 计算到最近障碍物的距离
        min_obstacle_dist = float('inf')
        for obstacle in self.obstacles:
            dist = np.sqrt((self.current_position[0] - obstacle.location[0])**2 + 
                         (self.current_position[1] - obstacle.location[1])**2) - obstacle.radius
            min_obstacle_dist = min(min_obstacle_dist, dist)
        
        # 计算到最近禁飞区的距离
        min_nfz_dist = float('inf')
        for nfz in self.no_fly_zones:
            dist = np.sqrt((self.current_position[0] - nfz.location[0])**2 + 
                         (self.current_position[1] - nfz.location[1])**2) - nfz.radius
            min_nfz_dist = min(min_nfz_dist, dist)
        
        state.append(max(0, min_obstacle_dist))
        state.append(max(0, min_nfz_dist))
        
        return state
    
    def step(self, action):
        """
        执行动作
        """
        # 动作：0-上，1-右，2-下，3-左
        actions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        move = actions[action]
        
        # 计算新位置
        new_position = (self.current_position[0] + move[0], self.current_position[1] + move[1])
        
        # 检查是否碰撞
        collision = False
        for obstacle in self.obstacles:
            dist = np.sqrt((new_position[0] - obstacle.location[0])**2 + 
                         (new_position[1] - obstacle.location[1])**2)
            if dist < obstacle.radius:
                collision = True
                break
        
        for nfz in self.no_fly_zones:
            dist = np.sqrt((new_position[0] - nfz.location[0])**2 + 
                         (new_position[1] - nfz.location[1])**2)
            if dist < nfz.radius:
                collision = True
                break
        
        # 计算奖励
        if collision:
            reward = -10  # 碰撞惩罚
            new_position = self.current_position  # 保持原位置
        else:
            # 距离奖励
            old_dist = np.sqrt((self.current_position[0] - self.goal[0])**2 + 
                             (self.current_position[1] - self.goal[1])**2)
            new_dist = np.sqrt((new_position[0] - self.goal[0])**2 + 
                             (new_position[1] - self.goal[1])**2)
            distance_reward = (old_dist - new_dist) * 10
            
            # 时间惩罚
            time_penalty = -0.1
            
            reward = distance_reward + time_penalty
            
            # 到达目标奖励
            if new_dist < 1.0:
                reward += 100
        
        # 更新状态
        self.current_position = new_position
        self.step_count += 1
        
        # 检查是否完成
        done = False
        if np.sqrt((self.current_position[0] - self.goal[0])**2 + 
                 (self.current_position[1] - self.goal[1])**2) < 1.0:
            done = True
        elif self.step_count >= self.max_steps:
            done = True
            reward -= 50  # 超时惩罚
        
        return self._get_state(), reward, done, {}

class ReinforcementLearningPlanner:
    """
    强化学习路径规划器
    """
    def __init__(self, algorithm='dqn'):
        """
        初始化强化学习规划器
        :param algorithm: 算法类型 ('dqn' 或 'ppo')
        """
        self.algorithm = algorithm
        self.planner = None
    
    def initialize(self, state_size=6, action_size=4):
        """
        初始化规划器
        """
        if self.algorithm == 'dqn':
            self.planner = DQNPlanner(state_size, action_size)
        elif self.algorithm == 'ppo':
            self.planner = PPOPlanner(state_size, action_size)
        else:
            raise ValueError(f"不支持的算法: {self.algorithm}")
    
    def train(self, env, episodes=1000):
        """
        训练模型
        """
        if not self.planner:
            self.initialize()
        self.planner.train(env, episodes)
    
    def load_model(self):
        """
        加载模型
        """
        if not self.planner:
            self.initialize()
        self.planner.load_model()
    
    def plan(self, state):
        """
        执行路径规划
        """
        if not self.planner:
            self.initialize()
            self.load_model()
        return self.planner.plan(state)
    
    def self_improve(self, env, episodes=100):
        """
        自迭代改进
        """
        if not self.planner:
            self.initialize()
            self.load_model()
        
        # 继续训练以改进模型
        self.planner.train(env, episodes)
        logger.info("模型自迭代改进完成")

def load_input(file_index):
    """从文件加载JSON输入数据，防止命令注入"""
    if len(sys.argv) <= file_index:
        return {}
    file_path = sys.argv[file_index]
    with open(file_path, 'r') as f:
        return json.load(f)


def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': '缺少命令参数'
        }))
        return
    
    command = sys.argv[1]
    
    if command == 'train':
        # 训练命令
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少训练配置'
            }))
            return
        
        try:
            config = load_input(2)
            algorithm = config.get('algorithm', 'dqn')
            episodes = config.get('episodes', 1000)
            
            # 创建环境
            from three_layer_planner import Obstacle, NoFlyZone
            start = tuple(config.get('start', (0, 0)))
            goal = tuple(config.get('goal', (10, 10)))
            obstacles = [Obstacle(tuple(o['location']), o['radius']) for o in config.get('obstacles', [])]
            no_fly_zones = [NoFlyZone(tuple(n['location']), n['radius']) for n in config.get('no_fly_zones', [])]
            
            env = PathPlanningEnv(start, goal, obstacles, no_fly_zones)
            
            # 训练模型
            planner = ReinforcementLearningPlanner(algorithm)
            planner.train(env, episodes)
            
            print(json.dumps({
                'success': True,
                'message': f'{algorithm}模型训练完成'
            }))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    elif command == 'plan':
        # 规划命令
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少规划配置'
            }))
            return
        
        try:
            config = load_input(2)
            algorithm = config.get('algorithm', 'dqn')
            state = config.get('state', [0, 0, 10, 10, 10, 10])
            
            # 执行规划
            planner = ReinforcementLearningPlanner(algorithm)
            action = planner.plan(state)
            
            print(json.dumps({
                'success': True,
                'action': action
            }))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    elif command == 'improve':
        # 自迭代改进命令
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少改进配置'
            }))
            return
        
        try:
            config = load_input(2)
            algorithm = config.get('algorithm', 'dqn')
            episodes = config.get('episodes', 100)
            
            # 创建环境
            from three_layer_planner import Obstacle, NoFlyZone
            start = tuple(config.get('start', (0, 0)))
            goal = tuple(config.get('goal', (10, 10)))
            obstacles = [Obstacle(tuple(o['location']), o['radius']) for o in config.get('obstacles', [])]
            no_fly_zones = [NoFlyZone(tuple(n['location']), n['radius']) for n in config.get('no_fly_zones', [])]
            
            env = PathPlanningEnv(start, goal, obstacles, no_fly_zones)
            
            # 自迭代改进
            planner = ReinforcementLearningPlanner(algorithm)
            planner.self_improve(env, episodes)
            
            print(json.dumps({
                'success': True,
                'message': f'{algorithm}模型自迭代改进完成'
            }))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    else:
        print(json.dumps({
            'success': False,
            'error': '未知命令'
        }))

if __name__ == "__main__":
    main()
