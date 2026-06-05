"""
4D-VAR 算法性能基准测试

测试 4D-VAR 在不同时间窗口和网格规模下的性能表现，
重点关注时间维度的扩展性。
"""
import time
import pytest
import numpy as np


@pytest.mark.benchmark
@pytest.mark.parametrize("grid_size,time_steps,obs_per_step", [
    ((30, 30, 10), 5, 100),
    ((50, 50, 20), 10, 200),
    ((100, 100, 50), 20, 500),
])
def test_4dvar_performance(grid_size, time_steps, obs_per_step):
    from bayesian_assimilation.models.four_dimensional_var import FourDimensionalVar

    model = FourDimensionalVar(
        time_window=time_steps,
        assimilation_window=3600,
    )

    nx, ny, nz = grid_size
    background_3d = np.random.rand(nx, ny, nz)
    background = np.repeat(background_3d[..., np.newaxis], time_steps, axis=-1)
    background = background.reshape(nx, ny, nz, time_steps)

    total_obs = obs_per_step * time_steps
    observations = np.random.rand(total_obs)
    obs_locations = np.random.rand(total_obs, 4)

    start = time.perf_counter()
    analysis = model.assimilate(
        background=background,
        observations=observations,
        obs_locations=obs_locations,
    )
    elapsed = time.perf_counter() - start

    assert analysis.shape == (nx, ny, nz, time_steps)
    print(f"\n4D-VAR [{nx}x{ny}x{nz}, T={time_steps}, obs={total_obs}] 耗时: {elapsed:.3f}s")


@pytest.mark.benchmark
def test_4dvar_memory_usage(small_grid):
    from bayesian_assimilation.models.four_dimensional_var import FourDimensionalVar

    model = FourDimensionalVar(time_window=5, assimilation_window=3600)
    g = small_grid
    nx, ny, nz = g["shape"]
    background = np.repeat(g["background"][..., np.newaxis], 5, axis=-1)
    background = background.reshape(nx, ny, nz, 5)

    obs_4d = np.random.rand(g["obs_count"])
    obs_loc_4d = np.random.rand(g["obs_count"], 4)

    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        model.assimilate(background=background, observations=obs_4d, obs_locations=obs_loc_4d)

        mem_after = process.memory_info().rss / 1024 / 1024
        mem_delta = mem_after - mem_before
        print(f"\n4D-VAR 内存增量: {mem_delta:.1f} MB")
        assert mem_delta < 2048, f"内存使用过高: {mem_delta:.1f} MB"
    except ImportError:
        pytest.skip("psutil 未安装，跳过内存测试")
