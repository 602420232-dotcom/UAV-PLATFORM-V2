#!/usr/bin/env python3
"""
高级路径规划算法 — 兼容层

本文件保留向后兼容性，所有功能已模块化到 planners/ 子包。
新代码请直接使用 planners 模块。

模块结构:
- planners/base.py       : BasePlanner 基类及共享工具
- planners/rrt_star.py   : RRT* 规划器 (RRTP / RRTStarPlanner)
- planners/dijkstra.py   : Dijkstra 规划器
- planners/genetic.py    : 遗传算法规划器
- planners/pso.py        : 粒子群优化规划器
- planners/factory.py    : 规划器工厂 (PlannerFactory)
"""

import json
import sys
import logging

from planners import (RRTP, RRTStarPlanner, DijkstraPlanner,
                      GeneticAlgorithmPlanner, ParticleSwarmOptimizationPlanner,
                      PlannerFactory, BasePlanner)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_input(file_index):
    """从文件加载JSON输入数据，防止命令注入"""
    if len(sys.argv) <= file_index:
        return {}
    file_path = sys.argv[file_index]
    with open(file_path, 'r') as f:
        return json.load(f)


def _parse_obstacles(input_data):
    """解析障碍物数据"""
    return BasePlanner._make_obstacles(
        input_data.get('obstacles', []))


def main():
    """主函数 — 根据命令行参数选择规划器"""
    if len(sys.argv) < 2:
        logger.debug(json.dumps({'success': False, 'error': '缺少命令参数'}))
        return

    command = sys.argv[1]

    # 定义支持的命令与对应规划器类型
    commands = {
        'rrt_star': ('rrt_star', RRTP),
        'dijkstra': ('dijkstra', DijkstraPlanner),
        'genetic': ('genetic', GeneticAlgorithmPlanner),
        'pso': ('pso', ParticleSwarmOptimizationPlanner),
    }

    if command not in commands:
        logger.debug(json.dumps({'success': False, 'error': '未知命令'}))
        return

    if len(sys.argv) < 3:
        logger.debug(json.dumps({'success': False, 'error': '缺少输入数据'}))
        return

    try:
        input_data = load_input(2)
        start = tuple(input_data.get('start', (0, 0)))
        goal = tuple(input_data.get('goal', (10, 10)))
        obstacles = _parse_obstacles(input_data)

        planner_type, _ = commands[command]
        planner = PlannerFactory.create(
            planner_type, start=start, goal=goal, obstacles=obstacles)

        if command == 'dijkstra':
            result = planner.plan(start, goal)
        else:
            result = planner.plan()

        logger.debug(json.dumps(result))

    except Exception as e:
        logger.debug(json.dumps({'success': False, 'error': str(e)}))


if __name__ == "__main__":
    main()
