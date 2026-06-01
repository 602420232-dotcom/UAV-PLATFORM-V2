# 项目目录结构详解

本文档提供项目各目录的详细说明。

## 根目录结构

```
trae/                           # 项目根目录
├── .gitignore                  # Git 忽略规则
├── .pre-commit-config.yaml     # pre-commit 配置
├── pyproject.toml              # 项目级别工具配置
├── README.md                   # 主文档（项目引导）
├── DEPLOYMENT.md               # 部署与运维手册
├── EXAMPLE.md                  # 使用示例
│
├── data-assimilation-platform/ # 贝叶斯同化服务
├── wrf-processor-service/      # WRF 气象处理服务
├── meteor-forecast-service/    # 气象预测服务
├── path-planning-service/      # 路径规划服务
├── uav-platform-service/       # 主平台服务
├── uav-edge-sdk/              # 端侧 SDK
├── frontend-vue/               # 前端应用
└── deployments/               # Kubernetes 部署配置
```

## data-assimilation-platform/

```
data-assimilation-platform/
├── pyproject.toml              # 项目级别工具配置
└── algorithm_core/            # 【核心】Python 算法库
```

### algorithm_core/ 目录结构

```
algorithm_core/                 # 核心算法库（可独立 pip 安装）
├── README.md                  # 算法库文档
├── setup.py                  # pip 安装脚本
├── pyproject.toml            # 包配置
├── .env.example              # 环境变量模板
│
├── benchmarks/               # 性能测试
│   └── results/
│       └── report.md        # 测试报告
│
├── configs/                  # 配置文件
│   ├── default.yaml         # 默认配置
│   ├── development.yaml     # 开发环境
│   └── production.yaml     # 生产环境
│
├── docker/                  # Docker 配置
│   ├── Dockerfile          # CPU 版本
│   ├── nvidia.Dockerfile # GPU 版本
│   ├── docker-compose.yml  # 编排配置
│   ├── entrypoint.sh      # 启动脚本
│   └── README.md          # Docker 部署指南
│
├── docs/                   # 文档
│   └── CHANGELOG.md      # 变更日志
│
├── examples/               # 示例代码
│   ├── basic_usage.py     # 基础用法
│   ├── advanced_usage.py  # 高级用法
│   ├── gpu_acceleration.py # GPU 加速
│   ├── parallel_demo.py   # 并行计算
│   ├── jupyter/          # Jupyter 教程
│   └── output/          # 示例输出
│
└── src/
    └── bayesian_assimilation/  # 主包
        ├── __init__.py
        ├── __version__.py
        │
        ├── accelerators/    # 硬件加速
        ├── adapters/       # 数据适配
        ├── api/           # API 接口
        ├── components/    # 组件
        ├── core/         # 核心算法
        ├── models/        # 同化模型
        ├── parallel/      # 并行计算
        ├── quality_control/ # 质量控制
        ├── risk_assessment/ # 风险评估
        ├── time_series/  # 时间序列
        ├── utils/        # 工具
        ├── visualization/ # 可视化
        ├── workflows/    # 工作流
        └── data_sources/ # 数据源
```

### 核心源码模块说明

| 模块 | 说明 |
|------|------|
| `accelerators/` | GPU/CPU/TPU 硬件加速 |
| `adapters/` | WRF/观测/网格数据适配 |
| `api/` | CLI/REST/Web 接口 |
| `core/` | 核心同化算法基类 |
| `models/` | 3D-VAR/4D-VAR/EnKF 实现 |
| `parallel/` | Dask/MPI/Ray 并行计算 |
| `quality_control/` | 数据质量验证 |
| `risk_assessment/` | 风险评估 |
| `visualization/` | 结果可视化 |
| `workflows/` | 工作流管理 |

## wrf-processor-service/

WRF 气象数据处理服务（Java Spring Boot）

## meteor-forecast-service/

气象预测与订正服务（Java Spring Boot）

## path-planning-service/

路径规划服务（Java Spring Boot）

## uav-platform-service/

主平台服务（Java Spring Boot）

## uav-edge-sdk/

端侧 SDK（C++/Python 混合）

## frontend-vue/

Vue3 前端应用

## deployments/

Kubernetes 部署配置

---

> 📌 **提示**: 详细的 API 说明和部署步骤请参考 [DEPLOYMENT.md](DEPLOYMENT.md) 和 [EXAMPLE.md](EXAMPLE.md)。
