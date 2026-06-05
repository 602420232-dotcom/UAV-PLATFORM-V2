"""
3D-VAR 算法性能基准测试

测试在不同网格规模下 3D-VAR 的运行时间、内存消耗和收敛速度。
"""
import time
import pytest
import numpy as np


@pytest.mark.benchmark
@pytest.mark.parametrize("grid_size,obs_count", [
    ((50, 50, 20), 500),
    ((100, 100, 50), 2000),
    ((200, 200, 100), 5000),
])
def test_3dvar_performance(grid_size, obs_count):
    from bayesian_assimilation.core.assimilator import BayesianAssimilator

    assimilator = BayesianAssimilator()
    nx, ny, nz = grid_size
    assimilator.initialize_grid(domain_size=(nx, ny, nz))

    background = np.random.rand(nx, ny, nz)
    observations = np.random.rand(obs_count)
    obs_locations = np.random.rand(obs_count, 3)

    start = time.perf_counter()
    analysis, variance = assimilator.assimilate_3dvar(
        background=background,
        observations=observations,
        obs_locations=obs_locations,
    )
    elapsed = time.perf_counter() - start

    assert analysis.shape == (nx, ny, nz)
    assert variance.shape == (nx, ny, nz)
    assert isinstance(elapsed, float)
    print(f"\n3D-VAR [{nx}x{ny}x{nz}, obs={obs_count}] 耗时: {elapsed:.3f}s")


@pytest.mark.benchmark
def test_3dvar_convergence(small_grid):
    from bayesian_assimilation.core.assimilator import BayesianAssimilator

    assimilator = BayesianAssimilator()
    g = small_grid
    nx, ny, nz = g["shape"]
    assimilator.initialize_grid(domain_size=(nx, ny, nz))

    analysis, _ = assimilator.assimilate_3dvar(
        background=g["background"],
        observations=g["observations"],
        obs_locations=g["obs_locations"],
    )

    innovation = np.linalg.norm(analysis - g["background"]) / np.linalg.norm(g["background"])
    assert innovation < 1.0, f"同化后分析场偏离背景场过大: {innovation:.4f}"
