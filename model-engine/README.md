# AI 模型引擎

## 概述

AI 模型引擎（model-engine）包含多种 AI 模型和算法，包括 CNN、XGBoost、UNet、GPR、EnKF、多无人机协同、MPC 控制、主动观测等。该服务提供 REST API 接口，支持模型训练、推理、评估等功能，为整个无人机路径规划系统提供 AI 能力支持。

## 技术栈

| 技术 | 版本 | 用途 |
|------|:----:|------|
| Python | 3.10+ | 运行环境 |
| FastAPI | 0.100+ | Web 框架 |
| Uvicorn | 0.22+ | ASGI 服务器 |
| PyTorch | 2.0+ | 深度学习框架 |
| PyTorch Lightning | 2.0+ | 训练框架 |
| NumPy | 1.24+ | 数值计算 |
| Pandas | 2.0+ | 数据处理 |
| Scikit-learn | 1.3+ | 机器学习库 |
| GPyTorch | 1.9+ | 高斯过程库 |
| XGBoost | 1.7+ | 梯度提升库 |

## 项目结构

```
model-engine/
├── api/                          # API 层
│   ├── __init__.py
│   ├── main.py                   # FastAPI 应用入口
│   └── routes/                   # API 路由
│       ├── __init__.py
│       └── risk_routes.py        # 风险评估路由
├── cnn_corrector/                # CNN 校正模块
│   ├── __init__.py
│   ├── model.py
│   └── xgboost_corrector.py
├── unet_downscaler/              # UNet 降尺度模块
│   ├── __init__.py
│   ├── model.py
│   └── probabilistic.py
├── gpr_risk/                     # GPR 风险评估模块
│   ├── __init__.py
│   ├── model.py
│   └── enkf.py                   # EnKF 数据同化
├── control/                      # 控制模块
│   ├── __init__.py
│   └── mpc.py                    # MPC 模型预测控制
├── multi_uav/                    # 多无人机协同模块
│   ├── __init__.py
│   └── conflict_resolver.py      # 冲突解决
├── path_planning/                # 路径规划模块
│   ├── __init__.py
│   ├── planner.py
│   ├── cost_function.py
│   └── mavlink_output.py
├── active_obs/                   # 主动观测模块
│   ├── __init__.py
│   └── bayesian_observer.py
├── data_pipeline/                # 数据管道模块
│   ├── __init__.py
│   ├── config.py
│   ├── dataset.py
│   ├── fetcher.py
│   ├── outlier_detector.py
│   ├── registration.py
│   └── training_data.py
├── fusion/                       # 数据融合模块
│   ├── __init__.py
│   └── ensemble.py
├── integration/                  # 集成模块
│   ├── __init__.py
│   ├── adapter.py
│   └── bridge.py
├── checkpoints/                  # 模型检查点
│   └── README.md
├── tests/                        # 测试
│   ├── __init__.py
│   ├── test_cnn.py
│   ├── test_unet.py
│   ├── test_gpr.py
│   ├── test_enkf.py
│   ├── test_path_planning.py
│   └── ...
├── scripts/                      # 脚本
│   ├── train_all.py
│   ├── train_cnn.py
│   ├── train_unet.py
│   ├── train_xgboost.py
│   ├── auto_train.sh
│   └── install_deps.sh
├── PIPELINE.md                   # 数据管道文档
├── PIPELINE_VERIFICATION.md      # 管道验证文档
├── Dockerfile                    # Docker 配置
├── requirements.txt              # Python 依赖
├── pyproject.toml                # 项目配置
└── README.md                     # 本文件
```

## 服务端口

| 端口 | 协议 | 说明 |
|:----:|------|------|
| 8092 | HTTP | REST API 服务端口 |

## API 端点

### 健康检查

```
GET /health
GET /health/ready
```

### 模型信息

```
GET /api/models
获取所有可用模型列表
```

```
GET /api/models/{model_name}
获取指定模型的详细信息
```

### CNN 气象校正

```
POST /api/cnn/correct
使用 CNN 模型进行气象数据校正
```

**请求体:**
```json
{
  "input_data": [[...]],
  "model_version": "v1.0",
  "return_probabilistic": false
}
```

### UNet 降尺度

```
POST /api/unet/downscale
使用 UNet 模型进行气象数据降尺度
```

**请求体:**
```json
{
  "input_data": [[...]],
  "target_resolution": "1KM",
  "model_version": "v1.0"
}
```

### GPR 风险评估

```
POST /api/gpr/risk
使用 GPR 模型进行风险评估
```

**请求体:**
```json
{
  "location": {
    "lat": 30.0,
    "lon": 110.0,
    "height": 500
  },
  "weather_data": {...},
  "time": "2026-06-05T12:00:00Z"
}
```

### EnKF 数据同化

```
POST /api/enkf/assimilate
使用 EnKF 进行数据同化
```

**请求体:**
```json
{
  "forecast": [[...]],
  "observations": [...],
  "observation_locations": [...],
  "ensemble_size": 50
}
```

### 多无人机协同

```
POST /api/multi-uav/plan
多无人机协同路径规划
```

**请求体:**
```json
{
  "drones": [
    {"id": "uav-001", "position": {...}, "capabilities": [...]}
  ],
  "tasks": [...],
  "area": {...}
}
```

### MPC 控制

```
POST /api/mpc/control
模型预测控制
```

**请求体:**
```json
{
  "current_state": {...},
  "target_state": {...},
  "constraints": {...},
  "horizon": 10
}
```

### 主动观测

```
POST /api/active-obs/suggest
主动观测点建议
```

**请求体:**
```json
{
  "current_observations": [...],
  "area": {...},
  "uncertainty_threshold": 0.5,
  "budget": 5
}
```

## Docker 部署

### 构建镜像

```bash
docker build -t uav/model-engine:latest -f Dockerfile .
```

### 运行容器

```bash
docker run -d \
  --name model-engine \
  -p 8092:8092 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -e CUDA_VISIBLE_DEVICES=0 \
  uav/model-engine:latest
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SERVER_PORT` | `8092` | 服务端口 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `WORKERS` | `4` | Worker 数量 |
| `MODEL_PATH` | `/app/checkpoints` | 模型检查点路径 |
| `CUDA_VISIBLE_DEVICES` | - | GPU 设备（可选） |

## 开发指南

### 安装依赖

```bash
pip install -r requirements.txt
```

或使用脚本：

```bash
./scripts/install_deps.sh
```

### 启动开发服务器

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8092 --reload
```

### 模型训练

```bash
# 训练所有模型
python scripts/train_all.py

# 单独训练 CNN
python scripts/train_cnn.py

# 单独训练 UNet
python scripts/train_unet.py

# 单独训练 XGBoost
python scripts/train_xgboost.py
```

### 运行测试

```bash
pytest tests/
```

### API 文档

启动后访问:
- Swagger UI: http://localhost:8092/docs
- ReDoc: http://localhost:8092/redoc

## 相关文档

- [根项目 README](../README.md)
- [端口配置总表](../docs/PORTS_CONFIGURATION.md)
- [项目架构文档](../docs/architecture.md)
- [数据管道文档](./PIPELINE.md)
- [管道验证文档](./PIPELINE_VERIFICATION.md)

---

> **最后更新**: 2026-06-05
> **版本**: 1.0
> **维护者**: UAV Platform Team
