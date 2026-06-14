# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-06-14

### 二期迭代完成

#### Added - 算法引擎（102 个算法注册）

- **同化算法（13 个）**：3D-VAR、4D-VAR、5D-VAR、EnKF、贝叶斯同化器、自适应同化器、兼容同化器、增强贝叶斯、混合同化、自适应混合、多尺度混合、方差场优化器、自适应方差场
- **AI 模型（21 个）**：贝叶斯神经网络、CNN 校正器、DQN 模型、动态权重融合、EnKF、GP 路径规划器、GP 回归、GP 风险估计器、GPR 不确定性量化、LSTM 预测、LSTM 时序校正器、MPC、多 UAV 冲突消解器、物理约束、PPO 模型、概率 UNet、风险代价函数、稀疏 GP、UNet 气象、XGBoost 校正器、数据管线
- **规划算法（41 个）**：A*、蚁群算法、双向 A*、CBBA、CBS、冲突检测器、D* Lite、DE-RRT*、数字孪生、Dijkstra、DQN 规划器、DWA、遗传算法、贪心最佳优先、Informed RRT、跳跃点搜索、知识图谱、Lazy Theta*、LPA*、基于市场、MPC、多目标规划器、NSGA-II、轨道分解、粒子群、势场法、PPO 规划器、RRT、风险感知 A*、风险感知 RRT*、RRT*、模拟退火、空间分区、禁忌搜索、Theta*、三层规划器、4D 轨迹、不确定性感知规划器、可见性图、Voronoi 路网、VRPTW
- **边云协同（20 个）**：边缘聚合器、边缘 AI 推理、边缘异常检测、边缘带宽优化器、边缘缓存管理器、边缘数据同步、边缘容错、边缘模型更新、边缘资源监控、边缘调度器、边缘安全、边缘任务卸载、联邦学习、知识蒸馏、LLM 辅助决策、模型压缩、模型量化、自组织网络、拆分学习、V2X 通信
- **风险评估（4 个）**：空域风险、复合风险、地形风险、气象风险
- **观测决策（4 个）**：自适应观测、自适应观测设计、信息增益、传感器调度

#### Added - C++ Edge SDK（11 个组件）

- `IPathPlanner` / `AStarPlanner` / `RRTStarPlanner` -- 全局路径规划（A* / RRT*）
- `DWAPlanner` -- DWA 局部避障规划
- `PathSmoother` -- Bezier / Catmull-Rom / Douglas-Peucker 路径平滑
- `TrajectoryCorrector` -- PID 航迹跟踪修正
- `FlightController` -- MAVLink v2 飞控通信（PX4 / ArduPilot）
- `RiskAssessor` / `WeatherRiskAssessor` -- 气象风险定量评估
- `V2XClient` / `DSRCClient` -- DSRC / C-V2X 通信
- `FederatedClient` -- 联邦学习边缘端（FedAvg / FedProx）
- `ModelRuntime` / `ONNXRuntime` -- ONNX 模型推理
- `OfflineCache` -- 本地数据持久化与离线缓存
- `EdgeConfig` -- JSON 配置管理

#### Added - 5D-VAR 同化算法增强

- 五维变分同化（5D-VAR）支持时间维度的多时刻观测同化
- 自适应方差场优化器动态调整背景误差协方差

#### Added - GPR 不确定性量化

- 高斯过程回归（GPR）用于气象场不确定性量化
- 稀疏 GP 降维加速大规模数据推理

#### Added - 监控栈

- Prometheus 指标采集（Java Micrometer + Python 自定义指标）
- Grafana 可视化面板（JVM、Spring Boot、Algorithm Engine、Kafka）
- AlertManager 告警（服务不可用、高错误率、高延迟、Kafka 积压）

#### Added - RBAC 权限框架

- 5 种预置角色：SUPER_ADMIN、TENANT_ADMIN、OPERATOR、OBSERVER、ALGORITHM_ADMIN
- API Key HMAC-SHA256 签名认证
- 多租户 Schema 隔离

#### Added - 前端控制台

- Vue 3 + TypeScript + Vite 7 + Element Plus
- CesiumJS 地图可视化
- 多租户管理、算法注册、任务监控仪表盘

#### Added - 多环境 Docker Compose

- `docker-compose.yml` -- 基础配置（16 容器全栈编排）
- `docker-compose.override.yml` -- 开发环境（热重载、Debug 端口、Mock 模式）
- `docker-compose.staging.yml` -- 灰度环境（release 镜像、资源限制）
- `docker-compose.prod.yml` -- 生产环境（副本数、日志限制、OOM HeapDump）

#### Changed

- JDK 17 -> 21，Spring Boot 3.5 -> 4.0
- Nacos 2.3 -> 3.2
- Vite 5 -> 7
- 算法引擎从 20 个基础算法扩展到 102 个

## [1.0.0] - 2026-06-13

### MVP 一期

#### Added

- **7 个 Java 微服务**：api-gateway、platform-api、weather-api、assimilation-api、risk-api、observation-api、planning-api、utm-api
- **1 个 Python 算法引擎**：FastAPI + PyTorch + ONNX Runtime
- **Spring Cloud Gateway** -- API 路由与负载均衡
- **Apache Kafka** -- Java <-> Python 异步消息通信
- **Nacos 2.3** -- 服务注册与配置中心
- **MySQL 8.0 + Redis 7** -- 持久化与缓存
- **20 个基础算法**：A*、Dijkstra、RRT*、DWA、VRPTW、3D-VAR、4D-VAR、EnKF 等
- **Docker Compose 13 容器编排**：基础设施 + 业务服务一键启动
- **多租户独立 Schema 隔离**
- **Header 版本 API 策略**（/api/v1、/api/v2）
- **API Key HMAC-SHA256 签名认证**
- **E2E 测试脚本**（mock/real 双模式）
- **pre-commit 代码规范配置**
- **GitHub Actions CI/CD 流水线**
