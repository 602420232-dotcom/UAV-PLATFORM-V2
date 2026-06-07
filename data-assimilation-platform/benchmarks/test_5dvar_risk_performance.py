"""
5D-VAR 风险感知算法性能基准测试

测试 5D-VAR（带风险维度）在不同时间窗口和网格规模下的性能表现，
重点关注风险维度对整体性能的影响。
"""
import time
import pytest
import numpy as np
import sys
import os

# 添加路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ASSIMILATION_PATH = os.path.join(PROJECT_ROOT, 'algorithm_core', 'src')
if DATA_ASSIMILATION_PATH not in sys.path:
    sys.path.insert(0, DATA_ASSIMILATION_PATH)


@pytest.mark.benchmark
@pytest.mark.parametrize("grid_size,time_steps,obs_per_step", [
    ((30, 30), 5, 100),
    ((50, 50), 10, 200),
    ((100, 100), 20, 500),
])
def test_4dvar_performance(grid_size, time_steps, obs_per_step):
    """测试标准4D-VAR性能（基准对比）"""
    from bayesian_assimilation.models.four_dimensional_var import FourDimensionalVar

    model = FourDimensionalVar()

    nx, ny = grid_size

    # 准备背景场
    background = {
        'grid': {'shape': grid_size},
        'variables': {
            'temperature': np.random.rand(nx, ny) * 10 + 20,
            'u_wind': np.random.rand(nx, ny) * 5,
            'v_wind': np.random.rand(nx, ny) * 5,
            'pressure': np.random.rand(nx, ny) * 100 + 1000
        }
    }

    # 准备观测
    observations = []
    for t in range(time_steps):
        for _ in range(obs_per_step):
            lat_idx = np.random.randint(0, nx)
            lon_idx = np.random.randint(0, ny)
            observations.append({
                'time_idx': t,
                'lat_idx': lat_idx,
                'lon_idx': lon_idx,
                'variable': 'temperature',
                'value': 25.0 + np.random.randn() * 2.0
            })

    start = time.perf_counter()
    analysis, _ = model.assimilate(background, observations)
    elapsed = time.perf_counter() - start

    assert analysis['variables']['temperature'].shape == (nx, ny)
    print(f"\n4D-VAR [{nx}x{ny}, T={time_steps}, obs={len(observations)}] 耗时: {elapsed:.3f}s")


@pytest.mark.benchmark
@pytest.mark.parametrize("grid_size,time_steps,obs_per_step", [
    ((30, 30), 5, 100),
    ((50, 50), 10, 200),
    ((100, 100), 20, 500),
])
def test_5dvar_risk_mapping_performance(grid_size, time_steps, obs_per_step):
    """测试5D-VAR风险映射性能"""
    from bayesian_assimilation.utils.risk_mapper import (
        WeatherToRiskMapper,
    )

    nx, ny = grid_size

    # 生成同化结果
    analysis = {
        'grid': {'shape': grid_size},
        'variables': {
            'u_wind': np.random.rand(nx, ny) * 10 + 5,
            'v_wind': np.random.rand(nx, ny) * 10 + 5
        }
    }

    # 初始化风险映射器
    risk_mapper = WeatherToRiskMapper(grid_resolution=100.0)

    start = time.perf_counter()

    # 计算风险
    risk_result = risk_mapper.compute_comprehensive_risk(analysis, heading=0.0)

    # 生成风险障碍物
    risk_obstacles = risk_mapper.generate_risk_aware_obstacles(
        risk_result,
        risk_threshold=0.6
    )

    elapsed = time.perf_counter() - start

    assert 'risk_grid' in risk_result
    assert 'summary' in risk_result

    print(f"\n5D-VAR 风险映射 [{nx}x{ny}, T={time_steps}, obs={obs_per_step}] 耗时: {elapsed:.3f}s")
    print(f"  平均风险: {risk_result['summary']['avg_risk']:.3f}")
    print(f"  安全区域占比: {risk_result['summary']['safe_area_ratio']:.1%}")
    print(f"  风险障碍物数量: {len(risk_obstacles)}")


@pytest.mark.benchmark
@pytest.mark.parametrize("grid_size", [(30, 30), (50, 50), (100, 100)])
def test_risk_aware_planning_performance(grid_size):
    """测试风险感知路径规划性能"""
    from bayesian_assimilation.utils.risk_mapper import (
        WeatherToRiskMapper,
    )

    # 添加路径规划模块路径
    sys.path.insert(0, os.path.join(PROJECT_ROOT, '..', 'path-planning-service', 'src', 'main', 'python'))
    from risk_aware_planner import RiskAwareAStarPlanner  # type: ignore[reportMissingImports]

    nx, ny = grid_size

    # 生成风险场
    analysis = {
        'grid': {'shape': grid_size},
        'variables': {
            'u_wind': np.random.rand(nx, ny) * 10,
            'v_wind': np.random.rand(nx, ny) * 10
        }
    }

    risk_mapper = WeatherToRiskMapper()
    risk_result = risk_mapper.compute_comprehensive_risk(analysis)

    # 测试规划
    planner = RiskAwareAStarPlanner(
        risk_result=risk_result,
        risk_weight=0.4
    )

    start_pos = (0.0, 0.0)
    goal_pos = (float(nx-1), float(ny-1))

    start = time.perf_counter()
    result = planner.plan(start_pos, goal_pos, grid_resolution=1.0)
    elapsed = time.perf_counter() - start

    print(f"\n风险感知路径规划 [{nx}x{ny}] 耗时: {elapsed:.3f}s")
    if result['success']:
        print(f"  路径点数量: {len(result['path'])}")
        print(f"  平均路径风险: {result.get('avg_risk', 0):.3f}")
    else:
        print(f"  规划失败: {result['error']}")


@pytest.mark.benchmark
def test_end_to_end_pipeline():
    """测试端到端5D-VAR+规划流程"""
    from bayesian_assimilation.utils.risk_mapper import WeatherToRiskMapper

    grid_size = (50, 50)

    print(f"\n===== 端到端测试 [{grid_size[0]}x{grid_size[1]}] =====")

    # 阶段1: 数据准备
    start_phase1 = time.perf_counter()
    analysis = {
        'grid': {'shape': grid_size},
        'variables': {
            'u_wind': np.random.rand(*grid_size) * 10 + 5,
            'v_wind': np.random.rand(*grid_size) * 10 + 5
        }
    }
    time_phase1 = time.perf_counter() - start_phase1

    # 阶段2: 风险映射
    start_phase2 = time.perf_counter()
    risk_mapper = WeatherToRiskMapper()
    risk_result = risk_mapper.compute_comprehensive_risk(analysis)
    time_phase2 = time.perf_counter() - start_phase2

    # 阶段3: 风险障碍物生成
    start_phase3 = time.perf_counter()
    risk_obstacles = risk_mapper.generate_risk_aware_obstacles(risk_result, risk_threshold=0.6)
    time_phase3 = time.perf_counter() - start_phase3

    total_time = time_phase1 + time_phase2 + time_phase3

    print("\n阶段统计:")
    print(f"  数据准备: {time_phase1:.3f}s")
    print(f"  风险映射: {time_phase2:.3f}s")
    print(f"  障碍物生成: {time_phase3:.3f}s")
    print(f"  总时间: {total_time:.3f}s")
    print("\n风险统计:")
    print(f"  平均风险: {risk_result['summary']['avg_risk']:.3f}")
    print(f"  高风险占比: {risk_result['summary']['high_risk_ratio']:.1%}")
    print(f"  风险障碍物: {len(risk_obstacles)}")

    assert total_time < 1.0, f"端到端延迟过高: {total_time:.3f}s"


@pytest.mark.benchmark
@pytest.mark.parametrize("use_fp16", [False, True])
def test_performance_comparison(use_fp16):
    """对比FP32 vs FP16性能"""
    from bayesian_assimilation.utils.risk_mapper import WeatherToRiskMapper

    grid_size = (100, 100)
    nx, ny = grid_size

    analysis = {
        'grid': {'shape': grid_size},
        'variables': {
            'u_wind': np.random.rand(nx, ny) * 10,
            'v_wind': np.random.rand(nx, ny) * 10
        }
    }

    risk_mapper = WeatherToRiskMapper()

    # 测量多次求平均
    times = []
    for _ in range(5):
        start = time.perf_counter()
        _ = risk_mapper.compute_comprehensive_risk(analysis)
        times.append(time.perf_counter() - start)

    avg_time = np.mean(times)
    precision = "FP16" if use_fp16 else "FP32"
    print(f"\n{precision} [100x100] 平均耗时: {avg_time:.3f}s")
