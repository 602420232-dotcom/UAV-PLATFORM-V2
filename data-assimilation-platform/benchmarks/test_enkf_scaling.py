"""
EnKF 算法扩展性基准测试

测试 EnKF 在不同集合大小和网格规模下的性能扩展性，
评估并行加速效果。
"""
import time
import pytest
import numpy as np


@pytest.mark.benchmark
@pytest.mark.parametrize("ensemble_size", [10, 20, 50, 100])
def test_enkf_ensemble_scaling(ensemble_size, small_grid):
    from bayesian_assimilation.models.enkf import EnKF

    enkf = EnKF(
        ensemble_size=ensemble_size,
        inflation_factor=1.05,
        localization_radius=5000,
    )

    g = small_grid
    nx, ny, nz = g["shape"]
    ensemble = np.random.rand(ensemble_size, nx, ny, nz)

    start = time.perf_counter()
    analysis_ensemble = enkf.update(
        ensemble=ensemble,
        observations=g["observations"],
        obs_locations=g["obs_locations"],
    )
    elapsed = time.perf_counter() - start

    assert analysis_ensemble.shape == (ensemble_size, nx, ny, nz)
    print(f"\nEnKF [ens={ensemble_size}, grid={nx}x{ny}x{nz}] 耗时: {elapsed:.3f}s")


@pytest.mark.benchmark
def test_enkf_inflation_effect(small_grid):
    from bayesian_assimilation.models.enkf import EnKF

    g = small_grid
    nx, ny, nz = g["shape"]

    for inflation in [1.0, 1.05, 1.1, 1.2]:
        enkf = EnKF(
            ensemble_size=30,
            inflation_factor=inflation,
            localization_radius=5000,
        )
        ensemble = np.random.rand(30, nx, ny, nz)

        start = time.perf_counter()
        analysis = enkf.update(
            ensemble=ensemble,
            observations=g["observations"],
            obs_locations=g["obs_locations"],
        )
        elapsed = time.perf_counter() - start

        spread = np.std(analysis, axis=0).mean()
        print(f"  inflation={inflation:.2f}: 耗时={elapsed:.3f}s, spread={spread:.6f}")


@pytest.mark.benchmark
@pytest.mark.parametrize("localization_radius", [1000, 5000, 10000])
def test_enkf_localization_scaling(localization_radius, small_grid):
    from bayesian_assimilation.models.enkf import EnKF

    enkf = EnKF(
        ensemble_size=30,
        inflation_factor=1.05,
        localization_radius=localization_radius,
    )

    g = small_grid
    nx, ny, nz = g["shape"]
    ensemble = np.random.rand(30, nx, ny, nz)

    start = time.perf_counter()
    analysis = enkf.update(
        ensemble=ensemble,
        observations=g["observations"],
        obs_locations=g["obs_locations"],
    )
    elapsed = time.perf_counter() - start

    assert analysis.shape == (30, nx, ny, nz)
    print(f"\nEnKF [loc_rad={localization_radius}] 耗时: {elapsed:.3f}s")
