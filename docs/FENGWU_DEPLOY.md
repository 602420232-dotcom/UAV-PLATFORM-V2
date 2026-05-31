# FengWu AI 气象预测模型部署指南

> **文档版本**: v1.0  
> **最后更新**: 2026-05-31  
> **适用服务**: fengwu-service (端口 8085)  
> **模型**: FengWu-v2 ONNX 全球天气预报模型

---

## 目录

1. [概述](#1-概述)
2. [模型下载](#2-模型下载)
3. [Docker 部署](#3-docker-部署)
4. [模型配置](#4-模型配置)
5. [安全认证](#5-安全认证)
6. [性能优化](#6-性能优化)
7. [故障排除](#7-故障排除)
8. [API 接口](#8-api-接口)

---

## 1. 概述

### 1.1 FengWu 模型简介

FengWu 是基于 ONNX Runtime 的深度学习气象预测模型，能够提供全球天气预报：

| 特性 | 说明 |
|------|------|
| **预测范围** | 全球 (721×1440 格点) |
| **预测时长** | 最长 14 天 (56 个预测步) |
| **时间分辨率** | 6 小时间隔 |
| **气象变量** | 69 个 (13 个气压层 + 4 个地表变量) |
| **模型大小** | ~200MB (ONNX 格式) |

### 1.2 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    FengWu Service                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   FastAPI   │───▶│  ONNX RT   │───▶│  Numpy      │    │
│  │  (端口8085) │    │  Engine    │    │  Output     │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         ▲                                           │       │
│         │              ┌─────────────┐             │       │
│         └──────────────│  fengwu_v2  │◀────────────┘       │
│                        │  .onnx     │                        │
│                        └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 预测变量

**地表变量 (4个)**:
| 变量名 | 描述 | 单位 |
|--------|------|------|
| u10 | 10米风速 U分量 | m/s |
| v10 | 10米风速 V分量 | m/s |
| t2m | 2米温度 | K |
| msl | 平均海平面气压 | Pa |

**气压层变量 (65个)**:
- 位势高度 (z)
- 比湿 (q)
- 温度 (t)
- U/V 风分量

---

## 2. 模型下载

### 2.1 自动下载脚本

使用项目提供的脚本下载模型：

```bash
# 使用默认路径
cd scripts
./download_fengwu_model.sh

# 指定自定义路径
./download_fengwu_model.sh --output /path/to/models
```

### 2.2 手动下载

从 Hugging Face 下载模型：

```bash
# 安装依赖
pip install huggingface_hub

# 下载模型
python -c "
from huggingface_hub import hf_hub_download
path = hf_hub_download(
    repo_id='your-org/fengwu-v2',
    filename='fengwu_v2.onnx',
    local_dir='./fengwu-service/models'
)
print(f'Model saved to: {path}')
"
```

### 2.3 模型文件结构

```
fengwu-service/
├── models/
│   └── fengwu_v2.onnx    # ONNX 模型文件 (~200MB)
├── app.py                # FastAPI 应用
├── inference_engine.py    # ONNX 推理引擎
├── Dockerfile
└── README.md
```

---

## 3. Docker 部署

### 3.1 基础部署

```bash
# 构建镜像
docker build -t uav-fengwu-service:latest -f fengwu-service/Dockerfile .

# 运行容器 (需要挂载模型)
docker run -d \
  --name fengwu-service \
  -p 8085:8085 \
  -v /path/to/models:/app/model:ro \
  -e ENVIRONMENT=production \
  -e FENGWU_API_KEY=your-secure-api-key \
  -e CORS_ORIGINS=localhost:3000,your-domain.com \
  --restart unless-stopped \
  uav-fengwu-service:latest
```

### 3.2 Docker Compose 部署

**fengwu-service 部分配置**:

```yaml
fengwu-service:
  image: uav-fengwu-service:latest
  container_name: uav-fengwu-service
  ports:
    - "8085:8085"
  volumes:
    - ./models:/app/model:ro   # 挂载模型目录 (只读)
  environment:
    - ENVIRONMENT=${ENVIRONMENT:-production}
    - FENGWU_API_KEY=${FENGWU_API_KEY}
    - CORS_ORIGINS=${CORS_ORIGINS:-localhost:3000}
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8085/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 60s
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 8G
      reservations:
        cpus: '2'
        memory: 4G
  restart: unless-stopped
```

### 3.3 GPU 加速部署

使用 NVIDIA GPU 加速推理：

```dockerfile
# Dockerfile.gpu
FROM nvidia/cuda:11.8-runtime-ubuntu22.04

# 安装 ONNX Runtime GPU 版本
RUN pip install onnxruntime-gpu

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8085"]
```

```bash
# 运行 GPU 版本
docker run -d \
  --gpus all \
  --name fengwu-service-gpu \
  -p 8085:8085 \
  -v /path/to/models:/app/model:ro \
  uav-fengwu-service:gpu
```

---

## 4. 模型配置

### 4.1 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MODEL_PATH` | `/app/model/fengwu_v2.onnx` | 模型文件路径 |
| `MODEL_NAME` | `fengwu_v2.onnx` | 模型文件名 |
| `ENVIRONMENT` | `development` | 运行环境 |
| `FENGWU_API_KEY` | (空) | API 认证密钥 |
| `CORS_ORIGINS` | `localhost:3000,localhost:8080` | CORS 允许来源 |

### 4.2 模型预热

首次加载模型可能需要 30-60 秒，配置预热以提高响应速度：

```yaml
fengwu-service:
  environment:
    - WARMUP_ENABLED=true
    - WARMUP_STEPS=4
```

### 4.3 模型版本管理

建议使用版本化的模型路径：

```
models/
├── v1.0/
│   └── fengwu_v2.onnx
├── v1.1/
│   └── fengwu_v2.onnx
└── latest -> v1.1/
```

切换模型版本：

```bash
# 通过符号链接切换
ln -sfn /app/model/v1.1 /app/model/latest

# 或通过环境变量
docker exec fengwu-service mv /app/model/fengwu_v2.onnx /app/model/fengwu_v2.onnx.bak
docker exec fengwu-service ln -s /app/model/v1.1/fengwu_v2.onnx /app/model/fengwu_v2.onnx

# 重启服务加载新模型
docker restart fengwu-service
```

---

## 5. 安全认证

### 5.1 API Key 认证

生产环境必须配置 API Key：

```bash
# 生成安全 API Key
openssl rand -hex 32

# 配置到环境变量
export FENGWU_API_KEY="your-generated-key"
```

**请求示例**:

```bash
curl -X POST http://localhost:8085/api/v1/forecast \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-generated-key" \
  -d '{
    "input_0h": [[...]],  // 69×721×1440 数组
    "input_6h": [[...]],  // 69×721×1440 数组
    "steps": 14,
    "surface_only": true
  }'
```

### 5.2 CORS 配置

```bash
# 仅允许指定域名
export CORS_ORIGINS="your-frontend.com,your-admin.com"
```

### 5.3 网络隔离 (Kubernetes)

使用 NetworkPolicy 限制访问：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fengwu-network-policy
spec:
  podSelector:
    matchLabels:
      app: fengwu-service
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: uav-platform
      ports:
        - protocol: TCP
          port: 8085
```

---

## 6. 性能优化

### 6.1 并发配置

```yaml
fengwu-service:
  environment:
    - MAX_CONCURRENT_REQUESTS=4
    - REQUEST_TIMEOUT=300
```

### 6.2 缓存策略

对于相同输入的请求，启用结果缓存：

```yaml
fengwu-service:
  environment:
    - CACHE_ENABLED=true
    - CACHE_TTL=3600
```

### 6.3 资源限制

根据模型大小和并发需求配置资源：

| 并发数 | CPU | 内存 | GPU |
|--------|-----|------|-----|
| 1 | 2核 | 4GB | 可选 |
| 4 | 4核 | 8GB | 推荐 |
| 8 | 8核 | 16GB | 推荐 |

---

## 7. 故障排除

### 7.1 模型加载失败

**症状**: 服务启动后 `/health` 返回 `DEGRADED`

**排查步骤**:

1. 检查模型文件是否存在
   ```bash
   docker exec uav-fengwu-service ls -la /app/model/
   ```

2. 检查模型文件完整性
   ```bash
   # 文件大小应该 ~200MB
   docker exec uav-fengwu-service stat /app/model/fengwu_v2.onnx
   ```

3. 检查 ONNX 模型有效性
   ```python
   import onnxruntime as ort
   
   session = ort.InferenceSession("/path/to/model/fengwu_v2.onnx")
   print(f"Model inputs: {[i.name for i in session.get_inputs()]}")
   print(f"Model outputs: {[o.name for o in session.get_outputs()]}")
   ```

### 7.2 内存不足

**症状**: 推理时 OOM 或进程被 kill

**解决方案**:

```bash
# 增加内存限制
docker update --memory 16G --memory-swap 16G uav-fengwu-service

# 或减少并发数
docker exec uav-fengwu-service env MAX_CONCURRENT_REQUESTS=2
```

### 7.3 推理超时

**症状**: 请求返回 504 Gateway Timeout

**解决方案**:

```yaml
# 增加超时时间
fengwu-service:
  environment:
    - REQUEST_TIMEOUT=600
```

### 7.4 GPU 不可用

**症状**: 日志显示 "GPU not available, using CPU"

**解决方案**:

1. 检查 NVIDIA 驱动
   ```bash
   nvidia-smi
   ```

2. 检查 Docker GPU 支持
   ```bash
   docker run --gpus all nvidia/cuda:11.8-runtime-ubuntu22.04 nvidia-smi
   ```

3. 安装 nvidia-container-toolkit
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
     sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

---

## 8. API 接口

### 8.1 健康检查

**GET** `/health`

```json
{
  "status": "UP",
  "model_loaded": true,
  "model_path": "/app/model/fengwu_v2.onnx",
  "uptime_seconds": 3600.5
}
```

### 8.2 天气预报

**POST** `/api/v1/forecast`

**请求体**:

```json
{
  "input_0h": [[[float]]],  // 69×721×1440 ERA5 数据
  "input_6h": [[[float]]],  // 6小时后的ERA5数据
  "steps": 14,              // 预测步数 (1-56)
  "surface_only": true      // 仅返回地表变量
}
```

**响应**:

```json
{
  "status": "success",
  "model": "fengwu_v2.onnx",
  "steps": 14,
  "lead_time_hours": 84,
  "computation_time_s": 12.5,
  "forecasts": [
    {
      "step": 0,
      "lead_hours": 6,
      "u10": [[float]],  // 721×1440
      "v10": [[float]],
      "t2m": [[float]],
      "msl": [[float]]
    }
  ]
}
```

### 8.3 风场预测

**POST** `/api/v1/forecast/wind`

快速获取风场统计信息：

```json
{
  "status": "success",
  "model": "fengwu_v2.onnx",
  "wind": [
    {
      "step": 0,
      "lead_hours": 6,
      "wind_speed_avg": 5.2,
      "wind_speed_max": 15.8,
      "wind_speed_min": 0.1
    }
  ]
}
```

### 8.4 模型信息

**GET** `/api/v1/model/info`

```json
{
  "model": "fengwu_v2.onnx",
  "variables": 69,
  "grid": "721×1440",
  "levels": 13,
  "max_forecast_steps": 56,
  "max_lead_time": "14 days",
  "step_interval": "6 hours",
  "provider": "CUDAExecutionProvider"
}
```

---

## 附录 A: 输入数据格式

ERA5 再分析数据的标准格式：

```
shape: (69, 721, 1440)

维度说明:
- 69: 气象变量数量
- 721: 纬度格点数 (从 -90° 到 90°)
- 1440: 经度格点数 (从 0° 到 360°)

变量顺序:
[0:4]   地表: u10, v10, t2m, msl
[4:9]   50 hPa: z, q, u, v, t
[9:14]  100 hPa: z, q, u, v, t
[14:19] 200 hPa: z, q, u, v, t
...      继续各气压层
```

## 附录 B: 相关资源

- [FengWu 模型论文](https://arxiv.org/)
- [ONNX Runtime 文档](https://onnxruntime.ai/docs/)
- [ERA5 数据下载](https://cds.climate.copernicus.eu/)

---

> **维护者**: UAV Platform Team  
> **文档版本**: 1.0  
> **创建日期**: 2026-05-31
