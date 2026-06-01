# 贝叶斯同化系统 Docker 部署指南

## 目录结构

```
docker/
├── Dockerfile          # Docker 镜像构建文件
├── docker-compose.yml  # Docker Compose 编排文件
├── entrypoint.sh      # 容器启动脚本
└── README.md          # 本文件
```

## 快速开始

### 1. 构建 Docker 镜像

```bash
cd docker
docker build -t bayesian_assimilation:latest ..
```

### 2. 使用 Docker Compose 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d api      # 仅 REST API
docker-compose up -d web     # 仅 Web 界面
```

### 3. 直接使用 Docker 运行

```bash
# 运行 REST API
docker run -p 8000:8000 bayesian_assimilation:latest api

# 运行 Web 界面
docker run -p 5000:5000 bayesian_assimilation:latest web

# 运行 CLI 命令
docker run bayesian_assimilation:latest cli --help

# 进入容器 bash
docker run -it bayesian_assimilation:latest bash
```

## 服务访问

| 服务 | 地址 | 说明 |
|------|------|------|
| REST API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| Web 界面 | http://localhost:5000 | Flask Web 应用 |

## 数据挂载

可以将宿主机的目录挂载到容器中：

```bash
docker run -p 8000:8000 \
  -v /path/to/data:/app/data \
  -v /path/to/output:/app/output \
  bayesian_assimilation:latest api
```

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| PYTHONUNBUFFERED | 1 | 实时输出日志 |
| LOG_LEVEL | INFO | 日志级别 |

## Docker Compose 命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f api
docker-compose logs -f web

# 停止服务
docker-compose down

# 重新构建
docker-compose up -d --build

# 查看服务状态
docker-compose ps
```

## API 使用示例

### 执行同化
```bash
curl -X POST http://localhost:8000/assimilate \
  -H "Content-Type: application/json" \
  -d '{"background": {"wind_speed": [[...]]}, "observations": {"values": [...], "locations": [...]}}'
```

### 质量控制
```bash
curl -X POST http://localhost:8000/quality-control \
  -H "Content-Type: application/json" \
  -d '{"data": {"wind_speed": [[...]]}, "data_type": "wind_speed"}'
```

### 风险评估
```bash
curl -X POST http://localhost:8000/risk-assessment \
  -H "Content-Type: application/json" \
  -d '{"wind_speed": [[...]]}'
```

## 注意事项

1. 确保 Docker 已安装并运行
2. 容器默认以 root 用户运行
3. 数据卷权限需要根据实际情况调整
4. 生产环境建议使用反向代理（如 Nginx）
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
