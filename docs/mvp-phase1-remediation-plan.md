# UAV Platform V2 — MVP 一期整改方案

> **文档状态**: 已审批待执行
> **编制日期**: 2026-06-13
> **编制依据**: MVP 一期验收审计报告（mvp-phase1-audit.html）
> **执行原则**: 先解阻塞上线、再补完善项、最后治理风险

---

## 一、整体结论

当前 MVP 一期 **有条件通过验收**，必须先完成 3 项 P0 阻塞项才能启动内部灰度上线；P1/P2 项可灰度期间并行补齐；架构兼容性、服务发现等中长期风险同步落地缓解方案。

| 优先级 | 项数 | 预估工时 | 阶段 |
|--------|------|----------|------|
| P0 阻塞项 | 3 | **3 天** | 上线前必须完成 |
| P1 完善项 | 2 | **2.5 天** | 灰度期间并行 |
| P2 优化项 | 2 | **2 天** | 灰度/上线后补齐 |
| **合计** | **7** | **7.5 天** | — |

---

## 二、分级整改任务（按执行顺序）

---

### 2.1 P0 最高优先级（上线阻塞，3 个工作日内完成）

> 不完成则无法对外灰度 / 正式上线，全员优先投入

---

#### 任务 1：修复 API Gateway 启动问题

| 属性 | 内容 |
|------|------|
| **预估工时** | 0.5 天 |
| **问题根因** | Spring Boot 4.0 移除 `NettyWebServerFactoryCustomizer`，当前 Gateway 版本无兼容版本，main 分支不可用 |
| **执行人** | 后端架构 |
| **关联分支** | `gateway-legacy` |

**执行步骤：**

1. 切换至 `gateway-legacy` 分支（基于 Spring Boot 3.4.x）作为生产网关基线
2. 校验网关启动、端口监听、全局过滤器（鉴权/限流/版本/签名）全部正常加载
3. 核对路由配置：修正路由内旧服务名（`uav-control-service`/`utm-service`），统一为实际微服务名（`platform-api`/`utm-api`）
4. 验证网关转发、跨域、HMAC 校验、租户解析全流程

**完成标准（Checklist）：**

- [ ] `gateway-legacy` 分支 `mvn clean package` 编译通过
- [ ] `java -jar api-gateway-2.0.0.jar` 正常启动，端口 8080 监听
- [ ] 5 个 GlobalFilter 全部加载（日志/UTM回调/版本/应急/限流）
- [ ] 路由匹配测试：`/api/v1/weather/**` -> `weather-api:8082` 转发正常
- [ ] HMAC 签名验证通过（X-API-Key + X-Timestamp + X-Signature）
- [ ] 跨域 CORS 响应头正确

**长期策略：**

- 网关独立分支长期维护，不跟进 Boot 4.0
- 每周查看 [Spring Cloud Gateway Maven Central](https://repo.maven.apache.org/maven2/org/springframework/cloud/spring-cloud-gateway-server/) 版本更新
- 备选预案：评估 Gateway MVC 模式或替换为其他网关组件

---

#### 任务 2：修复 CI/CD + 前端 Docker 路径错误

| 属性 | 内容 |
|------|------|
| **预估工时** | 0.5 天 |
| **问题根因** | 流水线、Dockerfile 硬编码 `developer-console/`，实际目录为 `console/` |
| **执行人** | DevOps |
| **关联文件** | `.github/workflows/ci.yml`、`console/Dockerfile` |

**执行步骤：**

1. 修改 `.github/workflows/ci.yml` 前端构建工作目录：`console/developer-console/` -> `console/`
2. 修正 `console/Dockerfile` 中 COPY 目录路径：`developer-console/` -> `console/`
3. 手动触发全量 CI 流水线，验证：构建 -> 镜像打包 -> 部署全流程无报错

**完成标准（Checklist）：**

- [ ] `frontend-build` Job 执行成功
- [ ] `docker-build-frontend` Job 执行成功
- [ ] 前端镜像正常构建，nginx 服务启动
- [ ] 全量 CI 流水线 5 个 Job 全部绿色通过

---

#### 任务 3：Java ↔ Python 算法管线全链路联调

| 属性 | 内容 |
|------|------|
| **预估工时** | 2 天（核心主干） |
| **问题根因** | Kafka 通道已搭建，但端到端任务下发、算法执行、结果回调未验证；气象/风险模块仍纯 Mock |
| **执行人** | 后端 + 算法 |
| **关联模块** | assimilation-api、planning-api、observation-api、weather-api、risk-api、Python 算法引擎 |

**执行顺序 & 范围：**

**第一阶段（Day 1 上午）：基础通道验证**

1. 统一两端 Topic、消息体、序列化、ACK、状态同步规则
2. 启动 Kafka + Zookeeper + Python 算法引擎容器
3. 验证 Kafka 连通性：Java Producer -> Topic -> Python Consumer

**第二阶段（Day 1 下午）：assimilation-api 联调**

1. assimilation-api 提交 3D-VAR/4D-VAR/5D-VAR 任务
2. Python 引擎执行算法计算
3. 结果回传 -> Java Consumer -> DB 落库 -> Redis 状态同步
4. 验证状态机流转：PENDING -> RUNNING -> COMPLETED

**第三阶段（Day 2 上午）：planning-api + MPC 联调**

1. planning-api 提交路径规划任务（VRPTW/DE-RRT*/A*/DWA）
2. MPC 滚动重规划触发（位置更新 -> 重规划判断 -> 新路径生成）
3. 验证 MPC 三维度重规划逻辑：时间间隔 / 位置偏离阈值 / 风险变化

**第四阶段（Day 2 下午）：observation-api + weather/risk 改造**

1. observation-api 补全 Kafka Consumer，接收算法结果
2. weather-api 改造：接入真实算法逻辑、DB 持久化、补齐 WebSocket 实时流
3. risk-api 改造：接入 GPR 风险场计算、DB 持久化

**全局开关管控：**

- 生产环境 Profile 强制 `uav.mock.enabled=false`
- Mock 模式增加响应头 `X-Mock: true` 做标识，防止生产误用
- 异常场景验证：超时、算法报错、重复任务、网络抖动下状态流转正常

**完成标准（Checklist）：**

- [ ] 全链路闭环：Java 提交任务 -> Python 算法计算 -> 结果回传 -> Redis/DB 状态同步
- [ ] weather-api 脱离 Mock，输出真实计算数据
- [ ] risk-api 脱离 Mock，输出 GPR 风险场数据
- [ ] WebSocket 气象/风险实时流正常推送
- [ ] Mock 开关切换可逆，降级能力可用
- [ ] 异常场景：超时自动标记 FAILED，重复任务幂等拒绝，网络抖动后自动重试

---

### 2.2 P1 中优先级（灰度期间并行补齐，不阻塞上线）

---

#### 任务 4：基础监控体系搭建

| 属性 | 内容 |
|------|------|
| **预估工时** | 2 天 |
| **问题根因** | Prometheus/Grafana 仅容器定义，无抓取配置、面板、告警；无链路追踪、日志聚合 |
| **执行人** | DevOps + 后端 |
| **关联文件** | `docker-compose.yml`、各服务 `application.yml` |

**执行步骤：**

1. 基于服务 actuator 端点，配置 Prometheus 抓取规则（`prometheus.yml`）
2. 搭建基础 Grafana 面板：
   - 服务 QPS、接口耗时、错误率
   - JVM 内存/线程/GC
   - Kafka 队列堆积、消费延迟
3. 配置简易告警规则（服务宕机、接口错误率突增、队列阻塞）

**范围控制：**

- 本期仅落地 **指标监控**（Prometheus + Grafana）
- SkyWalking 链路追踪、ELK 日志聚合 **延后至 Phase 3 二期迭代**

**完成标准（Checklist）：**

- [ ] Prometheus 正常抓取所有服务 actuator `/actuator/prometheus` 端点
- [ ] Grafana 面板展示：服务 QPS、P99 延迟、错误率、JVM 指标
- [ ] 基础告警触发正常：服务宕机 1 分钟内告警、错误率 > 5% 告警

---

#### 任务 5：同步修正文档

| 属性 | 内容 |
|------|------|
| **预估工时** | 0.5 天 |
| **问题根因** | migration-tracker.md 严重滞后；architecture.md 服务列表过时 |
| **执行人** | 技术负责人 |
| **关联文件** | `docs/migration-tracker.md`、`docs/architecture.md` |

**执行步骤：**

1. 更新 `migration-tracker.md`：
   - 阶段一：骨架搭建 -> 全部完成
   - 阶段二：公共模块迁移 -> 全部完成
   - 阶段三：核心服务迁移 -> 全部完成
   - 阶段四：Python 服务迁移 -> 全部完成
   - 阶段五：集成与验收 -> 进行中（E2E 通过，待补齐监控/文档）
2. 更新 `architecture.md`：
   - 删除已合并的 `airworthiness-api`
   - 对齐当前 8 个微服务清单（gateway + 7 业务服务）

**完成标准（Checklist）：**

- [ ] `migration-tracker.md` 所有阶段状态与实际进度一致
- [ ] `architecture.md` 服务列表与代码完全一致
- [ ] 无 "待开始" 标记的已完成项

---

### 2.3 P2 低优先级（灰度 / 上线后陆续补齐）

---

#### 任务 6：完善版本日志 & SDK 文档

| 属性 | 内容 |
|------|------|
| **预估工时** | 1 天 |
| **问题根因** | CHANGELOG 仅记录到 2.0.0；Java SDK 无使用文档 |
| **执行人** | 技术写作 + 后端 |
| **关联文件** | `CHANGELOG.md`、`sdk/java-sdk/README.md` |

**执行步骤：**

1. 补全 `CHANGELOG.md`：
   - 逐条记录 10 项兼容性修复
   - 记录分支变更（main / gateway-legacy）
   - 记录 E2E 测试通过
2. 编写 Java SDK 使用文档：
   - 快速上手（Maven 依赖引入）
   - 鉴权示例（API Key + HMAC 签名）
   - 调用 Demo（Weather/Planning/UTM）
3. 补充 Javadoc 并配置自动发布（GitHub Actions）

**完成标准（Checklist）：**

- [ ] `CHANGELOG.md` 包含所有兼容性修复记录
- [ ] Java SDK README 含完整使用示例
- [ ] Javadoc 生成并发布到 GitHub Pages

---

#### 任务 7：编写部署运维手册

| 属性 | 内容 |
|------|------|
| **预估工时** | 1 天 |
| **问题根因** | 无生产部署指南、无运维手册 |
| **执行人** | DevOps + 技术负责人 |
| **输出文件** | `docs/deployment-guide.md` |

**内容清单：**

1. 环境准备（JDK 21 / Docker / Docker Compose / Maven / Node）
2. Docker Compose 部署步骤（开发环境 / 生产环境）
3. 环境变量说明（所有 `application.yml` 可配置项）
4. 服务启停命令（启动顺序、健康检查、优雅停机）
5. 常见故障排查（端口冲突、数据库连接失败、Kafka 连接超时）
6. Mock 开关说明（何时启用、如何切换、生产强制关闭）
7. 监控使用指南（Grafana 面板地址、告警规则说明）
8. 回滚方案（版本回退、数据库回滚、配置回滚）

**完成标准（Checklist）：**

- [ ] 手册覆盖从环境准备到生产部署的完整流程
- [ ] 含故障排查决策树（常见问题 -> 排查步骤 -> 解决方案）
- [ ] 新成员可按手册独立完成首次部署

---

## 三、遗留功能项分批处理

| 遗留项 | 处理方案 | 归属任务 | 完成时间 |
|--------|----------|----------|----------|
| observation-api 缺 Kafka Consumer | P0 联调阶段一并补齐 | 任务 3 | Day 2 下午 |
| 外部 UTM 对接未启用 | 灰度稳定后切换 `uav.utm.external.enabled=true` | 灰度期优化 | 灰度第 3~5 天 |
| 所有 Mock 模块 | 生产环境强制关闭 Mock，仅测试/开发环境保留 | 任务 3 | Day 2 下午 |

---

## 四、架构类中长期风险治理

### 风险 1：Gateway 无法兼容 Spring Boot 4.0（高风险）

| 维度 | 策略 |
|------|------|
| **短期** | 维持 `gateway-legacy`（Boot 3.4.x）独立分支，网关与业务服务分两个 Boot 版本维护 |
| **例行动作** | 每周查看 Spring Cloud Gateway 版本更新公告 |
| **备选预案** | 评估 Gateway MVC 模式，或后续替换为其他网关组件（如 Kong、Envoy） |

### 风险 2：无服务发现，服务间调用硬编码（中风险）

| 维度 | 策略 |
|------|------|
| **短期（MVP）** | 维持硬编码 + 统一环境变量管理，不改动现有逻辑 |
| **中期（Phase 3）** | 重新引入 Nacos 做服务注册发现 + 配置中心，统一地址与配置 |

### 风险 3：文档与代码不同步（中风险）

| 维度 | 策略 |
|------|------|
| **规范约束** | 新增 CI 轻量检查，核心架构/进度文档变更必须随代码提交同步 |
| **管理规则** | 迭代里程碑完成后，强制刷新进度追踪文档 |

### 风险 4：生产误用 Mock 数据（高风险）

| 维度 | 策略 |
|------|------|
| **防护层 1** | 生产环境 Spring Profile 硬编码禁用 Mock（`uav.mock.enabled=false`） |
| **防护层 2** | Mock 接口统一添加 `X-Mock: true` 响应头，监控平台做告警识别 |
| **防护层 3** | E2E 测试增加 Mock 模式检测用例，确保生产环境无 Mock 响应 |

---

## 五、整体排期与上线节奏

```
Day 1~3  [P0 攻坚期]
  ├── Day 1 上午: 任务 1 — Gateway 启动验证
  ├── Day 1 下午: 任务 2 — CI/CD 修复 + 任务 3 第一阶段（Kafka 通道）
  ├── Day 2 上午: 任务 3 第二阶段（assimilation-api 联调）
  ├── Day 2 下午: 任务 3 第三阶段（planning-api + MPC 联调）
  └── Day 3: 任务 3 第四阶段（observation + weather/risk 改造）

Day 4~5  [灰度启动期]
  ├── 启动内部灰度发布
  ├── 同步推进任务 4（监控）+ 任务 5（文档修正）
  └── E2E 全量回归测试

Day 6~10 [灰度验证期]
  ├── 验证线上稳定性
  ├── UTM 外部对接测试
  ├── 补齐任务 6（CHANGELOG/SDK 文档）+ 任务 7（运维手册）
  └── 灰度无重大问题 -> 启动正式验收

Day 11   [验收上线]
  ├── MVP 一期正式验收
  ├── 全量上线
  └── 团队切换至 Phase 3 二期迭代
```

---

## 六、验收上线最终准入清单

> **必须全部勾选完成后，方可启动灰度发布**

### P0 阻塞项

- [ ] **gateway-legacy 分支网关正常启动**，路由配置修正完成（uav-control-service -> platform-api 等）
- [ ] **CI/CD、前端 Docker 路径问题修复**，流水线全绿（5 个 Job 全部通过）
- [ ] **Java-Python 算法全链路 Kafka 联调通过**，所有核心算法脱离 Mock
- [ ] **生产环境 Mock 强制关闭**，Mock 标识 `X-Mock: true` 生效

### P1 完善项（灰度前优先完成）

- [ ] **基础 Prometheus + Grafana 监控可用**，面板正常展示指标
- [ ] **核心架构/进度文档同步更新**（migration-tracker.md、architecture.md）

### 回归验证

- [ ] **9 条 E2E 用例全部复测通过**
- [ ] **Mock 模式检测用例通过**（确认生产环境无 Mock 响应）

---

### 准入结论

> **以上 P0 项全部完成，即可启动灰度发布；剩余非阻塞项在灰度期间收尾。**

---

## 附录

### A. 参考文档

- [MVP 一期验收审计报告](../mvp-phase1-audit/mvp-phase1-audit.html)
- [VERSION_STATUS.md](../VERSION_STATUS.md)
- [docs/refactoring-plan-v2.md](refactoring-plan-v2.md)
- [docs/migration-tracker.md](migration-tracker.md)

### B. 关键分支

| 分支 | 用途 | Spring Boot | 状态 |
|------|------|-------------|------|
| `main` | 业务服务 | 4.0.0 | 正常运行 |
| `gateway-legacy` | API 网关 | 3.4.x | 待验证 |

### C. 关键配置项

| 配置项 | 文件 | 默认值 | 生产要求 |
|--------|------|--------|----------|
| `uav.mock.enabled` | `application.yml` | `true` | **必须 `false`** |
| `uav.utm.external.enabled` | `application.yml` | `false` | 灰度后 `true` |
| `spring.profiles.active` | 启动参数 | `default` | **必须 `prod`** |
