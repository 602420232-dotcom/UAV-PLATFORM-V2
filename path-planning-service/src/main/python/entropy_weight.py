#!/usr/bin/env python3
"""
熵权法多目标权重自动分配

基于各候选解在多个目标上的变异程度，自动计算客观权重。
熵值越小 → 信息量越大 → 权重越高。
"""
from typing import List, Dict, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


def entropy_weight(objectives_matrix: List[List[float]]
                   ) -> Tuple[List[float], List[float], List[float]]:
    """
    使用熵权法计算多目标权重

    Args:
        objectives_matrix: 目标矩阵，shape=(n_solutions, n_objectives)
                          每行是一个候选解，每列是一个目标维度的值

    Returns:
        (weights, entropy, redundancy) 元组:
            weights: 各目标的权重列表（和为1）
            entropy: 各目标的熵值
            redundancy: 各目标的信息冗余度
    """
    matrix = np.array(objectives_matrix, dtype=float)
    n_solutions, n_objectives = matrix.shape

    # 1. Min-Max归一化（正向指标）
    normalized = np.zeros_like(matrix)
    for j in range(n_objectives):
        col = matrix[:, j]
        min_val = col.min()
        max_val = col.max()
        if max_val - min_val < 1e-10:
            normalized[:, j] = 1.0
        else:
            normalized[:, j] = (col - min_val) / (max_val - min_val) + 0.0001  # 避免0值

    # 2. 计算概率矩阵 (特征比重)
    p_matrix = normalized / normalized.sum(axis=0, keepdims=True)

    # 3. 计算各目标的熵值
    # e_j = -k * Σ(p_ij * ln(p_ij)), k = 1/ln(n)
    k = 1.0 / np.log(n_solutions)
    entropy = -k * np.sum(p_matrix * np.log(p_matrix), axis=0)
    entropy = np.clip(entropy, 0, 1)

    # 4. 计算信息冗余度
    redundancy = 1 - entropy

    # 5. 计算权重
    total_redundancy = redundancy.sum()
    if total_redundancy < 1e-10:
        weights = np.ones(n_objectives) / n_objectives
    else:
        weights = redundancy / total_redundancy

    return (weights.tolist(), entropy.tolist(), redundancy.tolist())


def compute_weighted_score(objectives: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    计算加权综合得分

    Args:
        objectives: 目标维度名到值的映射
        weights: 目标维度名到权重的映射

    Returns:
        加权综合得分（越小越好）
    """
    score = 0.0
    for key, value in objectives.items():
        weight = weights.get(key, 0.0)
        score += weight * value
    return score


def auto_assign_weights(candidate_scores: List[Dict[str, float]],
                        objective_names: List[str]) -> Dict[str, float]:
    """
    自动为多目标分配熵权法权重

    Args:
        candidate_scores: 候选解列表，每个元素是 {目标名: 值}
        objective_names: 目标维度名称列表

    Returns:
        目标名到权重的映射
    """
    if not candidate_scores:
        return {name: 1.0 / len(objective_names) for name in objective_names}

    # 构建目标矩阵
    matrix = []
    for solution in candidate_scores:
        row = [solution.get(name, 0) for name in objective_names]
        matrix.append(row)

    weights, _, _ = entropy_weight(matrix)
    return {objective_names[i]: weights[i] for i in range(len(objective_names))}


if __name__ == "__main__":
    # 演示
    solutions = [
        {'distance': 100.0, 'time': 10.0, 'risk': 5.0, 'energy': 50.0},
        {'distance': 120.0, 'time': 12.0, 'risk': 3.0, 'energy': 55.0},
        {'distance': 90.0, 'time': 9.0, 'risk': 8.0, 'energy': 45.0},
        {'distance': 150.0, 'time': 15.0, 'risk': 2.0, 'energy': 60.0},
    ]
    names = ['distance', 'time', 'risk', 'energy']
    weights = auto_assign_weights(solutions, names)
    logger.info("熵权法自动分配权重:")
    for name, weight in weights.items():
        print(f"  {name}: {weight:.4f}")
