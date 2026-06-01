# Data Assimilation Platform - 数据同化平台

## 📋 项目概述

数据同化平台是 UAV Path Planning System 的核心组件，负责整合贝叶斯数据同化核心算法库，通过 REST API 提供数据同化计算服务。

**核心功能**: 融合多源气象观测数据，支持 3D-VAR、4D-VAR、EnKF 等先进算法

**技术栈**:
- Spring Boot 3.2.0 (Java 17)
- Python 3.8+ (算法引擎)
- Maven (构建工具)
- MySQL 8.0+ (数据存储)
- Redis 6.2+ (缓存)

---

## 📁 项目结构

```
data-assimilation-platform/
├── algorithm_core/          # 贝叶斯同化核心算法库 (Python)
│   ├── src/
│   │   ├── bayesian_assimilation/  # 核心算法
│   │   ├── data/                 # 数据处理
│   │   ├── models/               # 模型定义
│   │   └── utils/                # 工具函数
│   ├── tests/                   # 单元测试
│   ├── benchmarks/             # 性能基准测试
│   ├── requirements.txt        # Python 依赖
│   └── setup.py                # 安装配置
│
├── service_spring/            # Spring Boot 服务 (Java)
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/          # Java 源代码
│   │   │   └── resources/     # 配置文件
│   │   └── test/              # 测试代码
│   ├── pom.xml                # Maven 配置
│   └── application.yml        # 应用配置
│
├── service_python/           # Python 微服务
│   ├── api/                  # API 接口
│   ├── models/               # 数据模型
│   └── utils/                # 工具函数
│
├── shared/                   # 共享资源
│   ├── proto/                # Protocol Buffers 定义
│   ├── config/               # 共享配置
│   └── README.md             # 共享资源说明
│
├── deployments/              # 部署配置
│   ├── kubernetes/           # K8s 部署
│   ├── docker/               # Docker 配置
│   └── docker-compose.yml    # Docker Compose
│
├── docs/                     # 文档
│
├── benchmarks/              # 性能测试
│
├── scripts/                  # 自动化脚本
│
├── Makefile                 # Make 构建
├── pyproject.toml           # Python 项目配置
├── requirements.txt         # Python 依赖
└── README.md                # 本文档
```

---

## 🚀 快速开始

### 环境要求

- **Java**: 17+
- **Python**: 3.8+
- **Maven**: 3.8+
- **MySQL**: 8.0+
- **Redis**: 6.2+

### 1. 安装 Python 依赖

```bash
cd data-assimilation-platform

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装算法库（开发模式）
cd algorithm_core
pip install -e .[dev]
```

### 2. 配置数据库

```bash
# 启动 MySQL 和 Redis
docker-compose up -d mysql redis

# 创建数据库
mysql -h localhost -u root -p < deployments/init.sql
```

### 3. 启动服务

#### Spring Boot 服务

```bash
cd service_spring

# 构建
mvn clean package -DskipTests

# 运行
mvn spring-boot:run

# 或运行 JAR
java -jar target/service_spring-1.0.0.jar
```

#### Python 算法服务

```bash
cd service_python

# 运行
python -m api.main
```

### 4. 访问服务

服务启动后，访问: **http://localhost:8084**

---

## 🔧 服务配置

### Spring Boot 配置

**文件**: `service_spring/src/main/resources/application.yml`

```yaml
server:
  port: 8084

spring:
  application:
    name: data-assimilation-service
  
  datasource:
    url: jdbc:mysql://localhost:3306/uav_data_assimilation
    username: root
    password: ${DB_PASSWORD}
  
  redis:
    host: localhost
    port: 6379

# 算法配置
assimilation:
  python-script: src/main/python/bayesian_assimilation.py
  timeout: 300000  # 5分钟
  
  algorithms:
    - 3D-VAR
    - 4D-VAR
    - EnKF
```

### Python 环境变量

```bash
# .env 文件
ALGORITHM_HOST=localhost
ALGORITHM_PORT=5000
LOG_LEVEL=INFO
```

---

## 📊 核心算法

### 支持的算法

| 算法 | 说明 | 应用场景 |
|------|------|---------|
| **3D-VAR** | 三维变分同化 | 常规气象分析 |
| **4D-VAR** | 四维变分同化 | 时空连续分析 |
| **EnKF** | 集合卡尔曼滤波 | 不确定性量化 |

### 算法配置

**3D-VAR 配置**:
```yaml
assimilation:
  algorithm: 3D-VAR
  background-error-covariance: B_matrix.npy
  observation-error-variance: R_matrix.npy
  max-iterations: 100
  convergence-threshold: 1e-6
```

**4D-VAR 配置**:
```yaml
assimilation:
  algorithm: 4D-VAR
  time-window: 6h
  adjoint-model: true
  control-variables: [u, v, t, q]
```

---

## 🔌 API 接口

### 主要接口

#### 1. 执行贝叶斯同化

**端点**: `POST /api/assimilation/execute`

**请求示例**:
```bash
curl -X POST http://localhost:8084/api/assimilation/execute \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "3D-VAR",
    "observations": [...],
    "background": {...},
    "config": {
      "max-iterations": 100,
      "tolerance": 1e-6
    }
  }'
```

**响应示例**:
```json
{
  "success": true,
  "analysis": {
    "mean": [...],
    "variance": [...]
  },
  "metadata": {
    "algorithm": "3D-VAR",
    "iterations": 45,
    "computation-time": "2.3s"
  }
}
```

#### 2. 计算方差场

**端点**: `POST /api/assimilation/variance`

**请求示例**:
```bash
curl -X POST http://localhost:8084/api/assimilation/variance \
  -H "Content-Type: application/json" \
  -d '{
    "data": [...],
    "method": "ensemble"
  }'
```

#### 3. 批量执行同化

**端点**: `POST /api/assimilation/batch`

**请求示例**:
```bash
curl -X POST http://localhost:8084/api/assimilation/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"id": 1, "algorithm": "3D-VAR", "data": {...}},
      {"id": 2, "algorithm": "EnKF", "data": {...}}
    ],
    "parallel": true
  }'
```

#### 4. 健康检查

**端点**: `GET /actuator/health`

---

## 🧪 测试

### 运行测试

```bash
# 所有测试
mvn test

# 单元测试
mvn test -Dtest=*Test

# 集成测试
mvn verify

# Python 算法测试
cd algorithm_core
pytest tests/ -v

# 性能测试
cd benchmarks
python run_benchmarks.py
```

### 测试覆盖

| 模块 | 覆盖率 | 测试数 |
|------|--------|--------|
| Spring Service | 75% | 120 |
| Python API | 80% | 85 |
| Algorithm Core | 90% | 150 |

---

## 🐳 Docker 部署

### 开发环境

```bash
# 启动所有服务
docker-compose -f deployments/docker-compose.dev.yml up -d

# 查看日志
docker-compose -f deployments/docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f deployments/docker-compose.dev.yml down
```

### 生产环境

```bash
# 构建镜像
docker build -t uav-data-assimilation:latest ./service_spring

# 运行容器
docker run -d \
  -p 8084:8084 \
  -e DB_PASSWORD=${DB_PASSWORD} \
  -e SPRING_PROFILES_ACTIVE=prod \
  uav-data-assimilation:latest
```

---

## 📈 性能优化

### 基准测试

运行性能基准测试：

```bash
cd benchmarks

# 运行所有基准测试
python run_benchmarks.py

# 测试特定算法
python run_benchmarks.py --algorithm 3D-VAR

# 生成报告
python run_benchmarks.py --report --output benchmarks_report.html
```

### 性能指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 响应时间 (P95) | < 500ms | 320ms |
| 吞吐量 | > 100 req/s | 150 req/s |
| CPU 使用率 | < 70% | 55% |
| 内存使用 | < 2GB | 1.2GB |

---

## 🔒 安全配置

### JWT 配置

```yaml
uav:
  jwt:
    enabled: true
    secret: ${JWT_SECRET}
    expiration: 86400000
```

### 数据库安全

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/uav_data_assimilation?useSSL=true
    username: ${DB_USER}
    password: ${DB_PASSWORD}
```

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [Algorithm Core README](algorithm_core/README.md) | 核心算法库文档 |
| [Shared Resources README](shared/README.md) | 共享资源说明 |
| [Benchmarks README](benchmarks/README.md) | 性能测试说明 |
| [Deployment Guide](../docs/DEPLOYMENT.md) | 部署指南 |
| [API Documentation](../docs/api/) | API 接口文档 |

---

## 🔧 开发指南

### 代码规范

**Python 代码**:
```bash
# 格式化
black src/

# 检查
flake8 src/
pylint src/

# 类型检查
mypy src/
```

**Java 代码**:
```bash
# 格式化
mvn spotless:apply

# 检查
mvn checkstyle:check
```

### 提交规范

```
<type>(<scope>): <subject>

Types:
  - feat: 新功能
  - fix: 修复bug
  - docs: 文档更新
  - style: 代码格式
  - refactor: 重构
  - test: 测试
  - chore: 构建/工具
```

---

## 🤝 贡献指南

### 开发流程

1. **Fork** 项目
2. **创建分支**: `git checkout -b feature/your-feature`
3. **提交更改**: `git commit -am 'Add some feature'`
4. **推送分支**: `git push origin feature/your-feature`
5. **创建 Pull Request**

### 代码审查

- 所有 PR 需要通过 CI 测试
- 至少 1 人代码审查
- 遵循代码规范
- 添加测试用例

---

## 📄 许可证

本项目遵循项目整体许可证。

---

## 🙏 致谢

- **算法参考**: ECMWF, NCAR
- **开源库**: NumPy, SciPy, TensorFlow


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
