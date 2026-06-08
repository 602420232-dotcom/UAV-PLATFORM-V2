# UAV 气象驱动无人机 VRP 智能路径规划系统 —— 全局文档索引

> **索引版本**：v1.2  
> **索引日期**：2026-06-08  
> **收录文档总数**：209 份  
> **覆盖范围**：项目根目录下全部 `.md` 后缀 Markdown 文档，递归含所有子目录（已排除 `.pytest_cache` 等自动生成目录）  

---

## 使用说明

### 面向开发者

本索引按文档**功能分类**编排，可通过下方目录快速跳转到关注的技术领域。每份文档配有：

- **完整相对路径**：在 IDE 中可通过 `Ctrl+点击` 直接打开
- **内容摘要**（150–200 字）：快速判断文档是否与当前任务相关
- **结构分析**：展示文档的 H1~H3 标题层级，了解内容组织方式
- **目标受众**：明确适合的开发、运维、架构或入门人员

**快速检索技巧**：在 IDE 中按 `Ctrl+F` 搜索模块名（如 `wrf`、`nacos`、`docker`）或功能关键词（如 `部署`、`测试`、`接口`）可秒级定位目标文档。

### 面向运维人员

重点关注 **部署与运维文档**、**报告与归档** 两大分类。日常操作（日志查看、服务重启、健康检查）请查阅 [快速参考卡](./docs/QUICK_REFERENCE.md) 或 [完整构建指南 第六章](./docs/COMPLETE_BUILD_GUIDE.md#第六章运维排障--出了问题怎么办)。生产部署请查阅 [Docker 部署指南](./docs/DOCKER.md) 和 [部署与维护方案](./docs/deployment/DEPLOYMENT.md)。

### 面向零基础初学者

推荐阅读顺序：

1. **[完整构建指南](./docs/COMPLETE_BUILD_GUIDE.md)** —— 从零到上线的全流程教程
2. **[项目总览 README](./README.md)** —— 了解项目是什么
3. **[项目结构指南](./docs/PROJECT_STRUCTURE.md)** —— 搞清楚每个文件夹干什么
4. **[架构设计文档](./docs/architecture.md)** —— 理解系统怎么运转
5. **[快速参考卡](./docs/QUICK_REFERENCE.md)** —— 常用命令速查

---

## 目录

- [一、项目总览与入口文档](#一项目总览与入口文档)
- [二、架构与设计文档](#二架构与设计文档)
- [三、微服务模块文档](#三微服务模块文档)
- [四、部署与运维文档](#四部署与运维文档)
- [五、API 接口文档](#五api-接口文档)
- [六、开发指南与规范](#六开发指南与规范)
- [七、数据同化平台文档](#七数据同化平台文档)
- [八、测试与质量保障](#八测试与质量保障)
- [九、报告与归档](#九报告与归档)
- [十、SDK、移动端与前端文档](#十sdk移动端与前端文档)
- [十一、辅助目录文档](#十一辅助目录文档)

---

## 一、项目总览与入口文档

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [README.md](./README.md) | 面向城市低空物流、电力巡检、应急救援等场景的全栈无人机智能调度系统项目总览，集成WRF高精度气象预报、贝叶斯数据同化、多约束VRP路径规划、边云协同等核心技术，介绍系统架构、技术栈、快速开始、API文档、部署指南。 | **H1**-项目简介 / **H2**-核心特性·系统架构·技术栈·快速开始·安装指南·配置说明·使用指南·API文档·开发指南·部署指南·监控与运维·故障排除·贡献指南·许可证 | 开发者、系统架构师、运维人员 | 项目总入口，提供整体概览与快速入门引导 |
| [docs/README.md](./docs/README.md) | 文档中心导航页，按"快速入门""开发指南""部署运维""API参考""专题报告"五大场景分类索引全部文档资源，含按角色（开发者/运维/入门）的推荐阅读路径。 | **H1**-文档中心 / **H2**-快速入门·开发指南·部署运维·API参考·专题报告 | 所有用户 | 文档体系导航枢纽 |
| [docs/QUICK_REFERENCE.md](./docs/QUICK_REFERENCE.md) | 常用命令速查卡，涵盖Java服务构建运行、Python服务依赖安装测试、Docker容器管理、认证API端点等高频操作命令，适合打印或置顶备查。 | **H1**-快速参考卡 / **H2**-快速开始·常用命令·API端点 | 开发者、运维人员 | 日常操作命令速查 |
| [docs/COMPLETE_BUILD_GUIDE.md](./docs/COMPLETE_BUILD_GUIDE.md) | 面向零基础初学者的2057行完整构建指南，覆盖环境搭建、源码获取、模块开发（Java/SpringBoot/Maven/Vue/Flutter/Python）、联调测试、Docker容器化部署、运维排障六大章节，所有命令可复制粘贴执行。 | **H1**-零基础完整构建指南 / **H2**-第一章环境搭建·第二章源码获取·第三章模块开发·第四章联调测试·第五章容器部署·第六章运维排障·附录 | 零基础初学者 | 从零到上线的全流程教程 |

---

## 二、架构与设计文档

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [docs/architecture.md](./docs/architecture.md) | 微服务分层架构设计，定义9个服务模块（api-gateway/uav-platform-service/领域服务/backend-spring）的职责边界与端口分配，含backend-spring vs uav-platform-service职责区分对照表和3项架构决策记录（ADR-001~003）。 | **H1**-架构设计文档 / **H2**-模块边界定义·架构决策记录 | 架构师、技术负责人 | 系统架构权威说明 |
| [docs/PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md) | 完整项目目录树，详列Java后端服务（api-gateway/common-utils及各微服务）、算法模块（Python数据同化平台/路径规划）、前端（Vue3）、边缘计算SDK（C++/Python）及部署配置的完整文件清单。 | **H1**-项目结构指南 / **H2**-目录结构概览·Java后端服务详解·前端详解 | 开发者、新成员 | 项目目录导航与文件定位 |
| [docs/PORTS_CONFIGURATION.md](./docs/PORTS_CONFIGURATION.md) | 所有服务端口配置总表，含10个微服务端口（8080-8094）、API Gateway路由映射（5条规则）、前端开发与生产端口、端口分配原则，每条路径标注熔断器启用状态。 | **H1**-端口配置总表 / **H2**-后端服务端口·前端应用端口·API路由映射 | 开发者、DevOps | 端口分配与路由权威参考 |
| [docs/data_assimilation_platform.md](./docs/data_assimilation_platform.md) | 贝叶斯数据同化算法平台专项说明，介绍3D-VAR/4D-VAR/EnKF/Hybrid四种同化方法、多源数据融合流程、并行计算框架（Dask/MPI/Ray）及与WRF气象模型的集成方案。 | **H1**-数据同化平台 / **H2**-平台概述·同化方法·并行计算·集成方案 | 算法工程师、数据科学家 | 数据同化平台专项概述 |
| [docs/API_AGGREGATION_CONFIG.md](./docs/API_AGGREGATION_CONFIG.md) | API聚合优化配置，定义微服务间高频调用链路的聚合规则，减少客户端请求次数，提升用户体验与降低网络开销。 | **H1**-API聚合配置 / **H2**-聚合策略·配置示例·性能对比 | 后端开发者、架构师 | API性能优化配置参考 |
| [data-assimilation-platform/docs/architecture.md](./data-assimilation-platform/docs/architecture.md) | 贝叶斯数据同化平台五层模块化架构：API层（CLI/REST/Web）、工作流层（批处理/流水线/流式）、核心算法层、数据处理层（适配/质控/时序/评估）、基础设施层（并行/GPU加速/可视化/存储）。 | **H1**-系统架构 / **H2**-整体架构·模块职责 | 架构师、技术负责人 | 数据同化平台架构说明 |
| [data-assimilation-platform/docs/index.md](./data-assimilation-platform/docs/index.md) | 贝叶斯数据同化平台文档门户，提供架构说明、开发指南、API参考、教程、无人机集成五项核心文档导航及算法核心库、Docker部署、共享协议定义等快速链接。 | **H1**-贝叶斯数据同化平台文档 / **H2**-文档导航·平台概述·快速链接 | 所有用户 | 数据同化平台文档入口 |
| [data-assimilation-platform/docs/uav_integration.md](./data-assimilation-platform/docs/uav_integration.md) | 贝叶斯同化平台与无人机路径规划系统的三种集成方案：推荐REST API（通过Java WRF处理层调用）、高性能gRPC（Proto定义AssimilationService）、批处理CLI模式，注明各方案适用场景。 | **H1**-无人机路径规划系统集成 / **H2**-集成概述·集成架构·集成方式 | 系统集成工程师 | 跨平台集成接口设计文档 |

---

## 三、微服务模块文档

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [api-gateway/README.md](./api-gateway/README.md) | 基于Spring Cloud Gateway的统一API入口（端口8088），实现路由转发（5条规则）、负载均衡、限流（100请求/秒）、重试（3次）和Resilience4j熔断保护，集成Nacos服务发现。 | **H1**-API网关 / **H2**-概述·技术栈·服务信息·路由列表·默认过滤·熔断器监控·环境变量·构建与运行 | 后端开发者、DevOps | API网关微服务说明 |
| [common-utils/README.md](./common-utils/README.md) | 跨服务公共工具模块，提供JWT认证过滤器、CSRF保护、CORS配置、PythonExecutor执行器，以及Resilience4j熔断器/重试/限时器封装，保护下游气象预测、路径规划、数据同化三个关键服务。 | **H1**-公共工具模块 / **H2**-模块概述·模块结构·核心功能 | 后端开发者 | 公共工具库架构说明 |
| [uav-platform-service/README.md](./uav-platform-service/README.md) | 核心聚合服务（端口8080），整合用户管理、任务管理、无人机管理、数据源管理功能，编排WRF处理、贝叶斯同化、气象预测、路径规划四个下游服务的完整工作流，引入熔断器提升稳定性。 | **H1**-主平台服务 / **H2**-概述·技术栈·服务信息·功能模块·接口·环境变量 | 后端开发者 | 主平台微服务说明 |
| [wrf-processor-service/README.md](./wrf-processor-service/README.md) | WRF气象数据处理服务（端口8081），解析WRF模型输出的NetCDF4格式气象数据，提取温度、湿度、风速、气压等低空气象参数，Java调用Python脚本（wrf_processor.py）完成预处理、后处理与可视化。 | **H1**-WRF气象数据处理服务 / **H2**-概述·技术栈·服务信息·接口·Python依赖·输入文件格式·环境变量·构建与运行·配置 | 后端开发者、气象数据处理工程师 | WRF数据处理微服务说明 |
| [meteor-forecast-service/README.md](./meteor-forecast-service/README.md) | 气象预测服务（端口8082），基于ConvLSTM+XGBoost+GPR多模型融合进行气象预测与订正，预置lstm_model.h5/xgb_model.json/gpr_model.pkl模型文件，输出高分辨率网格化预报数据。 | **H1**-气象预测服务 / **H2**-概述·技术栈·服务信息·接口·Python依赖·模型文件·环境变量·构建与运行·配置 | 后端开发者、AI/ML工程师 | AI气象预测微服务说明 |
| [path-planning-service/README.md](./path-planning-service/README.md) | 路径规划服务（端口8083），实现VRPTW任务调度（顶层）+DE-RRT*全局规划（中层）+DWA实时避障（底层）三层递进式架构，支持动态重规划（<5秒）和风场补偿，输出三维航点序列。 | **H1**-路径规划服务 / **H2**-概述·三层架构·技术栈·服务信息·接口·Python依赖·算法参数·环境变量·构建与运行·配置 | 后端开发者、算法工程师 | 路径规划核心微服务说明 |
| [data-assimilation-service/README.md](./data-assimilation-service/README.md) | 贝叶斯同化服务（端口8084），整合3D-VAR/4D-VAR/EnKF数据同化算法，通过REST API融合多源气象观测数据，45%失败率阈值触发熔断保护，产出融合分析场供路径规划调用。 | **H1**-贝叶斯同化服务 / **H2**-概述·技术栈·服务信息·接口·熔断器配置·Python依赖·环境变量·构建与运行·配置·依赖服务 | 后端开发者、数据科学家 | 数据同化微服务说明 |
| [uav-weather-collector/README.md](./uav-weather-collector/README.md) | 无人机气象信息收集服务（端口8086），对接无人机传感器、WRF预报、地面站等多源气象数据，提供实时采集、多源融合、气象告警评估和历史数据查询功能，为路径规划提供实时气象输入。 | **H1**-无人机气象信息收集模块 / **H2**-概述·技术栈·接口·配置·构建与运行 | 后端开发者 | 气象数据采集微服务说明 |
| [edge-cloud-coordinator/README.md](./edge-cloud-coordinator/README.md) | 边云协同计算框架，实现无人机与云端分布式智能计算，包含任务编排器、实时流处理（Kafka/Flink）、边缘AI推理（TensorRT/ONNX INT8）、联邦学习（FedAvg/FedProx）、WebSocket同步、mTLS安全通信等11个子模块。 | **H1**-边云协同计算框架 / **H2**-概述·模块说明·架构·数据流·快速开始 | 后端开发者、边缘计算工程师 | 边云协同框架说明 |
| [fengwu-service/README.md](./fengwu-service/README.md) | 风乌气象模型推理服务（端口8085），基于FastAPI构建，集成AI气象预测模型，提供实时气象预报API，包含安全中间件和模型推理引擎，支持Docker/K8s部署。 | **H1**-风乌气象模型服务 / **H2**-概述·技术栈·服务信息·API·部署·安全 | 后端开发者、气象工程师 | 风乌AI气象模型服务说明 |
| [tianzi-service/README.md](./tianzi-service/README.md) | 天资气象分析服务（端口8090），基于FastAPI构建，提供气象数据处理与分析API，集成安全中间件和推理引擎，支持多源气象数据融合，Docker/K8s部署就绪。 | **H1**-天资气象分析服务 / **H2**-概述·技术栈·服务信息·API·部署·安全 | 后端开发者、气象工程师 | 天资气象分析服务说明 |
| [fenglei-service/README.md](./fenglei-service/README.md) | 风雷区域模式数据服务（端口8091），基于FastAPI构建，提供区域气象数据处理API，对接CMA GRAPES模式数据，支持自动化数据更新与持久化，Docker/K8s部署配置完整。 | **H1**-风雷区域模式服务 / **H2**-概述·技术栈·服务信息·API·部署·数据源 | 后端开发者、气象工程师 | 风雷区域气象模式服务说明 |
| [uav-path-planning-system/README.md](./uav-path-planning-system/README.md) | 旧版基于WRF气象驱动的无人机VRP智能路径规划系统总览，含Vue3+Spring Boot 3.2+Python 3.8+技术栈说明、MySQL 8.0+Redis数据层、Docker+K8s部署架构概述。 | **H1**-UAV路径规划系统 / **H2**-项目概述 | 开发者 | 旧版系统总览 |
| [uav-path-planning-system/backend-spring/README.md](./uav-path-planning-system/backend-spring/README.md) | 旧版系统Spring Boot后端服务（端口8089），独立于微服务体系，提供Spring Security+JWT认证授权、MyBatis-Plus+JPA双ORM数据访问、gRPC通信能力，含用户RBAC四角色权限控制。 | **H1**-backend-spring后端服务 / **H2**-概述·技术栈·构建与运行 | 后端开发者 | 旧版后端服务说明 |
| [uav-path-planning-system/algorithm-core/README.md](./uav-path-planning-system/algorithm-core/README.md) | Python核心算法库，包含VRP求解器、RRT*/DWA路径规划算法、WPS气象预处理与插值算法，通过pip install -e安装使用，提供Python API和独立脚本两种调用方式。 | **H1**-核心算法库 / **H2**-概述·项目结构·快速开始 | 算法工程师、Python开发者 | 算法核心库入口说明 |
| [uav-path-planning-system/database/README.md](./uav-path-planning-system/database/README.md) | MySQL 8.0+数据库脚本集管理说明，含init.sql全量初始化、Flyway版本迁移、按表拆分的schema文件结构，核心业务表为users/tasks/drones/routes/weather_cache。 | **H1**-数据库 / **H2**-目录结构·快速开始·数据库Schema·数据库迁移 | DBA、后端开发者 | 数据库脚本管理说明 |
| [uav-path-planning-system/DEPLOYMENT.md](./uav-path-planning-system/DEPLOYMENT.md) | 旧版系统部署文档，推荐Docker Compose一键部署方案，涵盖后端（8080）、前端（3000）、MySQL（3306）、Redis（6379）全栈组件，以及本地手动部署的JDK/Python/Node.js环境配置步骤。 | **H1**-部署文档 / **H2**-系统架构·部署方式 | DevOps、运维人员 | 旧版系统部署手册 |
| [data-assimilation-platform/README.md](./data-assimilation-platform/README.md) | 数据同化平台项目总入口，整合贝叶斯同化算法库，通过REST API提供3D-VAR/4D-VAR/EnKF同化计算服务，技术栈含Spring Boot 3.2.0（Java 17）、Python 3.8+、MySQL 8.0+和Redis缓存。 | **H1**-数据同化平台 / **H2**-项目概述·项目结构·快速开始 | 开发者、系统架构师 | 数据同化平台总入口 |
| [data-assimilation-platform/service_spring/README.md](./data-assimilation-platform/service_spring/README.md) | Spring Boot微服务，提供数据同化REST API接口（端口8094），基于Java 17+Spring Boot 3.2.0+Maven构建，集成Spring Data JPA和Spring Security，支持多环境配置切换。 | **H1**-Data Assimilation Service Spring Boot / **H2**-服务概述·项目结构·快速开始·配置 | Java后端开发者 | 同化平台Spring服务说明 |
| [data-assimilation-platform/service_python/README.md](./data-assimilation-platform/service_python/README.md) | Python微服务，提供数据同化算法独立API接口，基于Flask/FastAPI+NumPy+SciPy，服务端口5000，暴露/assimilate、/variance、/health三个端点，轻量级独立部署。 | **H1**-Data Assimilation Python Service / **H2**-服务概述·项目结构·快速开始·API接口·测试 | Python开发者 | 同化平台Python服务说明 |
| [data-assimilation-platform/algorithm_core/README.md](./data-assimilation-platform/algorithm_core/README.md) | 贝叶斯数据同化核心算法库，实现3D-VAR/4D-VAR/EnKF及混合同化算法，支持Dask/MPI/Ray并行计算、CUDA/JAX GPU加速、多源卫星雷达数据融合，提供CLI和Python API双重使用方式。 | **H1**-贝叶斯数据同化核心算法库 / **H2**-功能特点·安装·快速开始 | 算法工程师、数据科学家 | 算法核心库入口文档 |

---

## 四、部署与运维文档

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [docs/DOCKER.md](./docs/DOCKER.md) | Docker部署指南，含前置准备（Docker Desktop安装）、docker-compose up -d快速启动、服务启动顺序（基础设施→微服务→网关→前端）、健康检查验证命令及常见FAQ。 | **H1**-Docker部署指南 / **H2**-前置准备·快速启动·项目说明·常见问题 | 开发者、DevOps | Docker容器化部署主指南 |
| [docs/deployment/README.md](./docs/deployment/README.md) | 部署与运维文档目录，索引DEPLOYMENT.md（全方案部署）、DEPLOY_GUIDE.md（详细部署步骤）、DISASTER_RECOVERY_PLAN.md（灾难恢复）三份核心运维文档。 | **H1**-deployment / **H2**-目录说明·使用 | DevOps、运维人员 | 部署文档导航 |
| [docs/deployment/DEPLOYMENT.md](./docs/deployment/DEPLOYMENT.md) | 部署与维护方案，涵盖Docker Compose一键部署（含.env环境变量配置模板）和Kubernetes生产部署（Helm Chart/Ingress/HPA）两种完整方案，以及部署验证、日志查看、服务启停操作。 | **H1**-部署与维护方案 / **H2**-系统架构·部署方式 | DevOps、运维人员 | 综合部署方案 |
| [docs/deployment/DEPLOY_GUIDE.md](./docs/deployment/DEPLOY_GUIDE.md) | 详细部署指南，含环境要求表、Mermaid架构总览图、Docker Compose分步部署流程（基础设施→微服务→验证）、生产环境准备和Nginx反向代理配置。 | **H1**-详细部署指南 / **H2**-环境要求·架构总览·Docker Compose部署·Kubernetes部署 | DevOps、SRE | 分步操作级部署手册 |
| [docs/deployment/DISASTER_RECOVERY_PLAN.md](./docs/deployment/DISASTER_RECOVERY_PLAN.md) | 灾难恢复计划，定义RPO（恢复点目标）和RTO（恢复时间目标）指标，包含MySQL+Nacos自动备份策略、多级故障响应流程（Level 1-3）及数据恢复操作步骤。 | **H1**-灾难恢复计划 / **H2**-概述·备份策略·故障分级·恢复流程 | SRE、DBA | 业务连续性保障方案 |
| [deployments/README.md](./deployments/README.md) | K8s生产部署配置目录，包含各微服务Deployment、namespace、secrets、configmap、ingress入口配置，以及Prometheus监控配置和告警规则定义。 | **H1**-部署配置 / **H2**-目录说明·使用 | DevOps、运维人员 | 生产环境部署配置入口 |
| [deployments/kubernetes/README.md](./deployments/kubernetes/README.md) | K8s生产部署详细配置，含9个微服务Deployment/Service/HPA定义，7个PVC（133Gi总量），HPA自动扩缩容策略，Nginx Ingress入口及bash deploy.sh一键部署脚本。 | **H1**-kubernetes / **H2**-文件说明·持久卷·自动扩缩容·快速开始 | DevOps、SRE | K8s部署配置文档 |
| [deployments/monitoring/README.md](./deployments/monitoring/README.md) | 监控告警日志聚合系统，集成Prometheus+Grafana+Kibana+Jaeger+Alertmanager五大组件，采集Spring Boot（3个）+Python（2个）+MySQL+Redis+Nginx+cAdvisor指标，支持Slack/SMTP告警。 | **H1**-监控与日志指南 / **H2**-快速开始·Prometheus监控 | DevOps、SRE | 全栈监控运维指南 |
| [deployments/edge-device/README.md](./deployments/edge-device/README.md) | 边缘设备（无人机机载计算机）部署配置，基于python:3.11-slim非root运行，集成ONNX推理引擎+Kafka消息队列+FastAPI HTTP/WebSocket服务，资源限制256MB/1CPU。 | **H1**-edge-device / **H2**-文件说明·Docker镜像·Python依赖·资源限制·环境变量·快速开始 | 边缘计算工程师 | 边缘设备部署文档 |
| [deployments/streaming/README.md](./deployments/streaming/README.md) | 基于Kafka+Flink的实时流处理部署配置，含Zookeeper/Kafka Broker/Flink JobManager+TaskManager/Kafka UI五大组件，定义气象数据/路径规划/边缘数据三个核心Topic。 | **H1**-streaming / **H2**-文件说明·组件·资源限制·Kafka配置·快速开始·典型流处理场景 | 数据工程师、DevOps | 流处理栈部署文档 |
| [deployments/backup/README.md](./deployments/backup/README.md) | 自动化MySQL+Nacos备份方案，MySQL使用mysqldump全量备份（含存储过程+触发器+gzip压缩），Nacos通过API导出JSON配置，8个环境变量灵活配置，支持Cron和K8s CronJob。 | **H1**-backup / **H2**-文件说明·备份类型·MySQL备份详情·Nacos备份详情·配置·快速开始 | DBA、运维工程师 | 自动化备份方案文档 |
| [deployments/database/README.md](./deployments/database/README.md) | MySQL性能优化配置，为user/task/drone/path_planning等六类表创建20+个索引加速查询，调优innodb_buffer_pool_size（1GB）等11项InnoDB核心参数。 | **H1**-database / **H2**-文件说明·索引优化·数据库参数调优·使用方法 | DBA、后端开发者 | 数据库性能优化文档 |
| [deployments/argo/README.md](./deployments/argo/README.md) | ArgoCD GitOps配置实现声明式持续交付与金丝雀发布，双轨部署（主+金丝雀），Argo Rollout四阶段渐进（10%→30%→60%→100%，各暂停60s），自动同步+自愈策略。 | **H1**-ArgoCD / **H2**-文件说明·配置详情·快速开始 | DevOps、SRE | GitOps持续交付文档 |
| [deployments/service-mesh/README.md](./deployments/service-mesh/README.md) | Istio服务网格完整配置，实现uav-platform路径规划金丝雀路由（90/10分流）、严格mTLS双向认证、EnvoyFilter熔断器、DestinationRule弹性策略和Jaeger全链路追踪。 | **H1**-service-mesh / **H2**-文件说明·组件矩阵·快速开始 | 平台工程师、SRE | 服务网格配置文档 |
| [deployments/multi-region/README.md](./deployments/multi-region/README.md) | 多区域容灾部署管理器（Python），支持ACTIVE/STANDBY/FAILED/SYNCING四状态区域生命周期，自动健康检查与优先级故障切换，5秒间隔数据同步，DNS/GSLB→双Region容灾架构。 | **H1**-multi-region / **H2**-文件说明·核心功能·快速开始·容灾架构·同步策略 | SRE、架构师 | 多区域容灾部署文档 |
| [deployments/observability/README.md](./deployments/observability/README.md) | 可观测性统一K8s部署配置，整合Jaeger（OTLP/Zipkin全协议）、Prometheus（7个Spring微服务+边缘协调器指标采集）和Grafana（3数据源自动配置），含告警规则。 | **H1**-observability / **H2**-文件说明·组件·快速开始 | SRE、DevOps | 可观测性平台部署文档 |
| [deployments/monitoring/prometheus/README.md](./deployments/monitoring/prometheus/README.md) | Prometheus 监控指标采集配置，定义各微服务 scrape 目标、采集间隔及标签规则，用于服务健康监控与性能趋势分析。 | **H1**-Prometheus配置 / **H2**-采集目标·指标说明 | SRE、DevOps | 指标采集配置 |
| [deployments/monitoring/grafana/README.md](./deployments/monitoring/grafana/README.md) | Grafana 可视化仪表板配置，预置各微服务监控面板 JSON 模板及数据源（Prometheus）关联配置，实现服务状态一站式可视化。 | **H1**-Grafana配置 / **H2**-仪表板·数据源配置 | SRE、DevOps | 可视化仪表板配置 |
| [deployments/monitoring/elk/README.md](./deployments/monitoring/elk/README.md) | ELK（Elasticsearch+Logstash+Kibana）日志聚合系统配置，定义各微服务日志采集管道、索引模板及 Kibana 可视化视图，实现全链路日志集中查询与分析。 | **H1**-ELK日志系统 / **H2**-采集管道·索引配置·视图定义 | SRE、DevOps | 日志聚合系统配置 |
| [docs/MAVEN_FIX.md](./docs/MAVEN_FIX.md) | Maven依赖问题修复指南，涵盖"Missing artifact"报错的诊断流程、多模块项目结构说明、镜像源配置方法、本地缓存清理步骤及mvn clean install -U强制刷新命令。 | **H1**-Maven依赖问题修复指南 / **H2**-问题现象·问题原因·项目结构说明·解决方案 | 后端开发者 | Maven故障排查手册 |
| [docs/FEIGN_MIGRATION_GUIDE.md](./docs/FEIGN_MIGRATION_GUIDE.md) | OpenFeign迁移指南，说明微服务间HTTP调用从旧版Feign迁移至Spring Cloud OpenFeign的配置变更、注解调整及兼容性注意事项。 | **H1**-Feign迁移指南 / **H2**-迁移背景·配置变更·注解调整 | 后端开发者 | OpenFeign升级迁移参考 |
| [docs/UPGRADE_REPORT.md](./docs/UPGRADE_REPORT.md) | Spring Cloud与Alibaba依赖版本升级记录，详细说明各模块POM文件从旧版本号升级到Spring Cloud 2025.0.2+Alibaba 2025.0.0.0的变更明细。 | **H1**-升级报告 / **H2**-升级概览·版本对照·变更明细 | 后端开发者 | 依赖版本升级追溯 |
| [docs/TODO_CHECKLIST.md](./docs/TODO_CHECKLIST.md) | 项目待办事项清单，按模块和优先级记录未完成的功能开发、性能优化、文档补全及技术债务事项，作为迭代计划参考。 | **H1**-TODO清单 / **H2**-功能待办·优化待办·文档待办 | 项目管理者、开发者 | 项目任务跟踪清单 |
| [data-assimilation-platform/deployments/README.md](./data-assimilation-platform/deployments/README.md) | 数据同化平台专属部署配置，含Docker Compose编排文件及K8s资源定义，实现算法核心与Spring/Python服务的容器化部署和集群调度。 | **H1**-deployments / **H2**-目录结构·部署方式 | DevOps | 同化平台部署入口 |
| [data-assimilation-platform/scripts/README.md](./data-assimilation-platform/scripts/README.md) | 数据同化平台运维工具脚本集，包含开发/生产环境部署脚本（deploy_dev/prod.sh+rollback.sh）、测试执行脚本（run_tests/benchmark/coverage.sh）、数据库管理脚本（init/backup_db.sh）等9个运维工具。 | **H1**-Data Assimilation Scripts / **H2**-概述·脚本分类·使用方法·前置条件 | DevOps、运维工程师 | 同化平台运维脚本说明 |
| [scripts/SCRIPTIGNORE_REPORT.md](./scripts/SCRIPTIGNORE_REPORT.md) | ScriptIgnore配置实施报告，定义13个主要类别100+条排除规则，覆盖Python（venv/pycache）、Node.js（node_modules）、Java（target/.gradle）、文档、日志、密钥等编译产物过滤。 | **H1**-ScriptIgnore配置报告 / **H2**-概述·完成的工作·排除规则详解 | DevOps、开发者 | 脚本忽略规则配置说明 |
| [docs/EXAMPLE.md](./docs/EXAMPLE.md) | 项目配置与使用示例集，提供典型业务场景（用户认证、路径规划、气象数据查询）的完整代码示例和配置模板，供开发时参考。 | **H1**-示例文档 / **H2**-认证示例·规划示例·气象示例 | 开发者 | 典型场景代码参考 |

---

## 五、API 接口文档

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [docs/api/README.md](./docs/api/README.md) | API文档中心导航页，按微服务分类索引WRF处理、平台服务、路径规划、气象预测、数据同化、气象采集、边云协同、路径规划系统8大服务群的详细接口文档。 | **H1**-API文档中心 / **H2**-(微服务分类表格) | 全栈开发者 | API文档体系导航 |
| [docs/api/API_DOCUMENTATION.md](./docs/api/API_DOCUMENTATION.md) | 全局API接口规范文档，定义通用请求响应格式、JWT认证机制（Bearer Token）、错误码体系（200/400/401/403/404/500）、分页参数标准及各服务核心接口的完整请求响应示例。 | **H1**-API文档 / **H2**-通用规范·认证机制·错误码·接口列表 | 前端开发者、后端开发者、测试工程师 | 全局API规范标准 |
| [docs/api/uav-platform-service/README.md](./docs/api/uav-platform-service/README.md) | UAV平台服务API目录，索引认证（auth）、数据源管理（data-sources）、无人机管理（drone）、历史数据（history）、路径规划（path）、任务管理（task）、用户管理（user）七个功能域的完整接口文档。 | **H1**-uav-platform-service / (目录索引表格) | 全栈开发者 | 平台服务API导航 |
| [docs/api/uav-platform-service/auth.md](./docs/api/uav-platform-service/auth.md) | 认证接口文档，提供JWT登录获取令牌、新用户注册并自动登录、令牌续期刷新三个接口，支持Bearer Token认证，返回用户信息及角色权限。 | **H1**-认证接口 / **H2**-登录·注册·刷新令牌 | 前端开发者、后端开发者 | 认证API参考 |
| [docs/api/uav-platform-service/data-sources.md](./docs/api/uav-platform-service/data-sources.md) | 数据源管理接口文档，管理地面站、浮标、气象、卫星等多源数据的完整CRUD操作（10个接口），包含连接测试、类型枚举、实时数据获取和全局状态监控功能。 | **H1**-数据源管理接口 / **H2**-接口列表 | 后端开发者、系统管理员 | 数据源管理API参考 |
| [docs/api/uav-platform-service/drone.md](./docs/api/uav-platform-service/drone.md) | 无人机管理接口文档，提供无人机资产的完整生命周期管理（5个CRUD接口），包含注册、状态监控（可用/使用中/维护）、电池电量追踪及位置记录功能。 | **H1**-无人机管理接口 / **H2**-获取列表·获取详情·创建·更新·删除 | 前端开发者、后端开发者 | 无人机管理API参考 |
| [docs/api/uav-platform-service/history.md](./docs/api/uav-platform-service/history.md) | 历史数据接口文档，提供任务、路径、无人机状态和气象四类历史数据的分页查询接口，支持按日期范围、任务状态、无人机ID等维度筛选回溯。 | **H1**-历史数据接口 / **H2**-历史任务记录·历史路径记录·无人机历史状态·历史气象数据 | 前端开发者、数据分析师 | 历史数据查询API参考 |
| [docs/api/uav-platform-service/path.md](./docs/api/uav-platform-service/path.md) | 路径规划接口文档，提供三维飞行路径生成、详情查询、状态更新和任务级路径列表功能，支持航点时间窗口、飞行约束（最大速度/高度/最低电量）参数配置。 | **H1**-路径规划接口 / **H2**-生成路径规划·获取详情·更新路径·获取任务路径列表 | 前端开发者、后端开发者 | 路径规划API参考 |
| [docs/api/uav-platform-service/task.md](./docs/api/uav-platform-service/task.md) | 任务管理接口文档，飞行任务全生命周期管理（5个CRUD接口），包含任务创建/派发/状态跟踪（PENDING→IN_PROGRESS→COMPLETED/FAILED），支持航点排序和时效配置。 | **H1**-任务管理接口 / **H2**-获取列表·获取详情·创建·更新·删除 | 前端开发者、后端开发者 | 任务管理API参考 |
| [docs/api/uav-platform-service/user.md](./docs/api/uav-platform-service/user.md) | 用户管理接口文档，提供系统用户的完整CRUD管理（5个接口），包含角色分配（ADMIN/DISPATCHER/USER）、账号启用/禁用、信息更新，支持JWT权限校验和用户名唯一性。 | **H1**-用户管理接口 / **H2**-获取列表·获取详情·创建·更新·删除 | 后端开发者、系统管理员 | 用户管理API参考 |
| [docs/api/wrf-processor-service/README.md](./docs/api/wrf-processor-service/README.md) | WRF处理服务API目录，索引WRF文件解析、处理后气象数据获取、数据统计信息查询三个核心接口及依赖环境配置说明。 | **H1**-wrf-processor-service / (目录索引表格) | 后端开发者 | WRF服务API导航 |
| [docs/api/wrf-processor-service/wrf.md](./docs/api/wrf-processor-service/wrf.md) | WRF处理服务API文档，提供气象数据解析和处理功能，支持从WRF输出NetCDF4文件中提取低空气象参数，包含文件解析上传、处理后数据获取和统计信息查询。 | **H1**-WRF处理服务API / **H2**-接口列表 | 后端开发者、气象数据分析师 | WRF处理API参考 |
| [docs/api/meteor-forecast-service/README.md](./docs/api/meteor-forecast-service/README.md) | 气象预测服务API目录，索引气象预测执行、观测数据订正、可用模型列表查询三个核心接口，基于LSTM+XGBoost+GPR多模型融合架构。 | **H1**-meteor-forecast-service / (目录索引表格) | 后端开发者 | 气象预测API导航 |
| [docs/api/meteor-forecast-service/forecast.md](./docs/api/meteor-forecast-service/forecast.md) | 气象预测服务API文档，使用LSTM和XGBoost模型进行气象预测与数据订正，支持多种模型（lstm/xgboost/convlstm/gpr），提供预测执行、观测订正及可用模型枚举功能。 | **H1**-气象预测服务API / **H2**-接口列表 | AI/ML工程师、气象数据分析师 | 气象预测API参考 |
| [docs/api/path-planning-service/README.md](./docs/api/path-planning-service/README.md) | 路径规划服务API目录，索引VRPTW任务调度、A*全局规划、DWA实时避障和完整三层融合规划的接口文档，结合气象数据与地形约束生成三维飞行路径。 | **H1**-path-planning-service / (目录索引表格) | 算法工程师、后端开发者 | 路径规划API导航 |
| [docs/api/path-planning-service/path.md](./docs/api/path-planning-service/path.md) | 路径规划服务API文档，VRPTW实现多无人机任务分配与排序，A*做全局路径规划，DWA处理实时避障，完整三层融合提供端到端无人机路径规划方案。 | **H1**-路径规划服务API / **H2**-接口列表 | 算法工程师、后端开发者 | 路径规划算法API参考 |
| [docs/api/data-assimilation-service/README.md](./docs/api/data-assimilation-service/README.md) | 数据同化服务API目录，索引贝叶斯同化执行、方差场计算、批量同化三个核心接口，基于3D-VAR/4D-VAR/EnKF/Hybrid多方法融合。 | **H1**-data-assimilation-service / (目录索引表格) | 气象工程师、数据科学家 | 同化服务API导航 |
| [docs/api/data-assimilation-service/assimilation.md](./docs/api/data-assimilation-service/assimilation.md) | 贝叶斯同化服务API文档，基于贝叶斯方法融合背景场和多源观测数据，支持hybrid混合同化方法，输出分析场和不确定性估计，提供方差场计算和批量执行功能。 | **H1**-贝叶斯同化服务API / **H2**-接口列表 | 气象工程师、数据科学家 | 数据同化API参考 |
| [docs/api/uav-weather-collector/README.md](./docs/api/uav-weather-collector/README.md) | UAV气象采集服务API目录，索引无人机传感器数据采集、WRF模型数据采集、地面站数据采集、实时气象查询、历史气象查询、多源融合、告警评估等9个接口。 | **H1**-uav-weather-collector / (目录索引表格) | 后端开发者 | 气象采集API导航 |
| [docs/api/uav-weather-collector/weather.md](./docs/api/uav-weather-collector/weather.md) | 无人机气象信息收集服务API文档，对接多源气象数据（传感器/WRF/地面站/卫星/浮标），支持多源加权融合（传感器70%+WRF30%）及告警评估，涵盖采集、查询、告警全流程。 | **H1**-无人机气象信息收集服务API / **H2**-接口列表·数据源·告警阈值 | 后端开发者、气象数据处理工程师 | 气象采集API参考 |
| [docs/api/edge-cloud-coordinator/README.md](./docs/api/edge-cloud-coordinator/README.md) | 边云协调器API目录，系统核心调度组件，协调无人机机载边缘计算单元与云端服务器的任务分配、数据同步和资源调度，在带宽受限环境下实现高效计算卸载。 | **H1**-edge-cloud-coordinator / (目录索引表格) | 架构师、后端开发者 | 边云协同API导航 |
| [docs/api/edge-cloud-coordinator/coordinator.md](./docs/api/edge-cloud-coordinator/coordinator.md) | 边云协同核心API文档（HTTP:8000/WS:8765），覆盖任务提交/查询/批量/取消、云端模型同步与边缘数据上传、FedAvg联邦学习训练聚合、熔断器状态监控与控制、WebSocket四类实时消息同步。 | **H1**-Edge-Cloud Coordinator API / **H2**-基础信息·健康检查·任务管理·边云协同·联邦学习·熔断器API·WebSocket·错误响应 | 后端开发者、AI/ML工程师 | 边云协同API参考 |
| [docs/api/uav-path-planning-system/README.md](./docs/api/uav-path-planning-system/README.md) | UAV路径规划系统API目录，涵盖独立Spring Boot后端（端口8089）的认证授权、用户管理、路径优化等接口及系统整体架构、API网关配置和断路器策略说明。 | **H1**-uav-path-planning-system / (目录索引表格) | 架构师、后端开发者 | 路径规划系统API导航 |
| [docs/api/uav-path-planning-system/backend-spring.md](./docs/api/uav-path-planning-system/backend-spring.md) | 路径规划系统Spring微服务后端API总览（Base URL:8089），集成JWT认证（登录/注册/刷新/登出）、用户CRUD管理、路径优化任务提交与状态查询、Actuator健康检查和断路器监控端点。 | **H1**-Backend Spring API / **H2**-基础信息·认证接口·用户管理·路径规划·健康检查·熔断器端点 | 后端开发者、DevOps | 独立后端API参考 |
| [data-assimilation-platform/docs/api.md](./data-assimilation-platform/docs/api.md) | 算法核心REST API接口参考文档，基于FastAPI（默认端口8000），提供POST /assimilate执行数据同化计算、POST /quality-control数据质量控制、POST /risk-assessment风险评估等接口。 | **H1**-API参考 / **H2**-REST API | 后端开发者、集成工程师 | 同化算法API参考 |

---

## 六、开发指南与规范

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [docs/guides/README.md](./docs/guides/README.md) | 开发指南专题目录，索引熔断器使用指南、熔断器使用示例、异常HTTP状态码规范、生产环境密钥安全指南、问题排查指南五项专题文档。 | **H1**-guides / (目录索引表格) | 开发者 | 开发指南导航 |
| [docs/guides/CIRCUIT_BREAKER_GUIDE.md](./docs/guides/CIRCUIT_BREAKER_GUIDE.md) | Resilience4j熔断器配置与使用指南，详解熔断器三种状态（CLOSED/OPEN/HALF_OPEN）及转换条件，配置参数（滑动窗口大小、失败率阈值、等待时间）的含义与调整方法。 | **H1**-熔断器使用指南 / **H2**-熔断器原理·配置参数·状态转换·使用方式 | 后端开发者 | 熔断器配置权威指南 |
| [docs/guides/CIRCUIT_BREAKER_USAGE_EXAMPLES.md](./docs/guides/CIRCUIT_BREAKER_USAGE_EXAMPLES.md) | 熔断器实战代码示例，覆盖三个关键服务（meteor-forecast/path-planning/data-assimilation）的完整熔断器配置代码，含application.yml配置注解和Java调用示例。 | **H1**-熔断器使用示例 / **H2**-气象预测服务熔断·路径规划服务熔断·数据同化服务熔断 | 后端开发者 | 熔断器代码参考实现 |
| [docs/guides/EXCEPTION_HTTP_STATUS_GUIDE.md](./docs/guides/EXCEPTION_HTTP_STATUS_GUIDE.md) | 异常与HTTP状态码映射规范，定义业务异常（BusinessException）与标准HTTP状态码（400/401/403/404/409/500）的对应关系，含全局异常处理器（GlobalExceptionHandler）实现示例。 | **H1**-异常HTTP状态码指南 / **H2**-异常映射表·异常处理实现·响应格式 | 后端开发者、前端开发者 | 异常处理规范 |
| [docs/guides/PRODUCTION_SECRETS_GUIDE.md](./docs/guides/PRODUCTION_SECRETS_GUIDE.md) | 生产环境密钥安全配置指南，规定JWT签名密钥（≥32字节随机字符串）、数据库密码、加密密钥等敏感信息的管理规范，含.env文件安全实践和密钥轮换策略。 | **H1**-生产环境密钥指南 / **H2**-密钥类型·管理规范·轮换策略 | 后端开发者、DevOps | 安全配置规范 |
| [docs/guides/TROUBLESHOOTING.md](./docs/guides/TROUBLESHOOTING.md) | 常见问题排查指南，按现象→原因→解决方案三步法覆盖端口冲突、数据库连接失败、Maven依赖异常、Nacos注册失败、Redis连接异常、网关路由404等高频故障场景。 | **H1**-问题排查指南 / **H2**-端口冲突·数据库连接·Maven依赖·Nacos注册·Redis连接·网关路由 | 开发者、运维人员 | 故障排查参考 |
| [data-assimilation-platform/docs/development.md](./data-assimilation-platform/docs/development.md) | 数据同化平台开发环境搭建与编码规范指南，涵盖Python 3.8+虚拟环境配置、算法核心依赖安装（含api/parallel/gpu可选依赖）、项目模块结构说明及Black/isort/mypy/flake8代码规范工具链。 | **H1**-开发指南 / **H2**-环境搭建·项目结构·编码规范 | 开发者 | 同化平台开发规范 |
| [data-assimilation-platform/docs/tutorials.md](./data-assimilation-platform/docs/tutorials.md) | 贝叶斯数据同化从入门到高级完整教程，涵盖安装与配置、BayesianAssimilator初始化与3D-VAR同化、plot_comparison结果可视化、EnKF集合卡尔曼滤波配置及Dask/MPI并行计算学习路径。 | **H1**-教程 / **H2**-入门教程·进阶教程 | 算法使用者、数据分析师 | 同化平台使用教程 |
| [data-assimilation-platform/.github/PULL_REQUEST_TEMPLATE.md](./data-assimilation-platform/.github/PULL_REQUEST_TEMPLATE.md) | GitHub Pull Request标准化模板，定义8种PR类型（Feature/BugFix/Performance/Refactor/Documentation/Tests/Dependencies/Security），含测试、文档、安全、部署变更全套检查清单。 | **H1**-Pull Request Template / **H2**-Type·Description·Changes·Testing·Documentation·Security Checklist·Deployment Changes | 所有贡献者 | PR提交规范模板 |
| [data-assimilation-platform/algorithm_core/docs/CHANGELOG.md](./data-assimilation-platform/algorithm_core/docs/CHANGELOG.md) | 算法核心库版本变更日志，遵循Keep a Changelog格式和语义化版本规范，v1.0.0记录核心同化算法四种、并行计算框架四种后端、三大数据适配器、质量控制/风险评估/可视化/API/GPU加速等全模块新增。 | **H1**-Changelog / **H2**-[1.0.0]·[0.1.0] | 开发者、项目维护者 | 算法库版本变更记录 |

---

## 七、数据同化平台文档

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [data-assimilation-platform/docs/README.md](./data-assimilation-platform/docs/README.md) | 贝叶斯数据同化平台文档中心，列出index/architecture/development/api/tutorials/uav_integration六大核心文档，展示多算法同化/多源数据融合/并行计算/硬件加速/质量管控/可视化六大平台能力。 | **H1**-docs / **H2**-主要文件·快速导航·平台核心能力 | 所有用户 | 同化平台文档导航 |
| [data-assimilation-platform/algorithm_core/examples/README.md](./data-assimilation-platform/algorithm_core/examples/README.md) | 算法核心示例代码集合，涵盖basic_usage/advanced_usage/demos/real_world_case系列/parallel_demo/cuda_acceleration/gpu_acceleration等15个示例文件及4个Jupyter教程。 | **H1**-examples / **H2**-主要文件·子目录·Jupyter教程·运行示例·注意事项 | 算法学习者、新用户 | 示例代码索引导航 |
| [data-assimilation-platform/algorithm_core/examples/TESTING.md](./data-assimilation-platform/algorithm_core/examples/TESTING.md) | 数据适配器测试完整指南，介绍基本/CI/性能三种运行模式，生成JSON/HTML/JUnit XML三格式测试报告，设定处理速度≥100万点/秒等性能基线，集成GitHub Actions/Jenkins CI。 | **H1**-数据适配器测试指南 / **H2**-概述·运行测试·依赖项·测试报告·性能基线·CI/CD集成·通知系统 | 测试工程师、DevOps | 适配器测试与CI集成文档 |
| [data-assimilation-platform/algorithm_core/examples/结果分析.md](./data-assimilation-platform/algorithm_core/examples/%E7%BB%93%E6%9E%9C%E5%88%86%E6%9E%90.md) | 同化结果可视化详细分析，对比背景场（原始模型预报风场3.10-6.90m/s）与分析场（同化观测后修正风场0.00-6.90m/s），方差场量化不确定性分布（观测点0.50→远端2.25高斯扩散）。 | **H3**-背景场·分析场·方差场 | 数据分析师、算法研究人员 | 同化结果科学解读 |
| [data-assimilation-platform/algorithm_core/configs/README.md](./data-assimilation-platform/algorithm_core/configs/README.md) | 算法核心配置文件目录说明，定义各同化算法（3D-VAR/4D-VAR/EnKF/Hybrid）的运行时参数、模型路径及并行计算资源配置的配置文件组织结构。 | **H1**-configs / (目录说明) | 算法工程师 | 配置目录说明 |
| [data-assimilation-platform/algorithm_core/benchmarks/README.md](./data-assimilation-platform/algorithm_core/benchmarks/README.md) | 算法性能基准测试目录说明，定义同化算法在不同数据规模与并行框架下的性能测试方案、评价指标及对比基准。 | **H1**-benchmarks / (目录说明) | 算法性能测试工程师 | 基准测试目录说明 |
| [data-assimilation-platform/algorithm_core/scripts/README.md](./data-assimilation-platform/algorithm_core/scripts/README.md) | 算法核心辅助脚本目录说明，包含数据预处理、批量同化执行、结果导出等辅助工具脚本的使用方法。 | **H1**-scripts / (目录说明) | 算法工程师 | 辅助脚本说明 |
| [data-assimilation-platform/algorithm_core/docker/README.md](./data-assimilation-platform/algorithm_core/docker/README.md) | 算法核心Docker化部署配置说明，提供基于python:3.11-slim的最小化镜像构建方案及CPU/GPU两种运行模式的环境配置。 | **H1**-Docker部署 / **H2**-构建·运行 | 算法工程师、DevOps | 算法容器化说明 |
| [data-assimilation-platform/benchmarks/README.md](./data-assimilation-platform/benchmarks/README.md) | 平台级性能基准测试目录说明，定义全平台端到端同化流程的性能测试方案、吞吐量与延迟指标及多场景对比基准。 | **H1**-benchmarks / (目录说明) | 性能测试工程师 | 平台基准测试说明 |
| [data-assimilation-platform/shared/README.md](./data-assimilation-platform/shared/README.md) | 数据同化平台共享资源目录说明，包含Protocol Buffers定义、JSON Schema数据校验规则及跨语言（Java/Python/C++）接口契约文件。 | **H1**-shared / (目录说明) | 全栈开发者 | 共享资源说明 |
| [data-assimilation-platform/shared/protos/README.md](./data-assimilation-platform/shared/protos/README.md) | Protocol Buffers接口定义汇总，包含请求（request）、响应（response）、服务（service）、通用（common）四类Proto文件的版本化管理及编译说明。 | **H1**-protos / (目录说明) | 全栈开发者 | Proto定义说明 |
| [data-assimilation-platform/shared/schemas/README.md](./data-assimilation-platform/shared/schemas/README.md) | JSON Schema数据验证规则目录说明，定义数据同化请求、响应及配置数据的结构化校验规则。 | **H1**-schemas / (目录说明) | 开发者 | 数据校验规则说明 |
| [data-assimilation-platform/service_python/requirements/README.md](./data-assimilation-platform/service_python/requirements/README.md) | Python服务依赖管理目录说明，按基础依赖、算法依赖、测试依赖、GPU加速依赖分类管理requirements文件。 | **H1**-requirements / (目录说明) | Python开发者 | 依赖管理说明 |
| [data-assimilation-platform/algorithm_core/benchmarks/results/report.md](./data-assimilation-platform/algorithm_core/benchmarks/results/report.md) | 贝叶斯同化系统性能测试报告（Intel Xeon Gold 6342 24核+128GB+A100 GPU环境），覆盖3D-VAR/4D-VAR/EnKF/混合同化四种核心算法执行时间与内存使用，评估Block Parallel/Dask/MPI/Ray多类并行框架加速比与效率及GPU加速性能，所有指标均满足或超越基线标准。 | **H1**-性能测试报告 / **H2**-概述·测试环境·测试结果·性能基线·结论 / **H3**-硬件配置·软件配置·核心算法性能·并行计算性能·GPU加速性能 | 算法研发工程师、性能测试工程师 | 算法核心性能基准测试报告 |
| [data-assimilation-platform/benchmarks/results/report.md](./data-assimilation-platform/benchmarks/results/report.md) | 数据同化平台性能测试报告（Intel Xeon Gold 6248R+64GB+Tesla V100环境），聚焦3D-VAR与EnKF算法在不同网格规模（50³→200³）和集合数量（20/50/100）下的耗时与内存对比，提供1至8工作节点并行加速比测量结果，体现平台良好可扩展性。 | **H1**-性能测试报告 / **H2**-测试环境·测试结果 / **H3**-3D-VAR性能·EnKF性能·并行加速比 | 平台性能测试人员、算法优化工程师 | 平台级端到端性能测试报告 |
| [data-assimilation-platform/algorithm_core/examples/output/结果分析.md](./data-assimilation-platform/algorithm_core/examples/output/%E7%BB%93%E6%9E%9C%E5%88%86%E6%9E%90.md) | 以通俗语言解读三张气象风险分析图：图一展示最大风险/平均风险/预测风险随时间演变（少数高风险点存在但整体安全）；图二以九宫格热力图分层呈现基础气象条件（深绿色低风险）、综合风险及湍流/切变/降水等具体风险类型；图三分析不确定性分布与信噪比，确认数据质量优良。总体结论为风险极低、系统可靠。 | **H1**-三张气象风险分析图通俗解读 / **H2**-风险随时间变化趋势·风险热力图（九宫格）·不确定性分析·总结 | 气象决策者、飞行安全管理人员 | 示例输出分析图通俗解读 |

---

## 八、测试与质量保障

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [tests/README.md](./tests/README.md) | 项目测试体系总览，定义六大类测试套件：单元测试（unittest/pytest）、集成测试、E2E测试（pytest+requests）、性能测试（JMeter）、安全测试（JWT/mTLS/加密）、混沌工程测试，覆盖Python和Java全模块。 | **H1**-tests / **H2**-目录结构·测试类型·快速开始 | 测试工程师、QA、开发者 | 测试体系总览与导航 |
| [tests/TESTING_GUIDE.md](./tests/TESTING_GUIDE.md) | 测试规范指南，定义各模块覆盖率阈值（common-utils 90%/其他85%/平台服务80%），CI/CD自动执行mvn test+安全扫描+JaCoCo覆盖率检查+依赖漏洞扫描，要求AAA模式与Mockito规范。 | **H1**-测试合规检查脚本 / **H2**-测试脚本·单元测试·测试覆盖率要求·CI/CD集成·新增测试规范·测试文件清单 | 测试工程师、开发者 | 测试规范与质量标准 |
| [tests/performance/README.md](./tests/performance/README.md) | 基于Apache JMeter的性能测试套件，覆盖路径规划/数据同化/气象接口/认证/API网关五大压测场景，设定P95<200ms、P99<500ms、错误率<0.1%、QPS>100等6项性能阈值。 | **H1**-performance / **H2**-文件说明·测试覆盖·性能指标阈值·快速开始·Python性能基准 | 性能测试工程师、SRE | 性能测试配置说明 |
| [tests/e2e/README.md](./tests/e2e/README.md) | 基于pytest+requests的端到端测试套件，覆盖用户注册登录JWT认证、数据源CRUD管理、WRF气象数据获取、路径规划提交与历史、API网关+Nacos健康检查、重试机制+批量请求弹性验证等六大关键流程。 | **H1**-e2e / **H2**-文件说明·覆盖的关键业务流程·快速开始 | 测试工程师、QA | 端到端测试说明 |
| [data-assimilation-platform/algorithm_core/tests/README.md](./data-assimilation-platform/algorithm_core/tests/README.md) | 算法核心测试套件总览，定义单元测试（unit/）与集成测试（integration/）的双层测试架构，说明各同化算法的测试用例组织和执行方式。 | **H1**-tests / (目录说明) | 算法测试工程师 | 算法测试总览 |
| [data-assimilation-platform/algorithm_core/tests/unit/README.md](./data-assimilation-platform/algorithm_core/tests/unit/README.md) | 算法核心单元测试目录说明，定义各同化算法模块（core/components/models/adapters等）的独立单元测试用例的组织规范与命名约定。 | **H1**-unit / (目录说明) | 算法开发者 | 单元测试组织说明 |
| [data-assimilation-platform/algorithm_core/tests/integration/README.md](./data-assimilation-platform/algorithm_core/tests/integration/README.md) | 算法核心集成测试目录说明，定义跨模块、端到端同化流程的集成测试方案，验证算法链路完整性与数据流正确性。 | **H1**-integration / (目录说明) | 测试工程师 | 集成测试组织说明 |
| [uav-mobile-app/test/README.md](./uav-mobile-app/test/README.md) | Flutter移动应用单元测试目录，基于flutter_test框架覆盖三大测试组：6种数据模型的JSON序列化与属性计算、边缘端正常/危险天气风险评估、模型不可变copyWith更新方法验证。 | **H1**-test / **H2**-关键文件·测试覆盖 | Flutter开发者、测试工程师 | 移动端测试说明 |

---

## 九、报告与归档

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [docs/reports/README.md](./docs/reports/README.md) | 项目质量保障报告汇总目录，汇集综合审计报告（v2.1/终版/v3.0/v4.0）、质量评估、文档重组、修复实施、Maven/Java审计、优化完成、包重构、Spring Cloud升级共12份阶段性评估报告。 | **H1**-reports / (分类表格) | 项目管理者、质量工程师 | 报告目录导航 |
| [docs/reports/PROJECT_QUALITY_AUDIT_FINAL_REPORT_v4.0.md](./docs/reports/PROJECT_QUALITY_AUDIT_FINAL_REPORT_v4.0.md) | 项目全面质量审计v4.0终版报告，覆盖Java（9服务）+Python+Docker+K8s+前端+移动端全栈扫描，综合评分90/100（优秀），修复JWT强制校验/CORS收紧/命令注入等3项高危漏洞。 | **H1**-项目质量审计报告v4.0 / **H2**-执行摘要·质量评分·问题清单·已修复内容 | 项目管理者、技术负责人 | 质量审计终版报告 |
| [docs/reports/PROJECT_QUALITY_AUDIT_FINAL_REPORT_v3.0.md](./docs/reports/PROJECT_QUALITY_AUDIT_FINAL_REPORT_v3.0.md) | 项目质量审计v3.0报告，在v4.0之前的审计基线，记录各模块质量评分、问题分布及修复优先级排序的历史状态。 | **H1**-项目质量审计报告v3.0 / **H2**-执行摘要·问题清单·修复计划 | 项目管理者 | 质量审计历史记录 |
| [docs/reports/PROJECT_QUALITY_AUDIT_FINAL_REPORT.md](./docs/reports/PROJECT_QUALITY_AUDIT_FINAL_REPORT.md) | 项目质量审计初次终版报告，建立质量审计框架基线，记录首轮全面审计发现的问题分布和初始质量评分。 | **H1**-项目质量审计终版报告 / **H2**-审计概述·发现问题·修复建议 | 项目管理者 | 首轮审计基线报告 |
| [docs/reports/PROJECT_QUALITY_AUDIT_REPORT.md](./docs/reports/PROJECT_QUALITY_AUDIT_REPORT.md) | 项目质量审计初始报告，定义审计范围与标准方法，记录代码质量、安全漏洞、架构合规性三大维度的初始评估结果。 | **H1**-项目质量审计报告 / **H2**-审计范围·评估标准·初始发现 | 项目管理者 | 审计方法论定义 |
| [docs/reports/COMPREHENSIVE_AUDIT_REPORT_v2.1.md](./docs/reports/COMPREHENSIVE_AUDIT_REPORT_v2.1.md) | 全面审计报告v2.1，聚焦代码规范、测试覆盖、安全漏洞扫描的深度审计，记录审计工具链运行结果及各项指标得分。 | **H1**-全面审计报告v2.1 / **H2**-代码规范·测试覆盖·安全扫描 | 项目管理者 | 深度审计专题报告 |
| [docs/reports/COMPREHENSIVE_QUALITY_ASSESSMENT.md](./docs/reports/COMPREHENSIVE_QUALITY_ASSESSMENT.md) | 项目综合质量评估报告，从功能完整性、代码质量、性能效率、安全性、可维护性五维度进行量化评分与综合评价。 | **H1**-综合质量评估 / **H2**-功能完整性·代码质量·性能·安全性·可维护性 | 项目管理者、客户 | 多维度质量评估 |
| [docs/reports/DOCUMENTATION_REORGANIZATION_REPORT.md](./docs/reports/DOCUMENTATION_REORGANIZATION_REPORT.md) | 文档体系重组实施报告，记录docs/目录从分散状态重组成api/guides/deployment/reports/archive五级分类结构的实施过程、迁移清单和结构对照。 | **H1**-文档重组报告 / **H2**-重组方案·迁移清单·结构对照 | 项目维护者 | 文档结构重组记录 |
| [docs/reports/FIX_IMPLEMENTATION_REPORT.md](./docs/reports/FIX_IMPLEMENTATION_REPORT.md) | 缺陷修复实施报告，记录各审计报告中发现问题（代码缺陷、配置错误、安全漏洞）的具体修复方案、实施过程和验证结果。 | **H1**-修复实施报告 / **H2**-修复清单·实施方案·验证结果 | 项目管理者、开发者 | 缺陷修复追踪 |
| [docs/reports/MAVEN_JAVA_AUDIT_REPORT.md](./docs/reports/MAVEN_JAVA_AUDIT_REPORT.md) | Maven与Java专项审计报告，检查多模块POM依赖一致性、Java代码规范遵循度、弃用API使用情况和Spring Boot版本适配。 | **H1**-Maven/Java审计报告 / **H2**-依赖一致性·代码规范·弃用API·版本适配 | 后端开发者 | Java生态专项审计 |
| [docs/reports/OPTIMIZATION_COMPLETION_REPORT.md](./docs/reports/OPTIMIZATION_COMPLETION_REPORT.md) | 优化实施完成报告，记录性能优化（数据库索引优化、缓存策略调优、连接池配置）和安全加固（JWT、CORS、CSRF）等优化工作的完成状态与效果验证。 | **H1**-优化完成报告 / **H2**-性能优化·安全加固·验证结果 | 项目管理者、开发者 | 优化工作成果记录 |
| [docs/reports/PACKAGE_REFACTOR_REPORT.md](./docs/reports/PACKAGE_REFACTOR_REPORT.md) | 包结构重构报告，记录Java代码包从旧版结构重构为统一规范的命名空间和分层结构的实施方案、迁移对照及影响评估。 | **H1**-包重构报告 / **H2**-重构方案·迁移对照·影响评估 | 后端开发者 | 代码结构重构记录 |
| [docs/reports/SC_UPGRADE_20250511.md](./docs/reports/SC_UPGRADE_20250511.md) | Spring Cloud升级专题报告（2025-05-11），记录从旧版本升级至Spring Cloud 2025.0.2的技术路线、兼容性变更、POM修改清单和升级后验证结果。 | **H1**-Spring Cloud升级报告 / **H2**-升级路线·兼容性变更·POM修改·验证结果 | 后端开发者 | Spring Cloud升级专题记录 |
| [docs/OPTIMIZATION_COMPLETE_REPORT.md](./docs/OPTIMIZATION_COMPLETE_REPORT.md) | 全局优化完成报告，汇总性能优化（数据库、缓存、连接池）、安全加固（JWT强化、CORS收紧、CSRF防护）及代码质量提升工作的整体成果。 | **H1**-优化完成报告 / **H2**-优化概览·分类成果·效果数据 | 项目管理者 | 全栈优化综合报告 |
| [docs/archive/README.md](./docs/archive/README.md) | 项目历史报告存档目录，收录断路器实现（3份）、代码质量审计、依赖管理重构、文档化完成（2份）、安全性改进、测试覆盖率分析、UAV系统文档化等12份阶段性里程碑报告。 | **H1**-archive / (分类表格) | 项目管理者、审计人员 | 历史档案目录导航 |
| [docs/archive/CIRCUIT_BREAKER_IMPLEMENTATION_COMPLETE_REPORT.md](./docs/archive/CIRCUIT_BREAKER_IMPLEMENTATION_COMPLETE_REPORT.md) | 断路器实施完成报告，记录Resilience4j在所有微服务中的部署完成状态、配置参数统一标准及实施效果验证。 | **H1**-断路器实施完成报告 / **H2**-实施范围·配置标准·验证结果 | 项目管理者 | 断路器实施归档 |
| [docs/archive/CIRCUIT_BREAKER_IMPLEMENTATION_REPORT.md](./docs/archive/CIRCUIT_BREAKER_IMPLEMENTATION_REPORT.md) | 断路器实施中期报告，记录Resilience4j集成过程中各服务的实施进度、配置调优和遇到的问题处理。 | **H1**-断路器实施报告 / **H2**-实施进度·配置调优·问题处理 | 项目管理者 | 断路器实施过程记录 |
| [docs/archive/ADDITIONAL_CIRCUIT_BREAKER_IMPLEMENTATION_REPORT.md](./docs/archive/ADDITIONAL_CIRCUIT_BREAKER_IMPLEMENTATION_REPORT.md) | 断路器补充实施报告，记录在初始实施后追加配置的额外服务断路器保护、增强的监控端点和故障恢复策略。 | **H1**-断路器补充实施报告 / **H2**-追加配置·监控增强·恢复策略 | 项目管理者 | 断路器补充实施归档 |
| [docs/archive/CODE_QUALITY_REPORT.md](./docs/archive/CODE_QUALITY_REPORT.md) | 代码质量评审报告，基于静态代码分析工具（SonarQube/Checkstyle）的扫描结果，记录代码规范遵循度、复杂度指标和改进建议。 | **H1**-代码质量报告 / **H2**-扫描结果·规范遵循度·改进建议 | 开发者 | 代码质量评审记录 |
| [docs/archive/COMMON_DEPENDENCIES_ANALYSIS.md](./docs/archive/COMMON_DEPENDENCIES_ANALYSIS.md) | 公共依赖分析报告，对各微服务模块的依赖树进行交叉对比分析，识别重复依赖、版本不一致问题及精简建议，为common-dependencies BOM设计提供依据。 | **H1**-公共依赖分析 / **H2**-依赖树对比·重复分析·版本一致性·精简建议 | 后端开发者、架构师 | 依赖管理分析记录 |
| [docs/archive/DEPENDENCY_MANAGEMENT_REFACTORING_REPORT.md](./docs/archive/DEPENDENCY_MANAGEMENT_REFACTORING_REPORT.md) | 依赖管理重构报告，记录从各模块独立管理依赖迁移至common-dependencies统一BOM管理的实施过程、POM调整清单和效果验证。 | **H1**-依赖管理重构报告 / **H2**-重构方案·POM调整·效果验证 | 后端开发者 | 依赖管理重构记录 |
| [docs/archive/DOCUMENTATION_COMPLETE_REPORT.md](./docs/archive/DOCUMENTATION_COMPLETE_REPORT.md) | 文档补全完成报告，记录大规模文档补全工作的完成状态，含各目录README.md的补全清单、文档质量标准和覆盖率统计。 | **H1**-文档补全完成报告 / **H2**-补全清单·质量标准·覆盖率统计 | 项目维护者 | 文档补全工作记录 |
| [docs/archive/DOCUMENTATION_UPDATE_SUMMARY.md](./docs/archive/DOCUMENTATION_UPDATE_SUMMARY.md) | 文档更新摘要，汇总历次文档版本更新的改动要点，含新增文档类型、结构优化、内容修订和格式规范化工作。 | **H1**-文档更新摘要 / **H2**-更新要点·新增文档·结构优化·格式规范 | 项目维护者 | 文档更新历史记录 |
| [docs/archive/OPTIMIZATION_IMPLEMENTATION_REPORT.md](./docs/archive/OPTIMIZATION_IMPLEMENTATION_REPORT.md) | 优化实施过程报告，记录数据库索引优化、JVM参数调优、缓存策略调整等性能优化工作的分步实施细节、中间状态和阶段性效果。 | **H1**-优化实施报告 / **H2**-数据库优化·JVM调优·缓存调整·阶段性效果 | 开发者 | 优化实施过程归档 |
| [docs/archive/SECURITY_IMPROVEMENTS.md](./docs/archive/SECURITY_IMPROVEMENTS.md) | 安全性改进实施报告，记录JWT密钥强化、CORS策略收紧、CSRF防护添加、密码加密升级、依赖漏洞修复等安全加固工作的实施细节。 | **H1**-安全性改进 / **H2**-JWT强化·CORS策略·CSRF防护·密码加密·依赖修复 | 后端开发者、安全工程师 | 安全加固实施记录 |
| [docs/archive/TEST_COVERAGE_REPORT.md](./docs/archive/TEST_COVERAGE_REPORT.md) | 测试覆盖率分析报告，记录各服务模块的JaCoCo覆盖率数据（行/分支/方法），含未覆盖热点区域分析和覆盖率提升建议。 | **H1**-测试覆盖率报告 / **H2**-覆盖率数据·未覆盖分析·提升建议 | 测试工程师 | 测试覆盖率历史记录 |
| [docs/archive/UAV_PATH_PLANNING_SYSTEM_DOCUMENTATION_REPORT.md](./docs/archive/UAV_PATH_PLANNING_SYSTEM_DOCUMENTATION_REPORT.md) | UAV路径规划系统文档化专项报告，记录旧版uav-path-planning-system模块的文档结构梳理、补充和规范化过程。 | **H1**-UAV系统文档化报告 / **H2**-文档梳理·补充清单·规范化过程 | 项目维护者 | 旧版系统文档化记录 |

---

## 十、SDK、移动端与前端文档

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [uav-edge-sdk/README.md](./uav-edge-sdk/README.md) | 无人机边缘计算SDK，C++高性能A*路径规划核心+PyBind11 Python封装，支持气象多因素风险评估、MAVLink飞控协议通信，C++模块不可用时自动降级为纯Python实现。 | **H1**-UAV Edge SDK / **H2**-特性·安装·快速开始 | 嵌入式开发者、无人机工程师 | SDK入口文档 |
| [uav-edge-sdk/INSTALL.md](./uav-edge-sdk/INSTALL.md) | SDK跨平台安装指南，Windows需Visual Studio C+++CMake，Linux需build-essential+cmake，macOS需Xcode CLT+brew cmake，推荐从源码编译安装。 | **H1**-Installation Guide / **H2**-Prerequisites·Installation Methods | 开发者 | SDK安装指南 |
| [uav-edge-sdk/CONTRIBUTING.md](./uav-edge-sdk/CONTRIBUTING.md) | SDK开源贡献流程规范，包括Fork仓库→创建特性分支→开发环境搭建→编写测试→更新CHANGELOG→提交PR的完整工作流。 | **H1**-Contributing to UAV Edge SDK / **H2**-Code of Conduct·Getting Started·Development Setup·Making Changes·Pull Request Process·Style Guides | 开源贡献者 | SDK贡献规范 |
| [uav-edge-sdk/CODE_OF_CONDUCT.md](./uav-edge-sdk/CODE_OF_CONDUCT.md) | 基于Contributor Covenant 2.1的社区行为准则，定义包容友善行为标准，规定四级违规处理机制：纠正→警告→临时封禁→永久封禁。 | **H1**-Contributor Covenant Code of Conduct / **H2**-Our Pledge·Our Standards·Enforcement Responsibilities·Enforcement·Enforcement Guidelines | 社区成员、贡献者 | 社区治理准则 |
| [uav-edge-sdk/CHANGELOG.md](./uav-edge-sdk/CHANGELOG.md) | SDK版本变更日志，v1.0.0（2026-05-07）记录C++/Python混合实现、A*路径规划、气象风险评估、MAVLink飞控接口等核心功能；规划ROS2集成、多机协同、ML风险评估。 | **H1**-Changelog / **H2**-[1.0.0]·[Unreleased] | 开发者、用户 | SDK版本变更记录 |
| [uav-mobile-app/README.md](./uav-mobile-app/README.md) | Flutter跨平台移动应用（iOS/Android），Riverpod状态管理+GoRouter路由+Dio网络请求，提供系统驾驶舱、路径规划可视化、WRF气象热力图、任务/无人机管理、边云协同等八大功能模块。 | **H1**-移动客户端 / **H2**-功能特性·技术栈·快速开始·项目结构 | 移动端开发者、终端用户 | 移动端应用总览 |
| [uav-path-planning-system/frontend-vue/README.md](./uav-path-planning-system/frontend-vue/README.md) | Vue3+Vite前端应用（端口3000），10个路由页面含智能驾驶舱（Cesium 3D AR数字地图+态势感知面板）、路径规划/气象数据（Leaflet 2D+ECharts）、任务/无人机/数据源管理、系统监控、历史记录。Ant Design Vue UI、Axios代理API网关（8088），含Cesium Token配置与生产构建优化说明。 | **H1**-Vue3前端应用 / **H2**-应用概述·页面功能一览·快速开始·Cesium 3D地图配置·API集成 | 前端开发者 | Web前端应用说明 |
| [uav-mobile-app/lib/config/README.md](./uav-mobile-app/lib/config/README.md) | Flutter应用全局配置模块，定义AppConfig类（应用名称"无人机路径规划系统"v1.0.0）、7个API端点常量（platform/wrf/forecast等）、主题色彩常量表，提供Material 3亮色与暗色双主题样式（含AppBar/Card/Input/Button/NavigationBar组件样式）。 | **H1**-config / **H2**-关键文件·配置项 | Flutter开发者 | 应用全局常量与主题配置 |
| [uav-mobile-app/lib/core/README.md](./uav-mobile-app/lib/core/README.md) | Flutter核心基础设施层总入口，聚合network/（网络通信）、storage/（本地持久化）、utils/（通用工具）三大子模块，为上层Service层和UI层提供统一的底层能力支撑，是应用架构的基石层。 | **H1**-core / **H2**-子模块 | Flutter开发者 | 核心基础设施层总入口 |
| [uav-mobile-app/lib/core/network/README.md](./uav-mobile-app/lib/core/network/README.md) | 基于Dio封装的HTTP网络通信模块，单例ApiClient封装GET/POST/PUT/DELETE及文件上传，15s连接超时30s接收超时；ApiInterceptor自动附加Bearer Token、X-Request-ID标记，401自动清除Token；统一ApiException异常体系。 | **H1**-core/network / **H2**-关键文件·错误处理 | Flutter开发者、后端对接人员 | HTTP网络层封装说明 |
| [uav-mobile-app/lib/core/storage/README.md](./uav-mobile-app/lib/core/storage/README.md) | 本地持久化存储模块，敏感非敏感数据分离架构：SecureStorage基于flutter_secure_storage利用系统Keychain/Keystore加密存储Token/RefreshToken/用户名等认证凭证；LocalStorage基于shared_preferences存储主题/语言/离线模式等偏好。 | **H1**-core/storage / **H2**-关键文件·存储策略 | Flutter开发者、安全审查人员 | 本地安全存储方案说明 |
| [uav-mobile-app/lib/core/utils/README.md](./uav-mobile-app/lib/core/utils/README.md) | 通用工具类集合，LogUtil基于logger包提供debug/info/warning/error四级静态日志方法统一日志输出；Debouncer防抖器默认300ms延迟，适用于防重复点击、搜索输入实时过滤等高频场景。 | **H1**-core/utils / **H2**-关键文件 | Flutter开发者 | 通用工具集合说明 |
| [uav-mobile-app/lib/models/README.md](./uav-mobile-app/lib/models/README.md) | 数据模型层（共8个模型文件），定义全部业务实体Dart数据类含JSON序列化/反序列化：drone（无人机状态）、task（任务+约束+航点）、waypoint（航点LatLng转换）、weather_data（含风险等级计算）、user（含isAdmin角色判断）、path_plan（算法耗时估算）、data_source（类型标签）、system_status（服务/算法状态）。 | **H1**-models / **H2**-关键文件 | Flutter开发者 | 业务数据模型层说明 |
| [uav-mobile-app/lib/providers/README.md](./uav-mobile-app/lib/providers/README.md) | 基于Riverpod的全局状态管理层，将Service层封装为Provider，AsyncNotifier管理异步数据加载/刷新/增删改，UI层通过ref.watch/ref.read消费；覆盖认证/无人机/任务/气象/规划/数据源/监控七大模块，建立Provider→Notifier→State三层体系。 | **H1**-providers / **H2**-关键文件·模块Provider清单 | Flutter开发者、架构设计人员 | Riverpod全局状态管理说明 |
| [uav-mobile-app/lib/services/README.md](./uav-mobile-app/lib/services/README.md) | 服务层封装全部后端API交互逻辑（9个核心服务），每个服务通过ApiClient发HTTP请求并将响应转为领域模型：AuthService（登录/登出/Token）、DroneService（CRUD）、TaskService、WeatherService、PathPlanningService（VRPTW/A*/DWA）、DataSourceService、MonitorService、EdgeCoordinatorService（边云协同）、OfflineService。 | **H1**-services / **H2**-关键文件 | Flutter开发者、后端对接人员 | 后端API交互服务层说明 |
| [uav-mobile-app/lib/widgets/README.md](./uav-mobile-app/lib/widgets/README.md) | 可复用Flutter Widget组件主目录，采用组件化架构将跨页面复用的基础Widget集中管理，当前包含common/子模块提供通用UI组件，提升代码复用性和维护一致性。 | **H1**-widgets / **H2**-子目录 | Flutter前端开发者 | 自定义Widget组件总目录 |
| [uav-mobile-app/lib/widgets/common/README.md](./uav-mobile-app/lib/widgets/common/README.md) | 通用UI组件集合（5个核心组件），在各业务页面共享复用：StatusCard（状态卡片含标题/数值/颜色/跳转）、LoadingPage（居中加载动画+提示）、ErrorPage（错误图标+消息+重试按钮）、EmptyPage（空状态图标+提示）、SectionTitle（分区标题含右侧附加Widget）。 | **H1**-widgets/common / **H2**-关键文件·组件清单 | Flutter前端开发者、UI设计实现人员 | 通用UI组件集合说明 |
| [uav-mobile-app/lib/pages/home/README.md](./uav-mobile-app/lib/pages/home/README.md) | 首页仪表盘模块（应用主入口），聚合展示系统概览（在线无人机数/待执行任务数/系统状态/今日完成数）、快速操作入口（路径规划/气象数据/任务/无人机管理）、气象预警、任务统计及六大核心能力展示，帮助用户快速掌握全局运行状况。 | **H1**-pages/home / **H2**-关键文件·页面结构 | 无人机运营人员、任务调度员 | 首页仪表盘页面说明 |
| [uav-mobile-app/lib/pages/login/README.md](./uav-mobile-app/lib/pages/login/README.md) | 登录认证页面，提供基于用户名/密码的表单认证，支持密码明文/密文切换（眼睛图标）、表单非空校验、Riverpod状态管理AuthService.login()调用、Token存储后跳转首页、预填默认凭据admin/admin123便于调试。 | **H1**-pages/login / **H2**-关键文件·功能 | 系统最终用户（操作员/调度员/管理员） | 登录认证页面说明 |
| [uav-mobile-app/lib/pages/monitoring/README.md](./uav-mobile-app/lib/pages/monitoring/README.md) | 系统监控页面，使用fl_chart实时呈现CPU/内存/磁盘使用率（5秒刷新）、在线/离线服务数量与健康评分、当前活跃任务数、各算法（3D-VAR/EnKF/VRPTW/A*/DWA等）执行时间和成功率柱状图，为运维提供可视化性能监控。 | **H1**-pages/monitoring / **H2**-关键文件·功能 | 系统运维人员、技术管理人员 | 性能监控可视化页面说明 |
| [uav-mobile-app/lib/pages/cockpit/README.md](./uav-mobile-app/lib/pages/cockpit/README.md) | 系统驾驶舱页面（核心可视化模块），fl_chart雷达图实现风速风向动态仪表（3秒实时更新）、flutter_map气象图层叠加二维风羽图、自定义绘制无人机飞线轨迹、fl_chart折线图展示风速/温度/湿度随高度深度剖面对比，是技术亮点最集中的界面。 | **H1**-pages/cockpit / **H2**-关键文件·可视化组件 | Flutter开发者、数据可视化工程师 | 实时气象可视化驾驶舱说明 |
| [uav-mobile-app/lib/pages/planning/README.md](./uav-mobile-app/lib/pages/planning/README.md) | 路径规划核心页面，基于flutter_map+OpenStreetMap瓦片，支持地图上添加/移动航点、调用多种算法（VRPTW全局分配/A*全局/DWA局部/全链路综合规划）进行路径计算，展示实时气象面板（风速/温度/湿度/风险等级）及路径距离+预计时间结果。 | **H1**-pages/planning / **H2**-关键文件·功能 | 任务规划员、无人机操作员 | 路径规划核心交互页面说明 |
| [uav-mobile-app/lib/pages/tasks/README.md](./uav-mobile-app/lib/pages/tasks/README.md) | 任务管理页面（无人机日常任务集中管控），支持按全部/待分配/已分配/执行中/已完成五种状态筛选任务列表，任务卡片展示类型标签（物流/巡检/救援/监测）+优先级+航点数，弹窗表单供新建任务，实现全生命周期便捷管理。 | **H1**-pages/tasks / **H2**-关键文件·功能 | 任务调度员、项目管理人员 | 任务全生命周期管理页面说明 |
| [uav-mobile-app/lib/pages/weather/README.md](./uav-mobile-app/lib/pages/weather/README.md) | 气象数据页面（无人机飞行气象决策支持），flutter_map叠加风速风向可视化图层，支持切换预报时间点和100m/500m/1000m/1500m高度层数据，实时显示风速/风向/温度/湿度/湍流度/能见度指标，fl_chart折线图展示趋势+气象预警列表。 | **H1**-pages/weather / **H2**-关键文件·功能 | 气象分析师、飞行安全管理人员 | 多高度层气象数据可视化说明 |
| [uav-mobile-app/lib/pages/drones/README.md](./uav-mobile-app/lib/pages/drones/README.md) | 无人机管理页面，卡片列表展示无人机关键信息（电池电量/型号/最大载荷/续航/速度），支持按在线/待命/维护三种状态筛选过滤，内置猎鹰/天鹰/闪电/海燕4系列共6架模拟数据，为路径规划提供设备资源池可视化管理。 | **H1**-pages/drones / **H2**-关键文件·功能 | 无人机操作员、设备管理员 | 无人机资产可视化管理说明 |
| [uav-mobile-app/lib/pages/data_sources/README.md](./uav-mobile-app/lib/pages/data_sources/README.md) | 数据源管理页面，TabBar组件实现分类切换查看5类气象数据来源：全部/地面气象观测站/海上浮标/卫星遥感/气象雷达，每种类型与DataSource模型的type字段标签对应，提供数据来源全景视图。 | **H1**-pages/data_sources / **H2**-关键文件·数据源类型 | 前端开发者、气象数据管理员 | 多源气象数据分类展示说明 |
| [uav-mobile-app/lib/pages/edge/README.md](./uav-mobile-app/lib/pages/edge/README.md) | 边云协同管理页面，调用EdgeCoordinatorService管理边缘计算节点，实时显示云端/边缘端连接状态（在线/离线），统计面板展示任务队列/已完成数/缓冲区使用率，核心功能将气象数据提交边缘节点做风险评估（low→severe四等级+颜色+警告信息）。 | **H1**-pages/edge / **H2**-关键文件·功能·风险评估等级 | 系统集成人员、前端开发者 | 边云协同交互与风险评估页面说明 |
| [uav-mobile-app/lib/pages/history/README.md](./uav-mobile-app/lib/pages/history/README.md) | 历史记录页面，展示已执行任务历史清单，三重过滤机制：按名称/编号模糊搜索、按成功/失败/进行中状态筛选、按起止日期范围选择，每条记录展示任务编号/名称/时间/状态/飞行距离/执行耗时等完整信息，供审计与回顾。 | **H1**-pages/history / **H2**-关键文件·功能 | 前端开发者、任务审计人员 | 历史任务查询与审计页面说明 |
| [uav-mobile-app/lib/pages/settings/README.md](./uav-mobile-app/lib/pages/settings/README.md) | 应用设置页面，三大配置组：服务器配置（API地址/边缘计算节点地址）、系统设置（离线地图缓存/地图类型/暗黑模式切换）、数据同步（自动同步开关），用户可根据部署环境和偏好灵活调整移动端行为。 | **H1**-pages/settings / **H2**-关键文件·配置分组 | 系统管理员、高级操作员 | 应用级全局配置页面说明 |

---

## 十一、辅助目录文档

以下文档为项目中各功能目录的 README 说明文件，主要用于目录作用解释和子文件索引，原则上每个目录包含一份：

| 文件路径 | 内容摘要 | 结构分析 | 目标受众 | 功能作用 |
|----------|---------|---------|---------|---------|
| [scripts/README.md](./scripts/README.md) | 自动化脚本集，包含Python类型注解自动分析、print转logging批量替换、pytest单元测试框架自动生成与补充等代码质量和测试辅助工具的说明。 | **H1**-自动化脚本集 / **H2**-概述·脚本分类 | 开发者 | 开发辅助工具集说明 |
| [uav-mobile-app/assets/README.md](./uav-mobile-app/assets/README.md) | Flutter移动应用静态资源目录说明，管理应用图标（icons/）、背景图片（images/）、自定义字体（fonts/）及运行参数配置（config/）四类资源文件。 | **H1**-assets / (目录说明) | Flutter开发者 | 静态资源目录 |
| [uav-mobile-app/assets/images/README.md](./uav-mobile-app/assets/images/README.md) | 应用图片资源目录说明，存储UI界面背景图、无人机型号图、气象示意图等位图资源，管理分辨率适配与格式规范。 | **H1**-images / (目录说明) | UI/UX设计师 | 图片资源目录 |
| [uav-mobile-app/assets/icons/README.md](./uav-mobile-app/assets/icons/README.md) | 应用图标资源目录说明，存储导航栏、功能入口、状态指示等SVG/PNG图标资源，管理图标命名规范与样式统一。 | **H1**-icons / (目录说明) | UI/UX设计师 | 图标资源目录 |
| [uav-mobile-app/assets/fonts/README.md](./uav-mobile-app/assets/fonts/README.md) | 应用自定义字体文件目录说明，管理本地字体资源（.ttf/.otf）的引入配置与跨平台渲染兼容性。 | **H1**-fonts / (目录说明) | UI/UX设计师 | 字体资源目录 |
| [uav-mobile-app/assets/config/README.md](./uav-mobile-app/assets/config/README.md) | 应用静态配置目录说明，存放入口URL、API版本号、功能开关等运行时常量配置文件，支持多环境切换。 | **H1**-config / (目录说明) | Flutter开发者 | 静态配置目录 |
| [data-assimilation-platform/service_python/src/api/core/README.md](./data-assimilation-platform/service_python/src/api/core/README.md) | Python服务核心模块目录说明，定义FastAPI应用实例创建、全局中间件注册、生命周期事件管理及依赖注入容器等应用基础框架代码。 | **H1**-core / (目录说明) | Python开发者 | 应用核心模块 |
| [data-assimilation-platform/service_python/src/api/routes/README.md](./data-assimilation-platform/service_python/src/api/routes/README.md) | Python服务路由模块目录说明，定义REST API端点注册、请求参数校验和响应序列化逻辑，按功能域（同化/方差/健康）分文件组织。 | **H1**-routes / (目录说明) | Python开发者 | API路由模块 |
| [data-assimilation-platform/service_python/src/api/services/README.md](./data-assimilation-platform/service_python/src/api/services/README.md) | Python服务业务逻辑层目录说明，封装数据同化核心算法调用、结果格式转换和异步任务管理，解耦路由与算法实现。 | **H1**-services / (目录说明) | Python开发者 | 业务服务模块 |
| [data-assimilation-platform/service_python/src/api/models/README.md](./data-assimilation-platform/service_python/src/api/models/README.md) | Python服务数据模型目录说明，定义请求体/响应体的Pydantic数据校验模型，确保输入输出数据的类型安全和完整性校验。 | **H1**-models / (目录说明) | Python开发者 | 数据模型模块 |
| [data-assimilation-platform/service_python/src/api/middleware/README.md](./data-assimilation-platform/service_python/src/api/middleware/README.md) | Python服务中间件目录说明，定义CORS跨域处理、请求日志记录、异常统一捕获和响应格式化中间件。 | **H1**-middleware / (目录说明) | Python开发者 | 中间件模块 |
| [data-assimilation-platform/service_python/src/api/utils/README.md](./data-assimilation-platform/service_python/src/api/utils/README.md) | Python服务工具函数目录说明，提供数据格式转换、文件IO操作、时间处理等通用辅助函数。 | **H1**-utils / (目录说明) | Python开发者 | 工具函数模块 |
| [data-assimilation-platform/service_python/src/api/parallel/README.md](./data-assimilation-platform/service_python/src/api/parallel/README.md) | Python服务并行计算模块目录说明，封装Dask/MPI/Ray多后端并行调度管理器，实现同化计算任务的分布式执行与资源调度。 | **H1**-parallel / (目录说明) | Python开发者 | 并行计算模块 |
| [data-assimilation-platform/algorithm_core/src/data_sources/README.md](./data-assimilation-platform/algorithm_core/src/data_sources/README.md) | 数据源适配器目录说明，定义WRF/GFS/卫星/雷达/浮标等多源数据的读取、格式转换与标准化接口，为同化算法提供统一数据入口。 | **H1**-data_sources / (目录说明) | 算法工程师 | 数据适配模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/README.md) | 贝叶斯同化核心算法目录说明，实现3D-VAR/4D-VAR/EnKF/Hybrid四种同化方法的核心计算逻辑和数学公式。 | **H1**-core / (目录说明) | 算法工程师 | 核心算法模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/components/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/components/README.md) | 同化组件目录说明，封装背景误差协方差矩阵构建、观测算子、增量分析等可复用的同化计算子组件。 | **H1**-components / (目录说明) | 算法工程师 | 算法组件模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/README.md) | 统计模型目录说明，定义高斯过程回归（GPR）、时空统计模型等辅助数据同化的概率统计模型实现。 | **H1**-models / (目录说明) | 算法工程师 | 统计模型模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/adapters/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/adapters/README.md) | 算法适配器目录说明，提供同化算法对外接口适配层，标准化不同算法方法的输入输出格式，支持REST/gRPC/CLI多协议调用。 | **H1**-adapters / (目录说明) | 算法工程师 | 接口适配模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/api/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/api/README.md) | 算法API层目录说明，定义FastAPI端点和请求处理逻辑，将算法核心能力暴露为标准化REST接口。 | **H1**-api / (目录说明) | 算法工程师 | API暴露层 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/quality_control/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/quality_control/README.md) | 数据质量控制模块目录说明，实现观测数据异常检测、一致性检验、离群值处理等质量控制流程，确保输入观测数据的可靠性。 | **H1**-quality_control / (目录说明) | 算法工程师 | 质量控制模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/visualization/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/visualization/README.md) | 可视化模块目录说明，基于Matplotlib+Cartopy实现同化前后气象场对比图、方差场分布图和分析场三维渲染等科学可视化输出。 | **H1**-visualization / (目录说明) | 数据分析师 | 可视化模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/utils/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/utils/README.md) | 同化工具函数目录说明，提供数值计算辅助、坐标转换、单位换算、数据插值等通用科学计算工具函数。 | **H1**-utils / (目录说明) | 算法工程师 | 科学计算工具 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/time_series/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/time_series/README.md) | 时间序列分析模块目录说明，实现气象时间序列的卡尔曼滤波平滑、趋势分解、周期性分析等功能，用于4D-VAR同化中的时间演化建模。 | **H1**-time_series / (目录说明) | 算法工程师 | 时序分析模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/risk_assessment/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/risk_assessment/README.md) | 风险评估模块目录说明，基于同化分析场的不确定性量化结果，评估目标区域气象风险等级，为路径规划提供安全级别参考。 | **H1**-risk_assessment / (目录说明) | 算法工程师 | 风险评估模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/parallel/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/parallel/README.md) | 并行计算模块目录说明，封装Dask分布式调度、MPI多进程通信、Ray任务并行三种后端的统一接口，实现同化计算任务的弹性并行化。 | **H1**-parallel / (目录说明) | 算法工程师 | 并行计算模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/accelerators/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/accelerators/README.md) | 硬件加速模块目录说明，封装CUDA（NVIDIA GPU）和JAX（TPU/GPU）两种加速后端的统一接口，实现同化核心计算的硬件加速。 | **H1**-accelerators / (目录说明) | 算法工程师 | GPU加速模块 |
| [data-assimilation-platform/algorithm_core/src/bayesian_assimilation/workflows/README.md](./data-assimilation-platform/algorithm_core/src/bayesian_assimilation/workflows/README.md) | 同化工作流模块目录说明，编排数据加载→质量控制→同化计算→后处理→可视化的端到端执行流程，支持批处理与实时流式两种模式。 | **H1**-workflows / (目录说明) | 算法工程师 | 工作流编排模块 |
| [data-assimilation-platform/shared/protos/common/README.md](./data-assimilation-platform/shared/protos/common/README.md) | Protocol Buffers通用数据结构定义目录说明，定义跨服务共享的地理坐标、气象要素、时间戳等基础数据类型。 | **H1**-common / (目录说明) | 全栈开发者 | Proto通用类型 |
| [data-assimilation-platform/shared/protos/common/v1/README.md](./data-assimilation-platform/shared/protos/common/v1/README.md) | Proto通用类型v1版本详细接口定义，声明GeoPoint、WeatherElement、Timestamp等基础消息体的字段与约束。 | **H1**-v1 / (目录说明) | 全栈开发者 | Proto通用类型v1 |
| [data-assimilation-platform/shared/protos/request/v1/README.md](./data-assimilation-platform/shared/protos/request/v1/README.md) | Proto请求消息v1版本定义目录说明，声明AssimilationRequest、ForecastRequest等请求消息体结构。 | **H1**-v1 / (目录说明) | 全栈开发者 | Proto请求定义v1 |
| [data-assimilation-platform/shared/protos/request/v2/README.md](./data-assimilation-platform/shared/protos/request/v2/README.md) | Proto请求消息v2版本定义目录说明，v2版本引入批量处理、流式传输等增强请求结构。 | **H1**-v2 / (目录说明) | 全栈开发者 | Proto请求定义v2 |
| [data-assimilation-platform/shared/protos/response/v1/README.md](./data-assimilation-platform/shared/protos/response/v1/README.md) | Proto响应消息v1版本定义目录说明，声明AssimilationResponse、VarianceField等响应消息体结构。 | **H1**-v1 / (目录说明) | 全栈开发者 | Proto响应定义v1 |
| [data-assimilation-platform/shared/protos/response/v2/README.md](./data-assimilation-platform/shared/protos/response/v2/README.md) | Proto响应消息v2版本定义目录说明，v2版本引入流式响应、分页结果等增强响应结构。 | **H1**-v2 / (目录说明) | 全栈开发者 | Proto响应定义v2 |
| [data-assimilation-platform/shared/protos/service/v1/README.md](./data-assimilation-platform/shared/protos/service/v1/README.md) | Proto服务定义v1版本目录说明，声明AssimilationService的gRPC服务接口（ExecuteAssimilation/GetVariance/HealthCheck）。 | **H1**-v1 / (目录说明) | 全栈开发者 | Proto服务定义v1 |
| [data-assimilation-platform/shared/protos/service/v2/README.md](./data-assimilation-platform/shared/protos/service/v2/README.md) | Proto服务定义v2版本目录说明，v2版本引入流式同化接口和批量处理RPC方法。 | **H1**-v2 / (目录说明) | 全栈开发者 | Proto服务定义v2 |

---

## 统计概览

| 分类 | 文件数 | 核心覆盖范围 |
|------|:-----:|------------|
| 一、项目总览与入口 | 4 | 项目总入口、文档中心、快速参考、完整构建指南 |
| 二、架构与设计 | 8 | 微服务架构、项目结构、端口配置、数据同化架构 |
| 三、微服务模块 | 21 | 12个核心微服务（含新增3个气象服务）+旧版系统+数据同化平台各服务组件 |
| 四、部署与运维 | 25 | Docker/K8s/监控/边缘/流处理/备份/数据库/ArgoCD/Istio/容灾/可观测性 |
| 五、API 接口 | 24 | 8个服务群的完整接口文档（REST+WebSocket+gRPC） |
| 六、开发指南与规范 | 10 | 熔断器、异常处理、安全密钥、故障排查、编码规范、PR模板 |
| 七、数据同化平台 | 16 | 算法核心库、示例代码、测试指南、配置、基准测试、性能报告 |
| 八、测试与质量保障 | 8 | 6类测试体系、性能测试、E2E测试、移动端测试 |
| 九、报告与归档 | 28 | 12份质量报告+12份历史归档+4份专项报告 |
| 十、SDK与移动端前端 | 28 | C++边缘SDK（5）、Flutter移动端（23含全lib/页面结构）、Vue3前端（1） |
| 十一、辅助目录 | 24 | 各功能子目录的README索引说明 |
| **合计** | **209** | **全项目覆盖，无遗漏** |

---

> **索引维护说明**：当项目新增、修改或删除 Markdown 文档时，请同步更新本索引的对应条目。新增文档按所属分类插入对应章节表格，删除文档从表格移除对应行，修改文档需同步更新"内容摘要""结构分析"列信息。
>
> **快速定位技巧**：在 IDE 中 `Ctrl+F` 搜索模块名、技术关键词（如"熔断""K8s""WRF""同化"）或文件名即可秒级定位。
>
> **索引版本**：v1.1 | **最后更新**：2026-06-01 | **维护者**：DITHIOTHREITOL