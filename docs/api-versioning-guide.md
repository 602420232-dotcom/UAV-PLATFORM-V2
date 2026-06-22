# UAV Platform V2 - API 版本管理指南

> 最后更新：2026-06-16
> 适用版本：V2.0.0+

---

## 概述

UAV Platform V2 支持与 V1 系统的 API 版本共存，通过 Spring Cloud Gateway 实现统一的 API 版本路由、JWT 鉴权转换和灰度发布。本文档描述 V1 和 V2 的 API 路径规划、版本映射规则以及灰度发布配置。

---

## 1. API 版本策略

### 1.1 版本标识

| 版本 | 路径前缀 | 状态 |
|------|----------|------|
| V1 | `/api/v1/**` | 维护中（逐步迁移） |
| V2 | `/api/v2/**` | 活跃开发 |

### 1.2 路由优先级

Gateway 按以下顺序匹配路由（优先级从高到低）：

1. **V1 代理路由**（`v1-legacy-proxy`）- 将未灰度的 V1 请求转发到原 V1 系统
2. **V2 服务路由** - 直接路由到 V2 微服务
3. **Actuator 路由** - 运维端点

---

## 2. V1 API 路径列表

以下路径由 V1 系统提供服务，通过 Gateway 代理转发：

| 模块 | 路径前缀 | V1 服务端口 |
|------|----------|------------|
| 平台管理 | `/api/v1/tenants/**` | 8080 |
| API 密钥 | `/api/v1/api-keys/**` | 8080 |
| 用量统计 | `/api/v1/usage/**` | 8080 |
| 平台配置 | `/api/v1/platform/**` | 8080 |
| 气象服务 | `/api/v1/weather/**` | 8081 |
| 同化服务 | `/api/v1/assimilation/**` | 8082 |
| 风险评估 | `/api/v1/risk/**` | 8083 |
| 观测服务 | `/api/v1/observation/**` | 8084 |
| 规划服务 | `/api/v1/planning/**` | 8085 |
| UTM 服务 | `/api/v1/utm/**` | 8086 |
| 飞行计划 | `/api/v1/flight/**` | 8086 |

### 2.1 V1 专属路径（无 V2 对应）

以下路径仅在 V1 系统中存在，V2 暂不提供对应接口：

| 路径 | 说明 | 迁移建议 |
|------|------|----------|
| `/api/v1/weather/buoy/**` | 浮标气象数据 | V2 规划中 |
| `/api/v1/weather/ground-station/**` | 地面站气象 | V2 规划中 |
| `/api/v1/weather/satellite/**` | 卫星气象数据 | V2 规划中 |
| `/api/v1/weather/radiosonde/**` | 探空气象数据 | V2 规划中 |
| `/api/v1/detection/drone/**` | 无人机探测 | V2 规划中 |

---

## 3. V2 API 路径列表

以下路径由 V2 微服务直接提供：

| 模块 | 路径前缀 | V2 服务名 | 内部端口 | 外部端口 |
|------|----------|----------|----------|----------|
| 平台管理 | `/api/v2/tenants/**` | platform-api | 8081 | 8251 |
| API 密钥 | `/api/v2/api-keys/**` | platform-api | 8081 | 8251 |
| 用量统计 | `/api/v2/usage/**` | platform-api | 8081 | 8251 |
| 平台配置 | `/api/v2/platform/**` | platform-api | 8081 | 8251 |
| 气象服务 | `/api/v2/weather/**` | weather-api | 8082 | 8252 |
| 同化服务 | `/api/v2/assimilation/**` | assimilation-api | 8083 | 8253 |
| 风险评估 | `/api/v2/risk/**` | risk-api | 8084 | 8254 |
| 观测服务 | `/api/v2/observation/**` | observation-api | 8085 | 8255 |
| 规划服务 | `/api/v2/planning/**` | planning-api | 8086 | 8256 |
| UTM 服务 | `/api/v2/utm/**` | utm-api | 8087 | 8259 |
| 飞行计划 | `/api/v2/flight/**` | utm-api | 8087 | 8259 |
| 算法引擎 | `/api/v2/algorithms/**` | algorithm-engine | 9090 | 9095 |
| 算法任务 | `/api/v2/tasks/**` | algorithm-engine | 9090 | 9095 |

### 3.1 V2 新增路径

以下路径为 V2 新增功能，V1 无对应接口：

| 路径 | 说明 | 服务 |
|------|------|------|
| `/api/v2/weather/ensemble/**` | 集合预报 | weather-api |
| `/api/v2/assimilation/4dvar/**` | 4D-VAR 同化 | assimilation-api |
| `/api/v2/risk/federated/**` | 联邦学习风险评估 | risk-api |
| `/api/v2/planning/multi-objective/**` | 多目标路径规划 | planning-api |
| `/api/v2/observation/adaptive/**` | 自适应观测 | observation-api |

---

## 4. 路径映射规则

### 4.1 路径重写配置

在 `application.yml` 中配置 V1 到 V2 的路径映射：

```yaml
gateway:
  v1:
    mapping:
      enabled: true
      path-rules:
        - name: weather-point
          v1-pattern: /api/v1/weather/point
          v2-template: /api/v2/weather/point
          description: 天气单点查询接口路径映射
        - name: weather-region
          v1-pattern: /api/v1/weather/region
          v2-template: /api/v2/weather/region
          description: 天气区域查询接口路径映射
        - name: planning-route
          v1-pattern: /api/v1/planning/route
          v2-template: /api/v2/planning/route
          description: 路径规划接口路径映射
        - name: risk-assessment
          v1-pattern: /api/v1/risk/assessment
          v2-template: /api/v2/risk/assessment
          description: 风险评估接口路径映射
      param-rules:
        - name: coordinates-lat
          v1-name: lat
          v2-name: latitude
          description: 纬度参数映射
        - name: coordinates-lon
          v1-name: lon
          v2-name: longitude
          description: 经度参数映射
        - name: time-format
          v1-name: time
          v2-name: timestamp
          description: 时间参数映射
```

### 4.2 参数转换类型

| 转换类型 | 说明 | 示例 |
|----------|------|------|
| `uppercase` | 转大写 | `admin` → `ADMIN` |
| `lowercase` | 转小写 | `ADMIN` → `admin` |
| `boolean-string` | 布尔转字符串 | `1` → `true` |
| `int-boolean` | 字符串转布尔 | `true` → `1` |
| `date-iso8601` | 日期格式转换 | `2026-06-16` → `2026-06-16T00:00:00Z` |

---

## 5. JWT 鉴权转换

### 5.1 Token 版本识别

Gateway 通过以下方式自动识别 Token 版本：

1. **尝试 V2 密钥解析** → 成功则为 V2 Token，直接透传
2. **尝试 V1 密钥解析** → 成功则为 V1 Token，执行转换
3. **均失败** → 返回 401 Unauthorized

### 5.2 Claims 映射

| V1 Claim | V2 Claim | 转换规则 |
|----------|----------|----------|
| `iss` | `iss` | V1: "uav-platform-v1" → V2: "uav-platform-v2" |
| `user_id` | `sub` | 字段名映射 |
| `roles` | `authorities` | 值加 `ROLE_` 前缀 |
| `tenant_id` | `tenant_id` | 直接透传 |
| `exp` | `exp` | 保留原过期时间 |

### 5.3 转换后 Token 特征

```json
{
  "iss": "uav-platform-v2",
  "sub": "user-12345",
  "authorities": ["ROLE_OPERATOR", "ROLE_TENANT_ADMIN"],
  "tenant_id": "tenant-alpha",
  "original_iss": "uav-platform-v1",
  "converted_at": 1750032000,
  "exp": 1750118400
}
```

---

## 6. 灰度发布配置

### 6.1 灰度策略类型

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| Header 灰度 | `X-Version: v2` 显式请求 V2 | 测试验证 |
| 用户哈希灰度 | `user_id % 100 < percentage` | 逐步放量 |
| 租户灰度 | 指定租户优先使用 V2 | 早期用户 |
| Cookie 灰度 | `version=v2` Cookie 标记 | A/B 测试 |

### 6.2 灰度配置示例

```yaml
gateway:
  gray-release:
    enabled: true
    default-percentage: 0
    header-key: X-Version
    header-value: v2
    modules:
      weather:
        enabled: true
        percentage: 10
        header-key: X-Version
        header-value: v2
        tenants:
          - tenant-alpha
          - tenant-beta
      planning:
        enabled: true
        percentage: 5
        header-key: X-Version
        header-value: v2
      risk:
        enabled: false
      observation:
        enabled: false
      assimilation:
        enabled: false
      utm:
        enabled: false
```

### 6.3 灰度过滤器执行顺序

```
RequestLogFilter (HIGHEST)
  → V1JwtConvertFilter (HIGHEST + 5)    [JWT 转换]
  → GrayReleaseFilter (HIGHEST + 15)    [灰度决策]
  → ApiVersionFilter (HIGHEST + 20)     [版本解析]
  → EmergencyPriorityFilter             [紧急优先级]
  → RateLimitFilter (HIGHEST + 40)      [限流]
```

---

## 7. Gateway 路由配置

### 7.1 完整路由表

```yaml
spring:
  cloud:
    gateway:
      routes:
        # V1 代理路由（优先级最高）
        - id: v1-legacy-proxy
          uri: ${V1_BASE_URL:http://localhost:8080}
          predicates:
            - Path=/api/v1/weather/**, /api/v1/planning/**, /api/v1/risk/**, /api/v1/observation/**, /api/v1/assimilation/**, /api/v1/utm/**, /api/v1/tenants/**, /api/v1/api-keys/**, /api/v1/usage/**, /api/v1/platform/**, /api/v1/flight/**
          filters:
            - StripPrefix=0
            - name: Retry
              args:
                retries: 2
                statuses: BAD_GATEWAY,SERVICE_UNAVAILABLE

        # V2 服务路由（按模块）
        - id: platform-api
          uri: lb://platform-api
          predicates:
            - Path=/api/v1/tenants/**, /api/v2/tenants/**, /api/v1/api-keys/**, /api/v2/api-keys/**, /api/v1/usage/**, /api/v2/usage/**, /api/v1/platform/**, /api/v2/platform/**

        - id: weather-api
          uri: lb://weather-api
          predicates:
            - Path=/api/v1/weather/**, /api/v2/weather/**

        - id: assimilation-api
          uri: lb://assimilation-api
          predicates:
            - Path=/api/v1/assimilation/**, /api/v2/assimilation/**

        - id: risk-api
          uri: lb://risk-api
          predicates:
            - Path=/api/v1/risk/**, /api/v2/risk/**

        - id: observation-api
          uri: lb://observation-api
          predicates:
            - Path=/api/v1/observation/**, /api/v2/observation/**

        - id: planning-api
          uri: lb://planning-api
          predicates:
            - Path=/api/v1/planning/**, /api/v2/planning/**

        - id: utm-api
          uri: lb://utm-api
          predicates:
            - Path=/api/v1/utm/**, /api/v2/utm/**, /api/v1/flight/**, /api/v2/flight/**
```

### 7.2 Docker 环境路由

在 Docker 环境中，服务发现禁用，使用显式服务地址：

```yaml
spring:
  config:
    activate:
      on-profile: docker
  cloud:
    gateway:
      discovery:
        locator:
          enabled: false
      routes:
        - id: platform-api
          uri: http://platform-api:8081
          # ...
        - id: weather-api
          uri: http://weather-api:8082
          # ...
```

---

## 8. 环境变量配置

### 8.1 V1 集成变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `V1_BASE_URL` | `http://localhost:8080` | V1 系统基础地址 |
| `GATEWAY_V1_JWT_SECRET` | - | V1 JWT 验证密钥（用于 Token 转换） |
| `GATEWAY_V2_JWT_SECRET` | - | V2 JWT 签名密钥（用于签发新 Token） |

### 8.2 灰度发布变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `GATEWAY_GRAY_RELEASE_ENABLED` | `false` | 是否启用灰度发布 |
| `GATEWAY_GRAY_RELEASE_DEFAULT_PERCENTAGE` | `0` | 默认灰度百分比 |

### 8.3 Vault 变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `VAULT_ENABLED` | `false` | 是否启用 Vault |
| `VAULT_ADDR` | `http://localhost:8200` | Vault 服务器地址 |
| `VAULT_TOKEN` | - | Vault 访问 Token |
| `VAULT_NAMESPACE` | - | Vault 命名空间 |
| `VAULT_KV_VERSION` | `2` | KV 引擎版本 |

---

## 9. 迁移检查清单

### 9.1 模块迁移状态

| 模块 | V1 代理 | V2 服务 | 灰度状态 | 计划下线 |
|------|---------|---------|----------|----------|
| 平台管理 | 活跃 | 就绪 | 0% | 待定 |
| 气象服务 | 活跃 | 就绪 | 0% | 待定 |
| 同化服务 | 活跃 | 就绪 | 0% | 待定 |
| 风险评估 | 活跃 | 就绪 | 0% | 待定 |
| 观测服务 | 活跃 | 就绪 | 0% | 待定 |
| 规划服务 | 活跃 | 就绪 | 0% | 待定 |
| UTM 服务 | 活跃 | 就绪 | 0% | 待定 |

### 9.2 迁移验证步骤

1. [ ] V1 代理路由配置正确，请求可正常转发到 V1 系统
2. [ ] V2 服务健康检查通过
3. [ ] JWT 转换功能验证（V1 Token → V2 Token）
4. [ ] 灰度配置热更新验证（Redis 方式）
5. [ ] 路径映射规则验证
6. [ ] 监控指标采集验证
7. [ ] 回滚流程验证

---

## 10. 常见问题

### Q1: V1 请求返回 404

**排查**：
1. 检查 `V1_BASE_URL` 是否指向正确的 V1 服务地址
2. 确认 V1 代理路由的 `Path` 列表包含该请求路径
3. 查看 Gateway 日志确认路由匹配结果

### Q2: JWT 转换后权限丢失

**排查**：
1. 确认 `GATEWAY_V1_JWT_SECRET` 与 V1 系统密钥一致
2. 检查 V1 Token 的 `roles` 字段格式
3. 查看转换后的 Token `authorities` 字段

### Q3: 灰度配置不生效

**排查**：
1. 确认 `gateway.gray-release.enabled=true`
2. 检查目标模块的 `enabled` 和 `percentage` 配置
3. 验证 Redis 配置是否覆盖了 YAML 配置
4. 确认 GrayReleaseFilter 在 V1JwtConvertFilter 之后执行

### Q4: V2 服务返回 502

**排查**：
1. 确认 V2 目标服务已启动并通过健康检查
2. 检查服务间网络连通性（Docker/K8s）
3. 验证 Nacos 服务注册状态（如启用服务发现）

---

*文档版本：v1.0*
*维护团队：架构组*
