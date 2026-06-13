# UAV Platform V2 - 二期迭代计划

> 最后更新：2026-06-14
> 状态：**二期算法补齐已完成，102个算法注册**

---

## 一期成果总结

### 完成度：100%

一期灰度部署全部完成，13 个 Docker 容器全部健康运行，Kafka 全链路打通。

### 部署架构

| 层级 | 服务 | 端口 | 状态 |
|------|------|------|------|
| **基础设施** | MySQL 8.0 | 3306 | healthy |
| | Redis 7 | 6379 | healthy |
| | Kafka + Zookeeper | 9092 / 2181 | healthy |
| | Nacos 3.2.0 | 8950 | healthy |
| **API 网关** | api-gateway (Spring Boot 3.4.5 standalone) | 8258 | healthy |
| **Java 微服务** | platform-api | 8251 | healthy |
| | weather-api | 8252 | healthy |
| | assimilation-api | 8253 | healthy |
| | risk-api | 8254 | healthy |
| | observation-api | 8255 | healthy |
| | planning-api | 8256 | healthy |
| | utm-api | 8259 | healthy |
| **算法引擎** | algorithm-engine (Python/FastAPI) | 9095 | healthy |

### 一期关键验证结果

- **Kafka 全链路**：Python -> Kafka -> 3 个 Java Consumer 全部正确反序列化和处理
- **API 网关**：Spring Cloud Gateway 路由转发正常，限流过滤器生效
- **Nacos 注册中心**：v3.2.0 + MySQL 持久化，控制台可访问
- **算法引擎**：20 个算法注册，A* 路径规划端到端验证通过
- **HMAC 认证**：API Key 签名验证正常
- **Docker 编排**：健康检查 + 自动重启全部就绪

### 一期修复的问题（15+项）

- 端口冲突（platform-api / weather-api）
- 环境变量缺失（Kafka bootstrap servers）
- JSON 序列化（snake_case / camelCase 不匹配）
- 非标准浮点值（Infinity / NaN 导致 Java 反序列化失败）
- CORS 配置（allowedOrigins -> allowedOriginPatterns）
- Nacos 数据库初始化（schema 导入 + JWT token 长度）
- api-gateway Spring Boot 4.0 兼容性（改用 standalone Spring Boot 3.4.5 构建）

---

## 二期算法补齐成果（2026-06-14 完成）

### 总览：102个算法注册（HTML 93组件目标 100%覆盖）

| 类别 | HTML计划 | 当前注册 | 覆盖率 |
|------|---------|---------|--------|
| 同化算法 | 13 | 13 | 100% |
| AI模型 | 21 | 21 | 100% |
| 规划算法 | 28 | 41 | 100%（+13计划外） |
| 边云算法 | 20 | 20 | 100% |
| 边缘SDK | 11 | 11（C++） | 100% |
| 风险评估 | — | 4 | 计划外 |
| 观测决策 | — | 3 | 计划外 |
| **合计** | **93** | **102** | **109%** |

### 新增算法明细

#### 规划算法（+13个，对齐HTML计划）
CBS、NSGA-II、ConflictDetector、DQN、PPO、ThreeLayerPlanner、RiskAwareA*、RiskAwareRRT*、UncertaintyAwarePlanner、MultiObjectivePlanner、DigitalTwin、KnowledgeGraph、Trajectory4D

#### AI模型（+17个，对齐HTML计划）
CNNCorrector、ProbabilisticUNet、LSTMTemporalCorrector、XGBoostCorrector、DQNModel、PPOModel、GPRegressionModel、SparseGPModel、GPRiskEstimator、DynamicWeightFusion、PhysicsConstraint、ModelPredictiveController、GPRPathPlanner、RiskCostFunction、MultiUAVConflictResolver、EnsembleKalmanFilterModel、DataPipeline

#### 边云算法（+17个，对齐HTML计划）
EdgeAIInference、LLMAssistedDecision、SelfOrganizingNetwork、EdgeAggregator、ModelCompressor、SplitLearning、KnowledgeDistillation、EdgeScheduler、EdgeCacheManager、EdgeDataSync、EdgeModelUpdate、EdgeResourceMonitor、EdgeTaskOffload、EdgeSecurity、EdgeFaultTolerance、EdgeBandwidthOptimizer、EdgeAnomalyDetector

#### C++ Edge SDK（+11个组件，完整实现）
A*路径规划、DWA局部规划、风险评估、飞行控制器、路径平滑（Bezier/Catmull-Rom/Douglas-Peucker）、轨迹修正（PID）、离线缓存、V2X通信客户端、联邦学习客户端、模型推理运行时、配置管理

---

## 二期目标

### 1. GPR 不确定性量化（高斯过程回归）

- 实现基于高斯过程回归（Gaussian Process Regression）的不确定性量化模块
- 为气象场同化结果提供概率预测与置信区间
- 集成到 assimilation-api，支持 GPR 后处理模式
- 输出：`gpr_uncertainty_quantification` 算法（Python 端）

### 2. 联邦学习（边缘设备协同训练）

- 设计联邦学习框架，支持多边缘设备（UAV / 地面站）协同训练
- 实现模型参数聚合策略（FedAvg / FedProx）
- 在 algorithm-engine 中新增联邦学习调度器
- 支持断点续训与通信压缩

### 3. 模型量化部署（模型压缩与推理优化）

- 对现有 20 个算法模型进行量化评估（INT8 / FP16）
- 实现 ONNX Runtime 推理后端，替代部分纯 Python 推理
- 建立模型量化流水线：训练 -> 量化 -> 验证 -> 部署
- 目标：推理延迟降低 50%+，内存占用降低 40%+

### 4. 实时数据同化增强（5D-VAR 优化）

- 在现有 3D-VAR 基础上扩展为 5D-VAR（含时间维与多源观测）
- 优化背景误差协方差矩阵估计（Hybrid B / NMC 方法）
- 支持流依赖背景误差（Flow-dependent B）
- 增量分析与循环同化（Cycling）

### 5. 观测优化策略（自适应观测网络设计）

- 基于信息熵 / Fisher 信息矩阵的观测站位优化
- 自适应观测时间窗口与空间分辨率
- 与 observation-api 深度集成，支持动态观测计划生成
- 输出：`adaptive_observation_design` 算法

### 6. 前端控制台（Vue 3 + TypeScript）

- 基于 Vue 3 + Element Plus + TypeScript 构建管理控制台
- 功能模块：
  - 气象数据可视化（ECharts 风场 / 温度场渲染）
  - 同化任务管理与结果预览
  - 风险评估仪表盘
  - 飞行计划管理与航迹展示
  - 系统监控面板（集成 Grafana iframe）
- 已有 console/ 目录基础框架，需完善业务页面

### 7. 监控告警完善（Grafana Dashboard + Prometheus 告警）

- 完善 Prometheus 指标采集（各 Java 服务 + Python 算法引擎）
- 设计 Grafana Dashboard 模板：
  - 服务健康总览
  - Kafka 消息吞吐与延迟
  - 算法执行耗时分布
  - API 请求 QPS / 错误率
- 配置 AlertManager 告警规则（服务宕机 / 延迟阈值 / 错误率阈值）

### 8. 性能优化（连接池、缓存策略、异步处理）

- 数据库连接池优化（HikariCP 参数调优）
- Redis 缓存策略完善：
  - 气象数据多级缓存（L1 本地 + L2 Redis）
  - 缓存预热与失效策略
- Kafka 异步处理优化：
  - 批量消费与批量发送
  - 消费者线程池配置
- API 响应时间目标：P99 < 500ms

### 9. 安全增强（RBAC、API 限流、审计日志）

- RBAC 权限模型设计与实现
  - 角色：管理员 / 操作员 / 观察者 / 外部系统
  - 资源级权限控制
- API 限流增强（api-gateway 已实现基础限流，需扩展）
  - 全局限流 + 用户级限流 + 接口级限流
- 审计日志
  - 操作日志记录与查询
  - 关键操作（飞行计划审批 / 系统配置变更）留痕

### 10. CI/CD 流水线（GitHub Actions 自动构建部署）

- 完善 GitHub Actions 工作流：
  - PR 自动构建与单元测试
  - Docker 镜像自动构建与推送
  - 灰度环境自动部署
  - E2E 自动化测试（集成 grayscale-verify.py）
- 多环境管理：dev / staging / production
- Docker Compose 编排优化（健康检查 / 滚动更新）

---

## 里程碑

### M1（第 1-2 周）：GPR + 联邦学习算法实现

| 任务 | 负责模块 | 交付物 | 状态 |
|------|----------|--------|------|
| GPR 不确定性量化算法 | algorithm-engine | `gpr_uncertainty_quantification` 算法 | 待开始 |
| 联邦学习框架搭建 | algorithm-engine | 联邦学习调度器 + FedAvg 聚合 | 待开始 |
| assimilation-api GPR 集成 | assimilation-api | GPR 后处理 API 端点 | 待开始 |
| 单元测试 + 集成测试 | 全模块 | 测试覆盖率 >= 80% | 待开始 |

### M2（第 3-4 周）：前端控制台 + 监控完善

| 任务 | 负责模块 | 交付物 | 状态 |
|------|----------|--------|------|
| 气象数据可视化页面 | console | 风场 / 温度场 ECharts 组件 | 待开始 |
| 同化任务管理页面 | console | 任务列表 / 详情 / 结果预览 | 待开始 |
| 风险评估仪表盘 | console | 风险等级分布 / 历史趋势 | 待开始 |
| Grafana Dashboard 模板 | monitoring | 4 套 Dashboard JSON | 待开始 |
| Prometheus 告警规则 | monitoring | AlertManager 配置 | 待开始 |

### M3（第 5-6 周）：性能优化 + 安全增强

| 任务 | 负责模块 | 交付物 | 状态 |
|------|----------|--------|------|
| 连接池与缓存优化 | 全 Java 服务 | HikariCP / Redis 配置调优 | 待开始 |
| Kafka 批量处理优化 | common-kafka | 批量消费 / 发送配置 | 待开始 |
| RBAC 权限模型 | common-security | 权限框架 + 数据库表 | 待开始 |
| API 限流增强 | api-gateway | 多维度限流过滤器 | 待开始 |
| 审计日志 | platform-api | 操作日志模块 | 待开始 |
| 模型量化评估 | algorithm-engine | 量化报告 + ONNX Runtime 集成 | 待开始 |

### M4（第 7-8 周）：CI/CD + 全量发布

| 任务 | 负责模块 | 交付物 | 状态 |
|------|----------|--------|------|
| GitHub Actions 完善 | .github/workflows | CI/CD Pipeline | 待开始 |
| 5D-VAR 算法实现 | algorithm-engine | 5D-VAR 同化算法 | 待开始 |
| 观测优化策略 | algorithm-engine | 自适应观测设计算法 | 待开始 |
| 灰度环境全链路验证 | scripts | grayscale-verify.py 自动化 | 待开始 |
| 全量发布与文档 | 全模块 | 部署文档 / 运维手册更新 | 待开始 |

---

## 技术栈版本锁定

| 组件 | 版本 | 备注 |
|------|------|------|
| Java 业务服务 | Spring Boot 4.0.0 | 7 个微服务 |
| api-gateway | Spring Boot 3.4.5 (standalone) | 独立构建，绕过 Boot 4.0 兼容性问题 |
| Spring Cloud Gateway | 4.1.0 | 与 Boot 3.4.5 配套 |
| Python 算法引擎 | FastAPI + Python 3.12 | 20 个算法 |
| Nacos | 3.2.0 | MySQL 持久化，JWT 认证 |
| Kafka | Confluent 7.8.0 | 全链路消息（Java <-> Python） |
| MySQL | 8.0 | 7 个业务库 + nacos 库 |
| Redis | 7 | 缓存 + 限流 |
| Docker | Docker Compose | 13 个容器编排 |

---

## 风险与依赖

| 风险项 | 影响 | 缓解措施 | 状态 |
|--------|------|----------|------|
| 5D-VAR 算法复杂度高 | M4 延期 | 提前在 M1 启动预研 | 待评估 |
| 联邦学习通信开销 | 边缘设备性能瓶颈 | 通信压缩 + 异步聚合 | 待评估 |
| 前端人力不足 | M2 延期 | 优先核心页面，次要页面后续迭代 | 待评估 |
| api-gateway Boot 版本分裂 | 维护成本增加 | 等待 Spring Cloud Gateway 5.x 支持 Boot 4.0 | 已知 |
| Kafka 消息积压 | 全链路延迟 | 批量消费 + 动态分区扩展 | 待评估 |

---

## 成功标准

- [ ] GPR 不确定性量化：同化结果置信区间覆盖率 >= 90%
- [ ] 联邦学习：支持 >= 4 个边缘设备协同训练
- [ ] 模型量化：推理延迟降低 >= 50%
- [ ] 5D-VAR：同化精度（RMSE）较 3D-VAR 提升 >= 15%
- [ ] 前端控制台：核心页面可用，首屏加载 < 2s
- [ ] 监控告警：关键指标 100% 覆盖，告警响应 < 5min
- [ ] 性能优化：API P99 响应时间 < 500ms
- [ ] 安全增强：RBAC 覆盖所有 API，审计日志 0 丢失
- [ ] CI/CD：PR 合并后 <= 15min 完成构建部署
- [ ] 灰度验证：grayscale-verify.py 全部 PASS
