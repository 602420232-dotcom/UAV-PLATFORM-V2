# 🚀 无人机路径规划系统 - 快速启动指南

**面向团队成员的快速部署说明**

---

## 📋 前置要求

- **Docker & Docker Compose** 
  - Mac/Linux: `docker -v && docker-compose -v`
  - Windows: 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Git** 版本控制
- **网络连接**：能访问 Docker Hub

> ✅ 无需本地安装 Java、Python、Node.js 等环境

---

## ⚡ 5 分钟快速启动

### 步骤 1：克隆项目

```bash
git clone https://github.com/602420232-dotcom/weather
cd trae
```

### 步骤 2：配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件（修改必要的敏感参数）
# Windows: notepad .env
# Mac/Linux: nano .env

# 必须修改的参数（最少要改这三个）：
# DB_PASSWORD=your_strong_password_here
# SECURITY_USER_PASSWORD=your_admin_password_here
# JWT_SECRET=your_jwt_secret_here
```

### 步骤 3：启动所有服务

```bash
# 拉取最新镜像
docker-compose pull

# 启动所有服务（首次运行需要 3-5 分钟）
docker-compose up -d

# 等待所有服务就绪
docker-compose logs -f

# 按 Ctrl+C 退出日志查看
```

### 步骤 4：验证部署

```bash
# 查看所有服务状态
docker-compose ps

# 访问以下地址验证
# ✅ 前端应用：http://localhost:3000
# ✅ API 网关：http://localhost:8088/actuator/health
# ✅ Nacos 控制台：http://localhost:8848/nacos (nacos/nacos)
```

---

## 📡 服务状态检查

### 快速健康检查

```bash
# 检查所有服务是否就绪
curl http://localhost:8088/actuator/health

# 预期响应：
# {"status":"UP","components":{"..."},...}
```

### 查看具体服务状态

```bash
# 查看所有容器
docker-compose ps

# 预期输出（所有服务应该是 Up 或 healthy）：
# NAME                  STATUS              PORTS
# uav-gateway           Up 2 minutes (health: starting)
# uav-fengwu            Up 2 minutes (healthy)
# uav-frontend          Up 2 minutes (health: starting)
# mysql                 Up 3 minutes (healthy)
# redis                 Up 3 minutes (healthy)
# nacos                 Up 3 minutes (healthy)
# ...
```

---

## 🛠️ 常用命令

### 启动 / 停止 / 重启

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务（但保留数据）
docker-compose stop

# 启动已停止的服务
docker-compose start

# 重启特定服务
docker-compose restart uav-gateway

# 停止并删除所有容器和网络（删除数据！）
docker-compose down

# 停止并完全清理（包括数据卷）
docker-compose down -v
```

### 查看日志

```bash
# 查看所有服务的最新日志
docker-compose logs -f --tail=50

# 查看特定服务日志
docker-compose logs -f uav-gateway

# 仅显示最后 20 行
docker-compose logs --tail=20 uav-fengwu

# 查看带时间戳的日志
docker-compose logs -f -t
```

### 进入容器调试

```bash
# 进入容器 shell
docker-compose exec uav-gateway sh

# 运行一次性命令
docker-compose exec mysql mysql -uroot -p$DB_ROOT_PASSWORD -e "SELECT VERSION();"

# 查看容器文件系统
docker-compose exec uav-platform ls -la /app
```

### 清理和维护

```bash
# 删除已停止的容器
docker container prune -f

# 删除未使用的镜像
docker image prune -f

# 删除未使用的卷
docker volume prune -f

# 查看磁盘使用情况
docker system df

# 完整清理（谨慎使用！）
docker system prune -a --volumes -f
```

---

## 🔍 故障排除

### 问题 1：服务启动失败

**症状**：`docker-compose ps` 显示 Exited

**解决方案**：

```bash
# 查看错误日志
docker-compose logs <service-name>

# 常见原因：
# - 数据库密码错误 → 检查 .env 中的 DB_PASSWORD
# - 端口被占用 → 改 docker-compose.yml 中的端口或停止占用进程
# - 磁盘空间不足 → 清理旧镜像和容器
```

### 问题 2：无法连接前端

**症状**：访问 http://localhost:3000 无响应

**解决方案**：

```bash
# 检查前端服务状态
docker-compose ps uav-frontend

# 查看前端日志
docker-compose logs uav-frontend

# 检查端口是否在监听
# Mac/Linux: lsof -i :3000
# Windows: netstat -ano | findstr :3000

# 重启前端服务
docker-compose restart uav-frontend
```

### 问题 3：数据库连接失败

**症状**：后端服务无法启动，日志显示 "Can't connect to MySQL"

**解决方案**：

```bash
# 检查 MySQL 是否就绪
docker-compose logs mysql

# 进入 MySQL 容器验证
docker-compose exec mysql mysql -uroot -p$DB_ROOT_PASSWORD -e "SELECT 1;"

# 检查 .env 中数据库配置
# DB_HOST 应该是 mysql（不是 localhost）
# DB_PORT 应该是 3306
# DB_PASSWORD 应该与 DB_ROOT_PASSWORD 一致
```

### 问题 4：内存或资源不足

**症状**：容器频繁重启，日志显示 OOM 或崩溃

**解决方案**：

```bash
# 增加 Docker 内存分配
# Mac/Linux: Docker Desktop 设置 → Resources → Memory (改为 8GB+)
# Windows: Docker Desktop 设置 → Resources → Memory (改为 8GB+)

# 或删除旧容器和镜像释放空间
docker system prune -a -f --volumes
```

---

## 🌐 访问服务

### 主要应用

| 服务 | 地址 | 用户名 | 密码 | 说明 |
|------|------|--------|------|------|
| **前端应用** | http://localhost:3000 | - | - | Vue3 web 应用 |
| **API 网关** | http://localhost:8088 | - | - | REST API 入口 |
| **Nacos** | http://localhost:8848/nacos | nacos | nacos | 服务发现 & 配置 |
| **MySQL** | localhost:3306 | uav | (DB_PASSWORD) | 数据库 |
| **Redis** | localhost:6379 | - | - | 缓存 |

### API 健康检查端点

```bash
# API 网关健康检查
curl http://localhost:8088/actuator/health

# WRF 处理器
curl http://localhost:8081/actuator/health

# 路径规划服务
curl http://localhost:8083/actuator/health

# FengWu 服务
curl http://localhost:8085/health
```

---

## 📚 获取帮助

### 查看完整文档

- [完整 README](README.md) - 项目总体说明
- [部署指南](docs/DEPLOYMENT.md) - 详细部署步骤
- [API 文档](docs/api/API_DOCUMENTATION.md) - API 接口说明
- [故障排除](docs/guides/TROUBLESHOOTING.md) - 常见问题解答

### 获取支持

- 📧 **邮件**：向团队主管反馈
- 🐛 **Bug 反馈**：在 GitHub Issues 中提交
- 💬 **讨论**：在团队 Slack/钉钉 中沟通

---

## ✅ 验证清单

启动后，请按照以下清单验证：

- [ ] 所有容器都在运行 (`docker-compose ps` 显示 Up)
- [ ] 前端可访问 (http://localhost:3000 能打开)
- [ ] API 网关健康 (curl http://localhost:8088/actuator/health 返回 UP)
- [ ] Nacos 控制台可访问 (http://localhost:8848/nacos)
- [ ] 数据库连接正常 (后端日志无连接错误)
- [ ] 前端可以加载 API 数据 (无 CORS 错误)

---

## 🚪 退出和清理

### 临时停止

```bash
# 停止所有服务，保留数据
docker-compose stop

# 稍后恢复
docker-compose start
```

### 完全退出

```bash
# 停止并删除所有容器和网络（数据卷保留）
docker-compose down

# 删除所有数据
docker-compose down -v
```

---

## 💡 Tips

1. **首次启动缓慢**：第一次运行会下载镜像和初始化数据库，可能需要 5-10 分钟
2. **开发修改**：修改后端代码需要重新构建镜像 (`docker-compose build --no-cache`)
3. **查看实时日志**：建议开一个新终端窗口运行 `docker-compose logs -f`
4. **重置数据**：如果需要清空数据库，执行 `docker-compose down -v` 再 `up -d`
5. **性能优化**：如果运行缓慢，检查 Docker 内存分配是否足够 (8GB 以上推荐)

---

## 📞 更新镜像

如果发现镜像有更新，按以下步骤更新：

```bash
# 拉取最新镜像
docker-compose pull

# 停止现有容器
docker-compose down

# 用新镜像启动
docker-compose up -d

# 验证
docker-compose ps
```

---

**需要帮助？查看 [完整文档](README.md) 或联系团队主管！** 🎯
