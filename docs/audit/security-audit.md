# 🔒 UAV Platform 安全漏洞扫描报告

> **扫描日期**: 2026-05-31  
> **扫描范围**: `/mnt/d/Developer/workplace/py/iteam/trae` (全项目)  
> **扫描工具**: 自动化代码审计 (grep + 人工分析)  
> **扫描文件类型**: Java, Python, Dart, YAML/XML/Properties, Dockerfile, JS/TS, Shell, Config  

---

## 📊 摘要

| 级别 | 数量 | 状态 |
|------|------|------|
| 🔴 CRITICAL | 4 | 已自动修复 3, 需手动处理 1 |
| 🟠 HIGH | 3 | 已自动修复 2, 需手动处理 1 |
| 🟡 MEDIUM | 6 | 已自动修复 1, 需手动处理 5 |
| 🔵 LOW | 4 | 需手动处理 4 |
| **总计** | **17** | **自动修复 6, 需手动处理 11** |

---

## 🔴 CRITICAL (立即修复)

### NOC-01: API V1 登录接口无凭据验证 (认证绕过)

- **文件**: `uav-platform-service/src/main/java/com/uav/platform/controller/ApiV1Controller.java`
- **行号**: ~140 (login 方法)
- **严重级别**: 🔴 CRITICAL
- **描述**: `/api/v1/auth/login` 端点接受任意用户名/密码，不进行任何凭据验证即生成有效 JWT Token。由于 API Gateway 将 `/api/**` 路由到此服务 (port 8080)，导致所有登录请求绕过后端真实认证 (port 8089 的 AuthController)。
- **影响**: 攻击者可通过任意用户名登录系统，获取管理员级别 JWT Token，完全绕过认证机制。
- **修复**: ✅ **已自动修复** — 替换为抛出 UnsupportedOperationException，保留原始代码为注释供参考。生产环境应删除此方法或实现真实的 AuthenticationManager 验证。
- **下一步**: 确保 API Gateway 将 `/api/v1/auth/**` 路由到 `backend-spring:8089` 而非 `uav-platform:8080`。

### NOC-02: .env 文件含真实密钥已提交

- **文件**: `.env`
- **行号**: 10-18
- **严重级别**: 🔴 CRITICAL
- **描述**: 项目根目录 `.env` 文件包含真实 JWT 密钥、加密密钥和数据库密码。此文件可能已提交到版本控制或通过 Docker 构建上下文泄露。
- **发现的密钥**:
  - `JWT_SECRET_KEY=zcTsGp3sbyf33iObgWgqeML58tBM3mCI5iqWjicpTQI=`
  - `ENCRYPTION_KEY=TcavENLUvp3pXdaqHBpJb+fyVHNr+18VjKFpx9pfnnU=`
  - `DB_PASSWORD=uav_ploy_2026_secure`
  - `TEST_USERNAME=test_admin` / `TEST_PASSWORD=test_pass_123`
- **修复**: ⚠️ **需手动处理** — 
  1. 立即轮换所有密钥（生成新值: `openssl rand -base64 32`）
  2. 将 `.env` 添加到 `.gitignore`
  3. 如果已提交到 Git，执行 `git filter-branch` 清除历史
  4. 从 Docker 镜像层中清除（重建镜像）
  5. ✅ 已在文件顶部添加安全警告注释

### NOC-03: CORS 配置允许任意来源 + 凭据传递

- **文件**: `uav-platform-service/src/main/java/com/uav/config/WebSecurityConfig.java`
- **行号**: ~47
- **严重级别**: 🔴 CRITICAL
- **描述**: CORS 配置使用 `allowedOriginPattern("*")` 与 `setAllowCredentials(true)` 组合。当凭据模式下允许任意来源时，虽然浏览器会拒绝此响应，但 Spring Security 本身不阻止请求，可能被非浏览器客户端利用进行 CSRF 攻击。
- **修复**: ✅ **已自动修复** — 改为从 `CORS_ORIGINS` 环境变量读取来源白名单，默认值限制为 `localhost:3000,localhost:8080`。
- **下一步**: 在生产环境设置 `CORS_ORIGINS=https://yourdomain.com` 环境变量。

### NOC-04: Docker Compose 硬编码密钥（已部分修复）

- **文件**: `docker-compose.yml`
- **行号**: 多处 (wrf-processor, data-assimilation, meteor-forecast, path-planning, uav-platform, uav-weather-collector)
- **严重级别**: 🔴 CRITICAL
- **描述**: 所有微服务的环境变量中原本硬编码了默认密钥。虽然已部分改为环境变量引用，但 `SECURITY_USER_PASSWORD` 仍有默认值 `admin123`。
- **修复**: ✅ **已自动修复** — `SECURITY_USER_PASSWORD:-admin123` → `SECURITY_USER_PASSWORD:-changeme`
- **下一步**: 在生产环境通过外部 secrets provider 注入真实密钥，不要依赖 Compose 文件中的默认值。

---

## 🟠 HIGH (尽快修复)

### NOC-05: application.yml 硬编码数据库密码默认值

- **文件**: `uav-platform-service/src/main/resources/application.yml`
- **行号**: 11
- **严重级别**: 🟠 HIGH
- **描述**: 原配置文件有 `password: ${DB_PASSWORD:uav_ploy_2026_secure}` 硬编码默认密码。虽有环境变量覆盖能力，但默认值即是已知密码。
- **修复**: ✅ **已自动修复** — 默认值已改为 `***` 占位符。
- **状态**: 已部分修复（默认值脱敏），但仍建议在生产环境移除此默认值。

### NOC-06: 数据库连接未启用 SSL

- **文件**: `uav-platform-service/src/main/resources/application.yml`
- **行号**: 9
- **严重级别**: 🟠 HIGH
- **描述**: 数据库连接字符串使用 `useSSL=false`，所有数据库流量为明文传输，包括认证凭据和数据。
- **修复**: ✅ **已自动修复** — `useSSL=false` → `useSSL=true`
- **下一步**: 
  1. 确保 MySQL 配置了 SSL 证书
  2. 如为 Docker 内网通信，可评估风险后使用此配置，但需在安全评估中标记

### NOC-07: FengWu 服务无认证保护

- **文件**: `fengwu-service/app.py`
- **行号**: 48-51, 所有 API 端点
- **严重级别**: 🟠 HIGH
- **描述**: FengWu 气象大模型推理服务所有端点均无认证保护。CORS 配置为 `allow_origins=["*"]`。该服务运行计算密集型推理，无认证可导致：
  - 未授权使用计算资源（DoS 风险）
  - 气象数据泄露
  - 模型接口被滥用
- **修复**: ⚠️ **需手动处理** — 
  1. 添加 API Key 或 JWT 认证中间件
  2. 限制 CORS 来源为已知服务
  3. 考虑在 K8s NetworkPolicy 中限制仅内部服务可访问
- **参考**: `edge-cloud-coordinator/api.py` 有较好的 CORS 配置模式可参考。

---

## 🟡 MEDIUM (建议修复)

### NOC-08: uav-platform-service 无输入校验

- **文件**: `uav-platform-service/src/main/java/com/uav/platform/controller/ApiV1Controller.java`
- **行号**: 多处 (所有 @PostMapping 端点)
- **严重级别**: 🟡 MEDIUM
- **描述**: 所有 POST 端点使用 `@RequestBody Map<String, Object>` 但缺少 `@Valid` 注解，无输入校验。虽然此控制器主要为 Stub 实现，但若保留必须添加校验。
- **修复**: ⚠️ **需手动处理** — 替换 `Map<String, Object>` 为强类型 DTO 并添加 Bean Validation 注解 (`@NotBlank`, `@Size`, `@Pattern` 等)。
- **受影响的端点**: `/api/v1/drones`, `/api/v1/tasks`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/planning/*`, `/api/forecast/*`

### NOC-09: PlatformController 无输入校验

- **文件**: `uav-platform-service/src/main/java/com/uav/platform/controller/PlatformController.java`
- **行号**: 69 (plan), 160 (manageTask)
- **严重级别**: 🟡 MEDIUM
- **描述**: `plan()` 和 `manageTask()` 方法接受未验证的 `Map<String, Object>` 作为请求体，无类型安全检查或输入校验。
- **修复**: ⚠️ **需手动处理** — 创建强类型 Request DTO 并添加 `@Valid` 注解。

### NOC-10: DataSourceController 无输入校验

- **文件**: `uav-platform-service/src/main/java/com/uav/controller/DataSourceController.java`
- **行号**: 50, 58, 80
- **严重级别**: 🟡 MEDIUM
- **描述**: 多个 POST 端点使用 `@RequestBody Map<String, Object>` 无 `@Valid` 校验。
- **修复**: ⚠️ **需手动处理** — 同上，添加 DTO 类和校验。

### NOC-11: Actuator 端点暴露过宽

- **文件**: 多个 `application.yml` 文件
- **服务**: uav-platform, uav-weather-collector, data-assimilation-service, meteor-forecast-service, path-planning-service, wrf-processor-service
- **严重级别**: 🟡 MEDIUM
- **描述**: 多数服务 Actuator 配置为 `include: health,info,prometheus` 且部分使用 `show-details: when-authorized`。虽然已限制为基本端点，但仍建议生产环境通过 `management.server.port` 使用独立端口，并通过防火墙限制访问。
- **修复**: ⚠️ **需手动处理** — 
  1. 生产环境配置 `management.server.port: -1` 或使用独立端口
  2. 仅允许监控系统（Prometheus）访问 management 端口
  3. 确保 `/actuator/health` 不泄露内部组件详情

### NOC-12: JPA ddl-auto:update 在配置中

- **文件**: 多个 `application.yml`
- **服务**: wrf-processor, data-assimilation, meteor-forecast, path-planning, uav-platform
- **严重级别**: 🟡 MEDIUM
- **描述**: `spring.jpa.hibernate.ddl-auto: update` 允许 Hibernate 自动修改数据库 Schema，在生产环境可能导致数据丢失或 Schema 不一致。
- **修复**: ⚠️ **需手动处理** — 
  1. 生产环境改为 `validate` 或 `none`
  2. 使用 Flyway/Liquibase 管理数据库迁移
  3. 通过 Profile 区分: `dev=update`, `prod=validate`

### NOC-13: Edge-Cloud Coordinator 开发模式 CORS 警告

- **文件**: `edge-cloud-coordinator/api.py`
- **行号**: 40-55
- **严重级别**: 🟡 MEDIUM (已部分缓解)
- **描述**: 开发环境下 CORS 默认为 `["*"]`，虽然代码已有环境区分逻辑（生产环境强制要求 `CORS_ORIGINS`），但 logger.warning 可能被忽略。
- **修复**: ⚠️ **需手动处理** — 在 CI/CD 中添加检查，确保生产部署时 `ENVIRONMENT=production` 且 `CORS_ORIGINS` 已设置。

---

## 🔵 LOW (可选修复)

### NOC-14: 系统状态检查使用 TODO 硬编码返回值

- **文件**: `edge-cloud-coordinator/api.py`
- **行号**: 214
- **严重级别**: 🔵 LOW
- **描述**: `get_system_status()` 返回硬编码的 `cloud_connected=True, edge_connected=True`，标注为 TODO 但无计划实现。
- **修复**: ⚠️ **需手动处理** — 实现真实连接检测。

### NOC-15: FengWu 服务硬编码 health check 端口

- **文件**: `docker-compose.yml`
- **行号**: 405
- **严重级别**: 🔵 LOW
- **描述**: FengWu healthcheck 使用 `/health` 端点（非标准 Actuator），与其他服务的 `/actuator/health` 不一致。
- **修复**: ⚠️ **需手动处理** — 统一 health check 端点路径。

### NOC-16: 前端 Cesium Token 在生产环境尚未配置

- **文件**: `uav-path-planning-system/frontend-vue/.env.production`
- **行号**: 4
- **严重级别**: 🔵 LOW
- **描述**: 生产环境 `.env.production` 仍使用占位符 `VITE_CESIUM_ION_TOKEN=your_cesium_ion_token_here`，需配置真实 Token。
- **修复**: ⚠️ **需手动处理** — 获取生产级 Cesium Ion Access Token 并配置域名白名单。

### NOC-17: 本地测试账号存在于配置文件

- **文件**: `.env`
- **行号**: 39-40
- **严重级别**: 🔵 LOW
- **描述**: 配置文件包含 `TEST_USERNAME=test_admin` 和 `TEST_PASSWORD=test_pass_123`。虽标注"仅开发环境"，但存在于配置文件中即有被误用风险。
- **修复**: ⚠️ **需手动处理** — 移除测试账号或使用专门的测试 Profile 管理。

---

## ✅ 安全实践亮点

审计中也发现了以下良好的安全实践：

- **密码哈希**: 使用 BCryptPasswordEncoder 存储密码（`backend-spring/SecurityConfig.java`）
- **JWT 认证**: 有完整的 JWT 生成/验证/刷新/过期机制（`backend-spring/JwtUtil.java`）
- **RBAC 权限模型**: 有 `@RequiresPermission` 注解和 `PermissionAspect` 切面（`backend-spring/`）
- **安全审计日志**: 有 `SecurityAuditConfig` 记录认证成功/失败事件（`backend-spring/`）
- **JWT 密钥长度强制**: `JwtUtil.init()` 检查密钥最低 32 字节，否则自动生成（`backend-spring/JwtUtil.java`）
- **日志脱敏配置**: 有 `LogDesensitizationConfig` 类（`backend-spring/`）
- **条件化安全配置**: `CommonSecurityConfig` 通过 `ConditionalOnProperty` 门控加载
- **CSRF 保护**: 非 API 端点启用了 CSRF Token（`backend-spring/SecurityConfig.java`）
- **Python 安全密钥校验**: `security.py` 强制检查和运行时错误提示
- **容器安全**: 所有服务在 docker-compose 中配置了 `no-new-privileges:true`
- **K8s Secrets 使用**: K8s 部署配置使用 Secrets 而非 ConfigMap 存储敏感信息
- **Resilience4j 熔断保护**: 多个服务配置了熔断器、重试、舱壁隔离

---

## 📋 自动修复摘要

| 编号 | 文件 | 修复内容 |
|------|------|---------|
| NOC-01 | `ApiV1Controller.java` | 禁用无认证登录端点，替换为抛异常 |
| NOC-03 | `WebSecurityConfig.java` | CORS 从 `*` + credentials → 环境变量白名单 |
| NOC-04 | `docker-compose.yml` | SECURITY_USER_PASSWORD 默认值脱敏 |
| NOC-05 | `uav-platform-service/application.yml` | DB_PASSWORD 默认值脱敏 |
| NOC-06 | `uav-platform-service/application.yml` | `useSSL=false` → `useSSL=true` |
| NOC-02 | `.env` | 添加安全审计警告注释 |

---

## 🔧 手动修复优先级建议

| 优先级 | 编号 | 修复项 | 估算工时 |
|--------|------|--------|---------|
| P0 (立即) | NOC-02 | 轮换所有泄露的密钥 | 2h |
| P0 (立即) | NOC-01 | 修复 API Gateway 路由/实现真实登录 | 4h |
| P1 (本周) | NOC-07 | FengWu 服务添加认证 | 3h |
| P2 (本月) | NOC-08/09/10 | 添加输入校验 (DTO + @Valid) | 6h |
| P2 (本月) | NOC-06 | 配置数据库 SSL | 2h |
| P3 (下月) | NOC-11/12/13 | Actuator 加固 + DDL 策略 + CORS 检查 | 4h |
| P4 (后续) | NOC-14~17 | LOW 级别问题 | 2h |

---

> **审计人员**: OpenClaw Security Audit Subagent  
> **审计方法**: 静态代码分析 + 配置审查  
> **局限性**: 未涵盖运行时安全测试、依赖项 CVE 扫描、网络渗透测试  
> **建议**: 配合 `mvn dependency-check:check` (OWASP DC) 和 SAST 工具 (SonarQube) 进行深度扫描
