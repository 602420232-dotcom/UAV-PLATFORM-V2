# UAV Platform V1-V2 迁移指南

## 概述

本文档描述 UAV Platform 从 V1（原单体系统）迁移到 V2（微服务架构）的三阶段平滑过渡策略。V2 基于 Spring Boot 4.1.0 + Spring Cloud Gateway 构建，需要与 V1 系统实现无缝兼容和逐步切换。

---

## 三阶段迁移策略

### 阶段一：全量代理（Phase 1: Full Proxy）

**目标**：V2 Gateway 作为统一入口，将所有 V1 路径请求转发到原 V1 系统。

**持续时间**：1-2 周（验证稳定性）

**配置说明**：

在 `gateway/api-gateway/src/main/resources/application.yml` 中，V1 代理路由已配置在所有 V2 路由之前：

```yaml
- id: v1-legacy-proxy
  uri: ${V1_BASE_URL:http://localhost:8080}
  predicates:
    - Path=/api/v1/weather/**, /api/v1/planning/**, ...
  filters:
    - StripPrefix=0
    - name: Retry
      args:
        retries: 2
        statuses: BAD_GATEWAY,SERVICE_UNAVAILABLE
```

**关键要点**：
- V1 路由必须放在 V2 路由之前（Spring Cloud Gateway 按顺序匹配）
- `StripPrefix=0` 保持原路径不变转发到 V1
- 环境变量 `V1_BASE_URL` 控制 V1 系统地址

**启动步骤**：
1. 确认 V1 系统正常运行
2. 设置环境变量 `V1_BASE_URL=http://v1-server:8080`
3. 启动 V2 Gateway
4. 验证所有 V1 API 路径可正常访问
5. 监控日志确认请求被正确转发

---

### 阶段二：灰度迁移（Phase 2: Gray Release）

**目标**：按模块逐步将流量从 V1 切换到 V2，降低迁移风险。

**持续时间**：每模块 1-2 周

#### 灰度策略

1. **按 Header 灰度**：客户端携带 `X-Version: v2` 显式请求 V2
2. **按用户 ID 哈希灰度**：`user_id % 100 < percentage` 的用户走 V2
3. **按 API Key / 租户灰度**：特定租户优先使用 V2
4. **按 Cookie / Query Param 灰度**：支持多种灵活策略

#### 配置示例

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
        enabled: false
```

#### 灰度操作步骤

1. **准备阶段**：
   - 确认目标 V2 模块服务已部署并通过健康检查
   - 在 Redis 中预热灰度配置（可选）

2. **开启灰度**：
   ```bash
   # 方式1：修改 application.yml 后重启 Gateway
   # 方式2：通过 Redis 热更新（无需重启）
   redis-cli SET gray:release:weather '{"enabled":true,"percentage":5}'
   ```

3. **监控阶段**：
   - 观察 V2 服务错误率、延迟、吞吐量
   - 对比 V1 和 V2 的响应一致性
   - 关注客户端异常反馈

4. **逐步放量**：
   - 5% → 10% → 25% → 50% → 100%
   - 每个阶段至少观察 24 小时

5. **完成切换**：
   - 当某模块达到 100% 且稳定运行 3 天后
   - 将该模块从 V1 代理路由的 Path 中移除
   - 关闭该模块的灰度配置

#### 灰度过滤器的执行顺序

```
RequestLogFilter (HIGHEST)
  → V1JwtConvertFilter (HIGHEST + 5)   [JWT转换]
  → GrayReleaseFilter (HIGHEST + 15)   [灰度决策]
  → ApiVersionFilter (HIGHEST + 20)    [版本解析]
  → EmergencyPriorityFilter            [紧急优先级]
  → RateLimitFilter (HIGHEST + 40)     [限流]
```

---

### 阶段三：下线旧系统（Phase 3: Decommission）

**目标**：全部模块迁移完成后，删除 V1 代理路由，完全切换到 V2。

**前提条件**：
- 所有模块已 100% 切换到 V2 并稳定运行至少 1 周
- V1 系统连续 7 天无流量（通过日志确认）
- 数据一致性校验通过

**操作步骤**：

1. **移除 V1 代理路由**：
   ```yaml
   # 从 application.yml 中删除以下路由
   - id: v1-legacy-proxy
     uri: ${V1_BASE_URL:http://localhost:8080}
     ...
   ```

2. **清理相关配置**：
   - 删除 `gateway.v1.jwt.secret` 环境变量
   - 清理 Redis 中的灰度配置
   - 移除 V1 路径映射规则

3. **关闭灰度功能**：
   ```yaml
   gateway:
     gray-release:
       enabled: false
   ```

4. **下线 V1 系统**：
   - 停止 V1 应用服务
   - 备份 V1 数据库（保留 30 天）
   - 归档 V1 代码仓库

---

## JWT 鉴权转换

### V1 Token 特征

| Claim | V1 格式 | V2 格式 |
|-------|---------|---------|
| 签发者 | `iss`: "uav-platform-v1" | `iss`: "uav-platform-v2" |
| 用户 ID | `user_id` | `sub` |
| 角色 | `roles` | `authorities` |

### 转换流程

1. **识别 Token 版本**：
   - 尝试用 V2 密钥解析 → 成功则为 V2 Token，直接透传
   - 尝试用 V1 密钥解析 → 成功则为 V1 Token，执行转换
   - 均失败 → 返回 401

2. **Claims 映射**：
   ```
   user_id → sub
   roles → authorities (加 ROLE_ 前缀)
   ```

3. **重新签名**：
   - 使用 V2 密钥（HS256）重新签发 Token
   - 保留原过期时间
   - 添加 `original_iss` 和 `converted_at` 追踪字段

### 环境变量配置

```bash
# V1 JWT 密钥（用于验证 V1 Token）
export GATEWAY_V1_JWT_SECRET="v1-secret-key"

# V2 JWT 密钥（用于签发新 Token）
export GATEWAY_V2_JWT_SECRET="v2-secret-key-at-least-32-characters"
```

---

## 路径映射配置

### 路径重写规则

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
      param-rules:
        - name: coordinates-lat
          v1-name: lat
          v2-name: latitude
          description: 纬度参数映射
        - name: coordinates-lon
          v1-name: lon
          v2-name: longitude
          description: 经度参数映射
```

### 参数转换类型

| 转换类型 | 说明 | 示例 |
|----------|------|------|
| `uppercase` | 转大写 | `admin` → `ADMIN` |
| `lowercase` | 转小写 | `ADMIN` → `admin` |
| `boolean-string` | 布尔转字符串 | `1` → `true` |
| `int-boolean` | 字符串转布尔 | `true` → `1` |

---

## 回滚方案

### 场景1：灰度期间 V2 服务异常

**症状**：V2 服务错误率升高或响应超时

**回滚步骤**：
1. 立即将灰度百分比降为 0：
   ```bash
   redis-cli SET gray:release:weather '{"enabled":true,"percentage":0}'
   ```
2. 或关闭模块灰度：
   ```yaml
   modules:
     weather:
       enabled: false
   ```
3. 所有流量自动回退到 V1（通过 V1 代理路由）

### 场景2：JWT 转换异常

**症状**：大量 401 错误

**回滚步骤**：
1. 检查 `gateway.v1.jwt.secret` 配置是否正确
2. 临时禁用 JWT 转换（修改代码或配置）
3. 让 V1 Token 直接透传到 V1 系统处理

### 场景3：Gateway 整体故障

**症状**：Gateway 无法启动或频繁崩溃

**回滚步骤**：
1. 停止 V2 Gateway
2. 将 DNS/负载均衡指向 V1 系统直接地址
3. 紧急修复后重新上线 Gateway

---

## 监控指标

### 关键指标

| 指标名称 | 类型 | 告警阈值 | 说明 |
|----------|------|----------|------|
| `gateway.v1.proxy.requests` | Counter | - | V1 代理请求总数 |
| `gateway.v1.proxy.errors` | Counter | > 10/分钟 | V1 代理错误数 |
| `gateway.v1.proxy.latency` | Timer | P99 > 2s | V1 代理延迟 |
| `gateway.jwt.convert.count` | Counter | - | JWT 转换次数 |
| `gateway.jwt.convert.errors` | Counter | > 5/分钟 | JWT 转换失败数 |
| `gateway.gray.route.v2` | Counter | - | 路由到 V2 的请求数 |
| `gateway.gray.route.v1` | Counter | - | 路由到 V1 的请求数 |

### 日志关键字

```
# V1 代理转发
[JWT-CONVERT] V1 token detected, converting to V2
[GRAY-RELEASE] Decision | module={} | routeToV2={}
[V1-MAPPING] Path mapped: {} → {}

# 错误告警
[JWT-CONVERT] Invalid token, rejecting
[GRAY-RELEASE] Failed to load config from Redis
```

### 健康检查端点

```bash
# Gateway 健康状态
curl http://gateway:8088/actuator/health

# 路由列表（确认 V1 代理路由存在）
curl http://gateway:8088/actuator/gateway/routes

# 灰度配置状态
curl http://gateway:8088/actuator/gateway/globalfilters
```

---

## 常见问题排查

### Q1: V1 请求没有被转发到 V1 系统

**排查步骤**：
1. 检查 `application.yml` 中 V1 路由是否在 V2 路由之前
2. 确认 `V1_BASE_URL` 环境变量指向正确的 V1 地址
3. 查看 Gateway 日志确认路由匹配结果
4. 检查 Path predicate 是否包含该请求路径

### Q2: JWT Token 转换失败

**排查步骤**：
1. 确认 `GATEWAY_V1_JWT_SECRET` 与 V1 系统的密钥一致
2. 检查 Token 格式是否为标准 JWT（Header.Payload.Signature）
3. 查看日志中的具体错误信息
4. 临时在 V1 系统上验证 Token 有效性

### Q3: 灰度配置不生效

**排查步骤**：
1. 确认 `gateway.gray-release.enabled=true`
2. 检查目标模块的 `enabled` 和 `percentage` 配置
3. 验证 Redis 配置是否覆盖了 YAML 配置
4. 确认 GrayReleaseFilter 的执行顺序正确

### Q4: 路径映射未生效

**排查步骤**：
1. 确认 `gateway.v1.mapping.enabled=true`
2. 检查路径规则的正则表达式是否正确匹配
3. 确认 `@ConfigurationProperties` 已正确绑定
4. 查看日志中的 `[V1-MAPPING]` 输出

### Q5: 循环路由或 404 错误

**排查步骤**：
1. 检查是否存在路径重叠导致路由冲突
2. 确认 V1 代理路由的 Path 列表完整
3. 验证 `StripPrefix` 配置是否正确
4. 使用 `/actuator/gateway/routes` 查看实际路由表

---

## 环境变量汇总

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `V1_BASE_URL` | `http://localhost:8080` | V1 系统基础地址 |
| `GATEWAY_V1_JWT_SECRET` | - | V1 JWT 验证密钥 |
| `GATEWAY_V2_JWT_SECRET` | - | V2 JWT 签名密钥 |
| `GATEWAY_GRAY_RELEASE_ENABLED` | `false` | 是否启用灰度发布 |
| `REDIS_HOST` | `localhost` | Redis 地址（灰度配置热更新） |
| `REDIS_PORT` | `6379` | Redis 端口 |

---

## 附录

### 模块迁移检查清单

- [ ] V2 服务部署完成并通过健康检查
- [ ] API 兼容性测试通过
- [ ] 数据库迁移脚本执行成功
- [ ] JWT 转换验证通过
- [ ] 灰度配置准备就绪
- [ ] 监控告警配置完成
- [ ] 回滚方案文档化
- [ ] 运维团队培训完成

### 联系人

| 角色 | 职责 | 联系方式 |
|------|------|----------|
| 架构组 | 技术方案评审 | - |
| 运维组 | 部署与监控 | - |
| 业务组 | 业务验证 | - |
