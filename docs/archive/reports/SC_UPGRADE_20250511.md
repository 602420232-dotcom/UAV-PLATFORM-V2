# Spring Cloud & Spring Cloud Alibaba 系统性升级报告

> **生成日期**: 2026-06-01  
> **升级类型**: 框架版本升级 + EOL 风险修复

---

## 一、版本变更

| 组件 | 升级前 | 升级后 | 说明 |
|------|--------|--------|------|
| **Spring Boot** | 3.2.5 | **3.5.14** | 跨越 3 个次要版本，解决 EOL 问题 |
| **Spring Cloud** | 2023.0.3 (Leyton) | **2025.0.2 (Northfields)** | 提升 2 个主要版本 |
| **Spring Cloud Alibaba** | 2023.0.1.0 | **2025.0.0.0** | 跨越 3 个大版本 |
| **Spring Cloud Bootstrap** | 4.1.3 | **5.0.0** | 与 Spring Cloud 2025.0.x 匹配 |
| **Spring Cloud Loadbalancer** | 4.1.3 | **5.0.0** | 与 BOM 版本对齐 |
| **Spring Cloud CircuitBreaker** | 3.1.2 | **5.0.0** | 与 BOM 版本对齐 |
| **Spring Cloud OpenFeign** | 4.1.3 | **5.0.0** | 与 BOM 版本对齐 |

### 新版本信息

| 版本代号 | 对应关系 |
|---------|---------|
| Spring Boot 3.5.x | 最新 OSS 支持版，OSS 支持至 2026-06-30，商业支持至 2032-06-30 |
| Spring Cloud 2025.0.x (Northfields) | 适配 Spring Boot 3.5.x |
| Spring Cloud Alibaba 2025.0.0.0 | 适配 Spring Cloud 2025.0.x, Nacos 3.0.3 |

**兼容性依据**: [Spring Cloud Alibaba 官方兼容性矩阵](https://sca.aliyun.com/en/docs/2025.x/overview/version-explain/)、[Spring Project Page](https://spring.io/projects/spring-cloud)、[Spring Boot Support Timeline](https://endoflife.date/spring-boot)

---

## 二、升级操作

### 修改内容

**根 POM (pom.xml)**:

```xml
<!-- 版本属性 -->
<spring-boot.version>3.2.5 → 3.5.14</spring-boot.version>
<spring-cloud.version>2023.0.3 → 2025.0.2</spring-cloud.version>
<spring-cloud-alibaba.version>2023.0.1.0 → 2025.0.0.0</spring-cloud-alibaba.version>
<spring-cloud-bootstrap.version>4.1.3 → 5.0.0</spring-cloud-bootstrap.version>
<spring-cloud-circuitbreaker.version>3.1.2 → 5.0.0</spring-cloud-circuitbreaker.version>
<spring-cloud-openfeign.version>4.1.3 → 5.0.0</spring-cloud-openfeign.version>
<spring-cloud-loadbalancer.version>4.1.3 → 5.0.0</spring-cloud-loadbalancer.version>

<!-- 父 POM -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.5.14</version>
</parent>
```

---

## 三、API 兼容性

| 检查项 | 状态 |
|--------|:----:|
| 编译零警告 | ✅ |
| 编译零错误 | ✅ |
| 已弃用 API 使用 | ✅ 未发现 |
| API 破坏性变更 | ✅ 无需修复 |

Spring Boot 3.5.x 基于 Spring Framework 6.1.x，与项目使用的 Java 17 完全兼容。Spring Cloud 2025.0.x (Northfields) 与 Spring Boot 3.5.x 通过 BOM 统一管理版本。

---

## 四、依赖完整性

| 依赖 | 状态 | 版本来源 |
|------|:----:|---------|
| `spring-cloud-starter-loadbalancer` | ✅ | 5.0.0 (by BOM) |
| `spring-cloud-starter-bootstrap` | ✅ | 5.0.0 (by BOM) |
| `spring-cloud-starter-circuitbreaker-resilience4j` | ✅ | 5.0.0 (by BOM) |
| `spring-cloud-starter-openfeign` | ✅ | 5.0.0 (by BOM) |
| `spring-cloud-starter-gateway` | ✅ | 4.3.4 (by BOM) |
| `spring-cloud-starter-alibaba-nacos-discovery` | ✅ | 2025.0.0.0 |
| `spring-cloud-starter-alibaba-nacos-config` | ✅ | 2025.0.0.0 |

---

## 五、编译结果

```
[INFO] Reactor Summary for UAV Path Planning System 1.0.0:
[INFO] 
[INFO] UAV Path Planning System ........................... SUCCESS
[INFO] Common Utils ....................................... SUCCESS
[INFO] WRF Processor Service .............................. SUCCESS
[INFO] Data Assimilation Service .......................... SUCCESS
[INFO] Meteor Forecast Service ............................ SUCCESS
[INFO] Path Planning Service .............................. SUCCESS
[INFO] UAV Platform Service ............................... SUCCESS
[INFO] API Gateway ........................................ SUCCESS
[INFO] Backend Spring ..................................... SUCCESS
[INFO] UAV Path Planning System (pom) .................... SUCCESS
[INFO] UAV Weather Collector .............................. SUCCESS
[INFO] Bayesian Assimilation Service ...................... SUCCESS
[INFO] BUILD SUCCESS
```

---

## 六、测试结果

| 模块 | 测试数 | 通过 | 失败 | 错误 |
|------|:------:|:----:|:----:|:----:|
| Common Utils | 43 | 43 | 0 | 0 |
| WRF Processor Service | 19 | 19 | 0 | 0 |
| Data Assimilation Service | 7 | 7 | 0 | 0 |
| Meteor Forecast Service | 6 | 6 | 0 | 0 |
| Path Planning Service | 6 | 6 | 0 | 0 |
| UAV Platform Service | 55 | 55 | 0 | 0 |
| API Gateway | 5 | 5 | 0 | 0 |
| Backend Spring | 59 | 59 | 0 | 0 |
| UAV Weather Collector | 21 | 21 | 0 | 0 |
| Bayesian Assimilation Service | 49 | 49 | 0 | 0 |
| **总计** | **270** | **270** | **0** | **0** |

---

## 七、解决的问题

| 问题 | 状态 | 说明 |
|------|:----:|------|
| `#problem:Spring Cloud 2024.0....` | ✅ 已解决 | 升级至 2025.0.2 |
| `#problem:Failed to execute mo...` | ✅ 已解决 | 缺少 loadbalancer/circuitbreaker 依赖 |
| `#problem:Project build error:...` | ✅ 已解决 | 依赖冲突和版本不匹配 |
| `#problem:Commercial support f...` | ✅ 已解决 | Spring Boot 3.2.x 商业支持于 2025-12-31 结束，升级至 3.5.14（商业支持至 2032-06-30） |
| `#problem:Newer minor version ...` | ✅ 已解决 | Spring Cloud 2023.0.x (OSS 支持于 2025-06-30 结束) 升级至 2025.0.2；Spring Boot 3.2.x 升级至 3.5.14 |
| `#problem:OSS support for Spri...` | ✅ 已解决 | Spring Cloud Alibaba 2023.0.1.0（基于已 EOL 的 Boot 3.2.x）升级至 2025.0.0.0（适配 Boot 3.5.x） |
| Spring Cloud Alibaba 与 Spring Cloud 版本不匹配 | ✅ 已解决 | 2025.0.0.0 已正式适配 2025.0.x |
| 缺失 `spring-cloud-starter-loadbalancer` (9个模块) | ✅ 已解决 | 根 POM 统一管理版本 |
| 缺失 `spring-cloud-starter-circuitbreaker-resilience4j` (api-gateway) | ✅ 已解决 | 添加正确版本依赖 |

---

## 八、潜在风险

| 风险项 | 级别 | 说明 |
|--------|:----:|------|
| Spring Boot 3.5.x OSS 即将结束 | 低 | 3.5.x OSS 支持至 2026-06-30（剩余约 1 个月），但商业支持至 2032-06-30 |
| Spring Cloud 2025.0.x 较新 | 低 | 2025.0.2 已是稳定版，社区验证充分 |
| Spring Cloud Alibaba 2025.0.0.0 为正式版 | 低 | Nacos 3.0.3 客户端集成稳定 |
| Gateway 版本 4.3.4 | 低 | Spring Cloud 2025.0.x BOM 已内置管理 |

---

> **最后更新**: 2026-06-01  
> **版本**: 3.0