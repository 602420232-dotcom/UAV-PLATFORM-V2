# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, List, Any, Optional, Callable, Tuple

﻿"""
性能基准测试脚本
用法: python benchmark.py [--grid small|medium|large]
"""
import argparse
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../algorithm_core/src'))

import numpy as np


def benchmark_3dvar(grid_size: str, obs_count: int):
    from bayesian_assimilation.core.assimilator import BayesianAssimilator
    assim = BayesianAssimilator()
    assim.initialize_grid(domain_size=grid_size)
    bg = np.random.rand(*grid_size)
    obs = np.random.rand(obs_count)
    obs_loc = np.random.rand(obs_count, 3)
    start = time.perf_counter()
    analysis, variance = assim.assimilate_3dvar(bg, obs, obs_loc)
    elapsed = time.perf_counter() - start
    return elapsed, analysis.shape, variance.shape


def main():
    parser = argparse.ArgumentParser(description="贝叶斯同化性能测试")
    parser.add_argument("--grid", choices=["small", "medium", "large"],
                        default="small", help="网格规模")
    args = parser.parse_args()

    configs = {
        "small": {"shape": (50, 50, 20), "obs": 500},
        "medium": {"shape": (100, 100, 50), "obs": 2000},
        "large": {"shape": (200, 200, 100), "obs": 5000},
    }
    cfg = configs[args.grid]
    nx, ny, nz = cfg["shape"]
    logger.info(f"测试 3D-VAR [{nx}x{ny}x{nz}, obs={cfg['obs']}]")
    elapsed, shape, v_shape = benchmark_3dvar(cfg["shape"], cfg["obs"])
    logger.info(f"耗时: {elapsed:.3f}s, 分析场: {shape}, 方差场: {v_shape}")


if __name__ == "__main__":
    main()

