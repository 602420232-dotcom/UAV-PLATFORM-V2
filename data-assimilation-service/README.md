# 贝叶斯同化服务

## 概述

贝叶斯同化服务整合了贝叶斯数据同化核心算法库，通过 REST API 提供数据同化计算服务。支持 3D-VAR、4D-VAR、EnKF 等算法，用于融合多源气象观测数据。

## 技术栈

- **框架**: Spring Boot 3.2.0
- **语言**: Java 17 + Python 3.8+
- **构建工具**: Maven
- **算法引擎**: Python (bayesian_assimilation.py)
- **弹性机制**: Resilience4j Circuit Breaker

## 服务信息

- **服务端口**: 8084
- **服务名称**: data-assimilation-service
- **熔断器**: ✅ 已启用（通过 common-utils）

## 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/assimilation/execute` | POST | 执行贝叶斯同化 |
| `/api/assimilation/variance` | POST | 计算方差场 |
| `/api/assimilation/batch` | POST | 批量执行同化 |
| `/api/admin/circuit-breaker/status` | GET | 熔断器状态 |

## 熔断器配置

作为被调用服务，data-assimilation-service 提供给 API Gateway 的熔断器保护：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **失败率阈值** | 45% | 超过此阈值触发熔断 |
| **恢复等待时间** | 8秒 | 熔断打开后等待时间 |
| **滑动窗口** | 8次调用 | 计算失败率的窗口大小 |
| **熔断器类型** | critical | 关键服务配置 |

详见: [Circuit Breaker Guide](../../docs/CIRCUIT_BREAKER_GUIDE.md)

## Python 依赖

| 包 | 版本 | 用途 |
|---|------|------|
| numpy | >=1.24.0 | 数值计算 |
| scipy | >=1.11.0 | 科学计算 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_PASSWORD` | （必填） | 数据库密码 |
| `assimilation.python-script` | `src/main/python/bayesian_assimilation.py` | Python 脚本路径 |
| `SERVER_PORT` | `8084` | 服务端口 |
| `JWT_SECRET` | （必填） | JWT签名密钥（生产环境必需） |

## 构建与运行

```bash
# 构建
mvn clean package -DskipTests

# 运行
mvn spring-boot:run
```

## 配置

详见 `src/main/resources/application.yml`。

## 依赖服务

- **MySQL**: 数据存储（启动前需运行）
- **Redis**: 缓存（可选）
- **uav-platform-service**: 认证服务（可选）
- **API Gateway**: 通过熔断器保护调用


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
