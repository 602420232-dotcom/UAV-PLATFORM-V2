# 贝叶斯数据同化核心算法库

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-beta-yellow)

> 📖 本模块是无人机路径规划系统的核心算法库。如需了解整体系统架构，请查看[项目主文档](../../README.md)。

## 功能特性

### 核心算法

- **3D-VAR**: 三维变分同化算法
- **4D-VAR**: 四维变分同化算法
- **EnKF**: 集合卡尔曼滤波
- **混合同化**: 多种算法自适应组合

### 数据处理

- 多源数据适配（卫星、雷达、地面站）
- 网格插值与数据重采样
- 质量控制与数据验证
- 时间序列分析与异常检测

### 并行计算

- 区域分解并行
- Dask 分布式计算
- MPI 多机并行
- Ray 分布式计算

### 可视化

- 同化结果可视化
- 风险热力图
- 不确定性分析
- 动画演示

## 安装

```bash
# 基础安装
pip install -e .

# 安装所有依赖（包括API、并行计算、GPU支持）
pip install -e .[api,parallel,gpu]
```

## 快速开始

### 基础使用

```python
from bayesian_assimilation.core.assimilator import BayesianAssimilator
import numpy as np

# 初始化同化器
assimilator = BayesianAssimilator()
assimilator.initialize_grid(domain_size=(100, 100, 50))

# 准备数据
background = np.random.rand(100, 100, 50)
observations = np.random.rand(1000)
obs_locations = np.random.rand(1000, 3)

# 执行同化
analysis, variance = assimilator.assimilate_3dvar(
    background, observations, obs_locations
)
```

### CLI 使用

```bash
# 查看帮助
assimilate --help

# 执行同化任务
assimilate run --config configs/default.yaml

# 质量控制
assimilate quality-control --input data/observations.nc

# 风险评估
assimilate risk-assessment --input data/analysis.nc
```

### REST API

```bash
# 启动API服务
python -m uvicorn bayesian_assimilation.api.rest:app --host 0.0.0.0 --port 8000

# 执行同化
curl -X POST http://localhost:8000/assimilate \
  -H "Content-Type: application/json" \
  -d '{"background": [...], "observations": [...]}'
```

## 配置

详见 [configs/](../configs/) 目录下的配置文件。

### 默认配置示例

```yaml
# configs/default.yaml
assimilation:
  method: 3dvar
  domain_size: [100, 100, 50]
  resolution: 1000.0

errors:
  background_error_scale: 1.5
  observation_error_scale: 0.8

parallel:
  enabled: true
  num_workers: 4
  backend: dask
```

## Docker 部署

详见 [docker/README.md](docker/README.md)

```bash
# 构建镜像
cd docker
docker build -t bayesian_assimilation:latest ..

# 启动服务
docker-compose up -d
```

## 项目结构

```
algorithm_core/
├── src/
│   └── bayesian_assimilation/   # 主包
│       ├── core/               # 核心同化算法
│       ├── models/             # 同化模型
│       ├── parallel/           # 并行计算框架
│       ├── api/                # API接口
│       ├── adapters/           # 数据适配器
│       ├── visualization/      # 可视化模块
│       ├── quality_control/    # 质量控制
│       ├── risk_assessment/    # 风险评估
│       └── workflows/          # 工作流管理
├── configs/                    # 配置文件
├── docker/                     # Docker部署
├── examples/                   # 示例代码
└── benchmarks/                # 性能测试
```

## 开发

### 环境设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装开发依赖
pip install -e .[dev]

# 安装pre-commit钩子
pre-commit install
```

### 运行测试

```bash
pytest
pytest tests/test_assimilator.py
pytest --cov=bayesian_assimilation --cov-report=html
```

## API 参考

### 核心类

| 类 | 说明 |
|---|---|
| `BayesianAssimilator` | 主同化器类 |
| `ThreeDimensionalVar` | 3D-VAR 实现 |
| `FourDimensionalVar` | 4D-VAR 实现 |
| `EnKF` | 集合卡尔曼滤波 |
| `HybridAssimilator` | 混合同化器 |

### 并行管理器

| 类型 | 说明 |
|------|------|
| `BlockParallelManager` | 区域分解并行 |
| `DaskParallelManager` | Dask 分布式 |
| `MPIParallelManager` | MPI 多机并行 |
| `RayParallelManager` | Ray 分布式 |

## 许可证

MIT License - 详见项目根目录 [LICENSE](../../LICENSE) 文件
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
