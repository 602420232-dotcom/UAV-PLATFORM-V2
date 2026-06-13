# UAV Platform V2 版本状态看板

> 更新日期：2026-06-13
> 当前阶段：MVP 一期 E2E 验收

---

## 分支策略

| 分支 | Spring Boot | 用途 | 状态 |
|------|-------------|------|------|
| `main` | **4.0.0** | 主分支，7 个业务服务 + E2E 测试 | ✅ 正常运行 |
| `gateway-legacy` | **3.4.x** | 独立网关分支，兼容 Spring Cloud Gateway | 🔄 待验证 |

---

## 服务运行状态（main 分支）

| 服务 | 端口 | 依赖 | 状态 | 备注 |
|------|------|------|------|------|
| platform-api | 18081 | MySQL + Redis | ✅ UP | 平台服务 |
| weather-api | 18082 | Redis | ✅ UP | 气象服务 |
| assimilation-api | 18083 | MySQL + Redis + Kafka | ✅ UP | 同化服务 |
| risk-api | 18084 | Redis | ✅ UP | 风险评估 |
| observation-api | 18085 | MySQL + Redis | ✅ UP | 观测决策 |
| planning-api | 18086 | MySQL + Redis | ✅ UP | 路径规划 |
| utm-api | 18087 | Redis | ✅ UP | UTM 服务 |
| **api-gateway** | — | — | ⚠️ **未适配** | 见下方说明 |

---

## E2E 测试结果（main 分支）

```
总计: 9  |  通过: 9  |  失败: 0  |  跳过: 0
结果: 全部通过 ✅
```

测试项：
- ✅ 健康检查（6 服务全部 UP）
- ✅ 气象数据查询
- ✅ 数据同化任务
- ✅ 风险评估
- ✅ 适航评估
- ✅ 观测决策
- ✅ 路径规划
- ✅ UTM 飞行计划生命周期
- ✅ 完整端到端管线

---

## 已知问题与限制

### 🔴 api-gateway 暂未适配 Spring Boot 4.0

**原因：**
- Spring Cloud Gateway 4.3.5（最新版）仍依赖 Spring Boot 3.x 的 `NettyWebServerFactoryCustomizer`
- Spring Boot 4.0 重构了 Netty 自动配置，该类已被移除
- 目前 **没有任何版本** 的 Spring Cloud Gateway 兼容 Spring Boot 4.0

**影响：**
- 开发/测试环境：E2E 测试直接连接业务服务（已验证通过）
- 生产环境：如需网关路由，请使用 `gateway-legacy` 分支独立部署

**解决方案时间线：**
1. **短期**：使用 `gateway-legacy` 分支（Spring Boot 3.4.x + Gateway 4.1.x）独立部署
2. **中期**：定时关注 Spring Cloud Gateway 官方发布日志
3. **长期**：待官方发布兼容 Spring Boot 4.x 版本后，统一升级合并到 main

**监控计划：**
- 每周检查 [Spring Cloud Gateway Maven Central](https://repo.maven.apache.org/maven2/org/springframework/cloud/spring-cloud-gateway-server/)
- 关注 [Spring Cloud 官方博客](https://spring.io/blog) 和 Release Notes
- 目标版本：Spring Cloud Gateway 4.4.x+ 或 Spring Cloud 2025.2.x+

---

## 基础设施状态

| 组件 | 版本 | 状态 | 访问地址 |
|------|------|------|----------|
| MySQL | 8.4.7 | ✅ 运行中 | localhost:3306 |
| Redis | 7.2 | ✅ 运行中 | localhost:6379 |
| Kafka | 7.5.0 | ✅ 运行中 | localhost:19092 |
| Zookeeper | 3.9 | ✅ 运行中 | localhost:12181 |

---

## 兼容性修复记录

| # | 问题 | 解决方案 | 涉及模块 |
|---|------|----------|----------|
| 1 | Docker 网络冲突 | 改用 172.28.0.0/16 | docker-compose.yml |
| 2 | Kafka 端口冲突 | 改为 19092 | docker-compose.yml |
| 3 | MyBatis Plus 不兼容 Boot 4.0 | 升级 3.5.16 + boot4 starter | 全部服务 |
| 4 | MySQL caching_sha2_password | JDBC URL + allowPublicKeyRetrieval | 全部服务 |
| 5 | Nacos config 依赖冲突 | 彻底移除 Nacos config + discovery | 全部服务 |
| 6 | HmacAuthenticationFilter 装配失败 | 条件装配 + List<HandlerMapping> | common-security |
| 7 | RedisTemplate bean 缺失 | 手动配置 RedisConfig | common-core |
| 8 | DataSource 冲突 | @Primary + 排除自动配置 | platform-api |
| 9 | KafkaTemplate 缺失 | 添加 spring-boot-starter-kafka | common-kafka |
| 10 | Redis Reactive 不兼容 | 改为 spring-boot-starter-data-redis | api-gateway |

---

## 访问策略

### 开发 / 测试（推荐）
```bash
# E2E 测试直连业务服务
python scripts/e2e-test.py --mock

# 或直接调用各服务
http://localhost:18081  # platform
http://localhost:18082  # weather
http://localhost:18083  # assimilation
http://localhost:18084  # risk
http://localhost:18085  # observation
http://localhost:18086  # planning
http://localhost:18087  # utm
```

### 生产（如需网关）
```bash
# 切换到 gateway-legacy 分支，独立部署网关
git checkout gateway-legacy
cd gateway/api-gateway
mvn clean package
java -jar target/api-gateway-2.0.0.jar
```
