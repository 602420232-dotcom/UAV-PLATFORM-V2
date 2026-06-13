# 迁移进度追踪

## 阶段一：骨架搭建 ✅

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 1.1 创建目录结构 | ✅ | - | 2026-06-12 |
| 1.2 编写父 POM | ✅ | - | 2026-06-12 |
| 1.3 搭建 CI/CD | ✅ | - | 2026-06-12 |
| 1.4 配置开发工具链 | ✅ | - | 2026-06-12 |
| 1.5 编写 docker-compose | ✅ | - | 2026-06-12 |
| 1.6 初始化 Git 仓库 | ✅ | - | 2026-06-12 |

## 阶段二：公共模块迁移 ✅

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 2.1 common-core | ✅ | - | 2026-06-13 |
| 2.2 common-security | ✅ | - | 2026-06-13 |
| 2.3 common-web | ✅ | - | 2026-06-13 |
| 2.4 common-resilience | ✅ | - | 2026-06-13 |
| 2.5 common-kafka | ✅ | - | 2026-06-13 |

## 阶段三：核心服务迁移 ✅

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 3.1 api-gateway | ✅ | - | 2026-06-13 |
| 3.2 platform-api | ✅ | - | 2026-06-13 |
| 3.3 weather-api | ✅ | - | 2026-06-13 |
| 3.4 planning-api | ✅ | - | 2026-06-13 |
| 3.5 assimilation-api | ✅ | - | 2026-06-13 |
| 3.6 observation-api | ✅ | - | 2026-06-13 |
| 3.7 risk-api | ✅ | - | 2026-06-13 |
| 3.8 utm-api | ✅ | - | 2026-06-13 |

> **注**: airworthiness-api 已合并至 risk-api，risk-api 包含适航评估功能。

## 阶段四：Python 服务迁移 ✅

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 4.1 合并去重算法代码 | ✅ | - | 2026-06-13 |
| 4.2 迁移 model-engine | ✅ | - | 2026-06-13 |
| 4.3 迁移 fengwu/tianzi/fenglei | ✅ | - | 2026-06-13 |
| 4.4 迁移 edge-cloud-coordinator | ✅ | - | 2026-06-13 |

> **注**: algorithm-engine 包含 20+ 算法（风乌/天资/风雷/数据同化/路径规划/风险评估等）。

## 阶段五：集成与验收 🔄

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 5.1 开发者控制台 (Vue 3) | ✅ | - | 2026-06-13 |
| 5.2 SDK 开发 (Java + Python) | ✅ | - | 2026-06-13 |
| 5.3 端到端集成测试 (9/9 passed) | ✅ | - | 2026-06-13 |
| 5.4 文档完善 | 🔄 | - | - |
| 5.5 生产部署 | ⏳ | - | - |
| 5.6 监控告警 | ⏳ | - | - |

> **Gateway**: 独立构建已验证（Spring Boot 3.4.x + Spring Cloud 2024.0.3），与主项目 Spring Boot 4.0 解耦。

## 旧模块 → 新模块映射

| 旧模块 | 新模块 | 迁移状态 |
|--------|--------|:--------:|
| common-utils | common/{core,security,resilience,web,kafka} | ✅ |
| api-gateway | gateway/api-gateway | ✅ |
| uav-platform-service | services/platform-api | ✅ |
| wrf-processor-service | services/weather-api | ✅ |
| meteor-forecast-service | services/weather-api | ✅ |
| path-planning-service | services/planning-api | ✅ |
| data-assimilation-service | services/assimilation-api | ✅ |
| uav-weather-collector | services/weather-api | ✅ |
| airworthiness-service | services/risk-api | ✅ |
| model-engine | python/algorithm-engine | ✅ |
| fengwu-service | python/algorithm-engine | ✅ |
| tianzi-service | python/algorithm-engine | ✅ |
| fenglei-service | python/algorithm-engine | ✅ |
| edge-cloud-coordinator | python/algorithm-engine | ✅ |
| data-assimilation-platform | python/algorithm-engine | ✅ |
