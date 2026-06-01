# Data Assimilation Deployments

## 📋 概述

数据同化平台的部署配置文件，包含 Docker、Kubernetes 等多种部署方式。

**最后更新**: 2026-05-08

---

## 📁 目录结构

```
deployments/
├── docker/               # Docker 配置
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── nginx.conf
├── kubernetes/           # Kubernetes 配置
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── secrets.yaml
├── helm/                 # Helm Charts
├── terraform/            # Terraform 配置
├── init.sql             # 数据库初始化
└── README.md           # 本文档
```

---

## 🐳 Docker 部署

### 开发环境

```bash
# 构建镜像
docker build -f docker/Dockerfile.dev -t uav-assimilation:dev .

# 运行容器
docker run -p 8084:8084 uav-assimilation:dev
```

### 生产环境

```bash
# 构建生产镜像
docker build -f docker/Dockerfile -t uav-assimilation:latest .

# 运行
docker-compose up -d
```

---

## ☸️ Kubernetes 部署

### 部署服务

```bash
# 应用配置
kubectl apply -f kubernetes/

# 查看 pods
kubectl get pods -l app=assimilation

# 查看日志
kubectl logs -l app=assimilation
```

### 配置说明

| 文件 | 用途 |
|------|------|
| deployment.yaml | 部署配置 |
| service.yaml | 服务暴露 |
| configmap.yaml | 配置项 |
| secrets.yaml | 密钥 |

---

## 📦 Helm Chart

```bash
# 安装
helm install assimilation ./helm

# 升级
helm upgrade assimilation ./helm

# 卸载
helm uninstall assimilation
```

---

## 🔧 环境变量

### 必需变量

| 变量 | 说明 |
|------|------|
| `DB_PASSWORD` | 数据库密码 |
| `JWT_SECRET` | JWT 密钥 |
| `REDIS_PASSWORD` | Redis 密码 |

### 可选变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_HOST` | localhost | 数据库地址 |
| `REDIS_HOST` | localhost | Redis 地址 |

---

## 🛡️ 安全配置

### 生产环境建议

1. 使用 Kubernetes Secrets 管理密钥
2. 启用 TLS/SSL
3. 配置 Network Policies
4. 使用 RBAC 权限控制

---

## 📚 相关文档

- [Docker 部署指南](../../docs/DOCKER.md)
- [Kubernetes 部署指南](../../docs/KUBERNETES.md)
- [运维手册](../../docs/OPS_MANUAL.md)

---

**最后更新**: 2026-05-08
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
