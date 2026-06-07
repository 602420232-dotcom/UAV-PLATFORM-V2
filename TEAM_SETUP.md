# 🚀 团队快速启动指南

## 📦 所有镜像已上传到 Docker Hub！

**Docker Hub 账户**: `dithiothreitollf`

### 可用的镜像列表

| # | 服务 | Docker Hub 链接 | 大小 | 说明 |
|---|------|----------------|------|------|
| 1 | **API Gateway** | https://hub.docker.com/r/dithiothreitollf/api-gateway | 716MB | REST API 入口 |
| 2 | **WRF Processor** | https://hub.docker.com/r/dithiothreitollf/wrf-processor | 848MB | 气象数据处理 |
| 3 | **Data Assimilation** | https://hub.docker.com/r/dithiothreitollf/data-assimilation | 846MB | 贝叶斯同化 |
| 4 | **Meteor Forecast** | https://hub.docker.com/r/dithiothreitollf/meteor-forecast | 846MB | 气象预测 |
| 5 | **Path Planning** | https://hub.docker.com/r/dithiothreitollf/path-planning | 846MB | 路径规划 |
| 6 | **UAV Platform** | https://hub.docker.com/r/dithiothreitollf/uav-platform | 846MB | 主平台服务 |
| 7 | **Weather Collector** | https://hub.docker.com/r/dithiothreitollf/weather-collector | 760MB | 气象数据采集 |
| 8 | **Edge Cloud** | https://hub.docker.com/r/dithiothreitollf/edge-cloud | 619MB | 边云协同 |
| 9 | **FengWu Service** | https://hub.docker.com/r/dithiothreitollf/fengwu | 541MB | 风乌气象模型 |
| 10 | **Model Engine** | https://hub.docker.com/r/dithiothreitollf/model-engine | 9.49GB | AI 模型引擎 |
| 11 | **Frontend** | https://hub.docker.com/r/dithiothreitollf/frontend | 36.8MB | Vue3 前端 |

---

## ⚡ 快速启动（3 步）

### 第 1 步：克隆项目

```bash
git clone https://github.com/602420232-dotcom/weather
cd trae
```

### 第 2 步：配置环境变量

```bash
cp .env.example .env

# 编辑 .env，修改以下三个必须的参数：
# DB_PASSWORD=your_strong_password_here
# SECURITY_USER_PASSWORD=your_admin_password_here
# JWT_SECRET=your_jwt_secret_here
```

### 第 3 步：拉取镜像并启动

```bash
# 拉取所有镜像
docker-compose pull

# 启动所有服务
docker-compose up -d

# 验证（等待 30-60 秒）
docker-compose ps
```

### 访问服务

- 🌐 **前端应用**：http://localhost:3000
- 🔧 **API 网关**：http://localhost:8088/actuator/health
- ⚙️ **Nacos 控制台**：http://localhost:8848/nacos (nacos/nacos)

---

## 📚 详细文档

- 📖 [5 分钟快速启动](QUICKSTART.md) - 详细步骤和故障排除
- 📋 [完整 README](README.md) - 项目总体说明
- 🐳 [Docker Hub 镜像](https://hub.docker.com/u/dithiothreitollf) - 所有镜像

---

## ❓ 常见问题

**Q: 能否不使用 Docker Hub，用本地构建？**
A: 可以，使用原始的 `docker-compose.yml` 会自动本地构建。但使用 Docker Hub 镜像更快。

**Q: 镜像需要付费吗？**
A: 不需要，都是免费的公开镜像。

**Q: 我没有 Docker 怎么办？**
A: 下载安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)（包含 Docker 和 Docker Compose）。

**Q: 启动很慢？**
A: 第一次启动会下载镜像（可能 10-30 分钟），后续启动会很快。

**Q: 端口被占用了怎么办？**
A: 编辑 `.env` 文件，修改端口号（如 3000 改为 3001）。

---

## 🔗 相关链接

- **GitHub 仓库**：https://github.com/602420232-dotcom/weather
- **Docker Hub 账户**：https://hub.docker.com/u/dithiothreitollf
- **项目主页**：http://localhost:3000

---

## 💬 需要帮助？

- 查看 [QUICKSTART.md](QUICKSTART.md) 中的"故障排除"部分
- 查看 [README.md](README.md) 获取完整文档
- 联系项目主管

---

**准备好了吗？开始使用吧！🚀**

```bash
git clone https://github.com/602420232-dotcom/weather && cd trae
cp .env.example .env
# 编辑 .env
docker-compose pull && docker-compose up -d
```
