# Algorithm Core - 核心算法库

## 📋 概述

无人机路径规划系统的核心算法库，包含 VRP、路径优化、气象数据处理等算法实现。

**技术栈**:
- Python 3.8+
- NumPy, SciPy
- TensorFlow
- NetworkX

**最后更新**: 2026-05-08

---

## 📁 项目结构

```
algorithm-core/
├── src/
│   ├── vrp/              # 车辆路径问题算法
│   │   ├── solver.py     # VRP求解器
│   │   ├── models.py     # 数据模型
│   │   └── constraints.py # 约束处理
│   │
│   ├── planning/         # 路径规划算法
│   │   ├── rrt_star.py  # RRT*算法
│   │   ├── dwa.py       # DWA算法
│   │   └── hybrid.py    # 混合算法
│   │
│   ├── weather/          # 气象数据处理
│   │   ├── wps.py       # WPS预处理
│   │   └── interpolation.py # 插值算法
│   │
│   └── utils/           # 工具函数
│       ├── math.py
│       └── visualization.py
│
├── tests/               # 单元测试
├── benchmarks/          # 性能测试
├── requirements.txt     # Python依赖
├── setup.py            # 安装配置
└── README.md          # 本文档
```

---

## 🚀 快速开始

### 安装

```bash
# 克隆并安装
cd algorithm-core
pip install -e .[dev]

# 或仅安装依赖
pip install -r requirements.txt
```

### 基本使用

```python
from algorithm_core.vrp import VRPSolver
from algorithm_core.planning import PathPlanner

# 创建VRP求解器
solver = VRPSolver()
result = solver.solve(
    locations=[[0, 0], [1, 1], [2, 2]],
    capacity=100
)
print(result.routes)

# 创建路径规划器
planner = PathPlanner()
path = planner.plan(start=[0, 0], goal=[10, 10])
print(path.trajectory)
```

---

## 📊 核心算法

### 1. VRP (车辆路径问题)

| 算法 | 说明 | 时间复杂度 |
|------|------|-----------|
| **CVRP** | 容量约束VRP | O(n²) |
| **VRPTW** | 时间窗约束VRP | O(n³) |
| **MDVRP** | 多仓库VRP | O(n²) |
| **PVRP** | 周期VRP | O(n³) |

### 2. 路径规划

| 算法 | 说明 | 适用场景 |
|------|------|---------|
| **RRT*** | 快速随机树 | 复杂环境 |
| **DWA** | 动态窗口法 | 实时避障 |
| **A\*** | A星算法 | 网格地图 |
| **DE-RRT\*** | 差分进化RRT\* | 全局最优 |

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/vrp/test_solver.py -v

# 性能测试
python benchmarks/run.py --algorithm VRP
```

---

## 📈 性能基准

| 算法 | 平均耗时 | 最差耗时 |
|------|----------|----------|
| CVRP | 0.5s | 2.1s |
| VRPTW | 1.2s | 5.3s |
| RRT\* | 0.3s | 1.5s |
| DWA | 0.05s | 0.2s |

---

## 📚 相关文档

- [Algorithm Core API](../docs/algorithm/)
- [性能测试报告](../docs/benchmarks/)

---

**最后更新**: 2026-05-08
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
