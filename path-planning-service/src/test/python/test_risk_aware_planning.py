#!/usr/bin/env python3
"""
气象风险感知路径规划集成测试

测试完整的风险映射 → 路径规划流程
"""
import os
import sys

import numpy as np


# 添加路径

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PYTHON_DIR = os.path.join(TEST_DIR, '..', '..', 'main', 'python')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(TEST_DIR))))

# 添加data-assimilation-platform的路径
DATA_ASSIMILATION_PATH = os.path.join(
    PROJECT_ROOT, 'data-assimilation-platform', 'algorithm_core', 'src'
)
if DATA_ASSIMILATION_PATH not in sys.path:
    sys.path.insert(0, DATA_ASSIMILATION_PATH)

# 导入风险映射模块
try:
    from bayesian_assimilation.utils.risk_mapper import (  # noqa: E402
        WeatherToRiskMapper,  # type: ignore[assignment]
        RiskAwarePathCostCalculator,  # type: ignore[assignment]
        RiskLevel  # type: ignore[assignment]
    )
    print("✓ 风险映射模块加载成功")
except ImportError as e:
    print(f"✗ 风险映射模块加载失败: {e}")
    print("使用简化版本...")
    class RiskLevel:
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        EXTREME = "EXTREME"

    class WeatherToRiskMapper:
        def __init__(self, grid_resolution=100.0, constraints=None):
            self.grid_resolution = grid_resolution
        def compute_comprehensive_risk(self, assimilation_result, heading=0.0):
            shape = assimilation_result.get('grid', {}).get('shape', (10, 10))
            return {
                'risk_grid': np.zeros(shape),
                'risk_level': np.full(shape, RiskLevel.LOW, dtype=object),
                'summary': {'avg_risk': 0.0, 'max_risk': 0.0, 'min_risk': 0.0, 'safe_area_ratio': 1.0, 'high_risk_ratio': 0.0}
            }
        def generate_risk_aware_obstacles(self, risk_result, risk_threshold=0.6):
            return []

    class RiskAwarePathCostCalculator:
        def __init__(self, mapper):
            self.mapper = mapper
        def set_risk_field(self, risk_result):
            pass
        def get_risk_at_position(self, position):
            return 0.0
        def compute_segment_risk_cost(self, start, end, steps=10):
            return 0.0
        def is_high_risk_zone(self, position, threshold=0.6):
            return False

# 添加路径规划模块路径
if MAIN_PYTHON_DIR not in sys.path:
    sys.path.insert(0, MAIN_PYTHON_DIR)

from three_layer_planner import ThreeLayerPlanner, Drone, Task  # type: ignore[import-not-found]  # noqa: E402
print("✓ 路径规划模块加载成功")

import logging  # noqa: E402
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_assimilation_result():
    """创建测试用同化结果"""
    np.random.seed(42)
    shape = (30, 30)  # 30x30 栅格

    # 创建模拟风场
    x = np.linspace(0, 2 * np.pi, shape[0])
    y = np.linspace(0, 2 * np.pi, shape[1])
    X, Y = np.meshgrid(x, y)

    # 基础风场 + 随机扰动
    u_wind = 8 + 4 * np.sin(X * 0.5) + np.random.normal(0, 1.5, shape)
    v_wind = 5 + 3 * np.cos(Y * 0.5) + np.random.normal(0, 1.5, shape)

    # 创建高风速区域（模拟城市峡谷效应）
    # 右侧边缘为高风险区
    u_wind[:, 20:] += 8
    # 左下角为中等风险区
    u_wind[:15, :15] += 3

    return {
        'variables': {
            'u_wind': u_wind,
            'v_wind': v_wind
        },
        'grid': {'shape': shape}
    }


def create_test_scenario():
    """创建测试场景"""
    # 创建无人机
    drones = [
        Drone('drone_1', max_payload=5.0, max_endurance=60.0, max_speed=15.0),
        Drone('drone_2', max_payload=3.0, max_endurance=45.0, max_speed=12.0)
    ]

    # 创建任务点
    tasks = [
        Task('task_1', location=(50.0, 80.0), demand=1.0, start_time=0.0, end_time=30.0),
        Task('task_2', location=(120.0, 150.0), demand=0.5, start_time=5.0, end_time=35.0),
        Task('task_3', location=(200.0, 100.0), demand=0.8, start_time=10.0, end_time=40.0),
        Task('task_4', location=(80.0, 220.0), demand=1.2, start_time=15.0, end_time=50.0)
    ]

    # 基础气象数据
    weather_data = {
        'wind_speed': 10.0,
        'wind_direction': 'NE'
    }

    return drones, tasks, weather_data


def test_risk_mapping():
    """测试1：风险映射功能"""
    print("\n" + "=" * 60)
    print("测试1: 气象风险映射")
    print("=" * 60)

    # 创建风险映射器
    mapper = WeatherToRiskMapper(grid_resolution=10.0)

    # 创建测试同化结果
    assimilation_result = create_test_assimilation_result()

    # 计算风险
    risk_result = mapper.compute_comprehensive_risk(assimilation_result, heading=0.0)

    # 打印统计信息
    summary = risk_result['summary']
    print("\n风险统计:")
    print(f"  - 平均风险: {summary['avg_risk']:.3f}")
    print(f"  - 最大风险: {summary['max_risk']:.3f}")
    print(f"  - 最小风险: {summary['min_risk']:.3f}")
    print(f"  - 安全区域占比: {summary['safe_area_ratio']:.1%}")
    print(f"  - 高风险区域占比: {summary['high_risk_ratio']:.1%}")

    # 风险等级分布
    risk_grid = risk_result['risk_grid']
    print("\n风险等级分布:")
    print(f"  - 低风险 (0-0.3): {np.sum(risk_grid < 0.3) / risk_grid.size:.1%}")
    print(f"  - 中风险 (0.3-0.6): {np.sum((risk_grid >= 0.3) & (risk_grid < 0.6)) / risk_grid.size:.1%}")
    print(f"  - 高风险 (0.6-0.85): {np.sum((risk_grid >= 0.6) & (risk_grid < 0.85)) / risk_grid.size:.1%}")
    print(f"  - 极高风险 (>0.85): {np.sum(risk_grid >= 0.85) / risk_grid.size:.1%}")

    # 生成风险障碍物
    obstacles = mapper.generate_risk_aware_obstacles(risk_result, risk_threshold=0.6)
    print(f"\n生成的风险障碍物数量: {len(obstacles)}")

    return risk_result


def test_risk_aware_planning():
    """测试2：风险感知路径规划"""
    print("\n" + "=" * 60)
    print("测试2: 风险感知路径规划")
    print("=" * 60)

    # 创建同化结果
    assimilation_result = create_test_assimilation_result()

    # 创建测试场景
    drones, tasks, weather_data = create_test_scenario()

    # 创建三层规划器（带风险感知）
    planner = ThreeLayerPlanner(
        drones=drones,
        tasks=tasks,
        weather_data=weather_data,
        assimilation_result=assimilation_result,
        risk_weight=0.4  # 40%风险权重
    )

    # 检查风险映射是否初始化
    if planner.risk_result:
        print("\n风险映射已初始化:")
        print(f"  - 平均风险: {planner.risk_result['summary']['avg_risk']:.3f}")
        print(f"  - 安全区域: {planner.risk_result['summary']['safe_area_ratio']:.1%}")
    else:
        print("\n警告: 风险映射未初始化")

    # 执行规划
    print("\n执行风险感知路径规划...")
    result = planner.plan()

    if result['success']:
        print("\n规划成功!")
        print(f"生成路由数: {len(result['routes'])}")

        # 打印每个路由的详细信息
        for i, route in enumerate(result['routes']):
            print(f"\n路由 {i+1} (无人机: {route['drone_id']}):")
            print(f"  - 任务数: {len(route['tasks'])}")
            print(f"  - 总距离: {route['total_distance']:.1f}")
            print(f"  - 总时间: {route['total_time']:.1f}")
            if 'path' in route:
                print(f"  - 路径点数: {len(route['path'])}")
            if 'path_risk' in route:
                print(f"  - 平均路径风险: {route['path_risk']:.3f}")
            if 'comprehensive_cost' in route:
                print(f"  - 综合代价: {route['comprehensive_cost']:.2f}")

        # 打印风险摘要
        if 'risk_summary' in result:
            print("\n全局风险摘要:")
            summary = result['risk_summary']
            print(f"  - 平均风险: {summary['avg_risk']:.3f}")
            print(f"  - 最大风险: {summary['max_risk']:.3f}")
            print(f"  - 安全区域: {summary['safe_area_ratio']:.1%}")
            print(f"  - 使用风险权重: {result['risk_weight_used']:.1%}")

    else:
        print(f"\n规划失败: {result.get('error', '未知错误')}")

    return result


def test_comparison():
    """测试3：对比有/无风险感知的规划结果"""
    print("\n" + "=" * 60)
    print("测试3: 风险感知 vs 普通规划对比")
    print("=" * 60)

    assimilation_result = create_test_assimilation_result()
    drones, tasks, weather_data = create_test_scenario()

    # 1. 普通规划（无风险感知）
    print("\n1. 普通规划（无风险感知）...")
    planner_normal = ThreeLayerPlanner(
        drones=drones[:1],  # 只用一个无人机
        tasks=tasks[:2],
        weather_data=weather_data
    )
    result_normal = planner_normal.plan()

    # 2. 风险感知规划
    print("2. 风险感知规划...")
    planner_risk = ThreeLayerPlanner(
        drones=drones[:1],
        tasks=tasks[:2],
        weather_data=weather_data,
        assimilation_result=assimilation_result,
        risk_weight=0.5  # 50%风险权重
    )
    result_risk = planner_risk.plan()

    # 对比结果
    if result_normal['success'] and result_risk['success']:
        route_normal = result_normal['routes'][0]
        route_risk = result_risk['routes'][0]

        print("\n对比结果:")
        print(f"{'指标':<20} {'普通规划':<15} {'风险感知规划':<15}")
        print("-" * 50)
        print(f"{'总距离':<20} {route_normal['total_distance']:<15.1f} {route_risk['total_distance']:<15.1f}")
        print(f"{'总时间':<20} {route_normal['total_time']:<15.1f} {route_risk['total_time']:<15.1f}")

        if 'comprehensive_cost' in route_normal and 'comprehensive_cost' in route_risk:
            print(f"{'综合代价':<20} {route_normal['comprehensive_cost']:<15.2f} {route_risk['comprehensive_cost']:<15.2f}")

        if 'path_risk' in route_risk:
            print(f"{'平均路径风险':<20} {'N/A':<15} {route_risk['path_risk']:<15.3f}")

        # 计算路径差异
        if 'path' in route_normal and 'path' in route_risk:
            path_normal_len = len(route_normal['path'])
            path_risk_len = len(route_risk['path'])
            print(f"{'路径长度':<20} {path_normal_len:<15} {path_risk_len:<15}")

            # 风险感知规划可能会选择更长的路径来规避风险
            if path_risk_len > path_normal_len:
                print(f"\n分析: 风险感知规划选择了更长的路径 ({path_risk_len - path_normal_len} 个额外点)")
                print("      这是为了规避高风险区域，提高飞行安全性")
    else:
        print("规划失败，无法对比")


def main():
    """主测试函数"""
    print("\n" + "#" * 60)
    print("# 气象风险感知路径规划 - 集成测试")
    print("#" * 60)

    try:
        # 测试1: 风险映射
        test_risk_mapping()

        # 测试2: 风险感知路径规划
        test_risk_aware_planning()

        # 测试3: 对比测试
        test_comparison()

        print("\n" + "#" * 60)
        print("# 所有测试完成!")
        print("#" * 60)

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback  # noqa: E402
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
