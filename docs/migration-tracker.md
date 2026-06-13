# 迁移进度追踪

## 阶段一：骨架搭建

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 1.1 创建目录结构 | ✅ | - | 2026-06-12 |
| 1.2 编写父 POM | ✅ | - | 2026-06-12 |
| 1.3 搭建 CI/CD | ✅ | - | 2026-06-12 |
| 1.4 配置开发工具链 | ✅ | - | 2026-06-12 |
| 1.5 编写 docker-compose | ✅ | - | 2026-06-12 |
| 1.6 初始化 Git 仓库 | ⏳ | - | - |

## 阶段二：公共模块迁移

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 2.1 common-core | ⏳ | - | - |
| 2.2 common-security | ⏳ | - | - |
| 2.3 common-web | ⏳ | - | - |
| 2.4 common-resilience | ⏳ | - | - |

## 阶段三：核心服务迁移

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 3.1 api-gateway | ⏳ | - | - |
| 3.2 platform-api | ⏳ | - | - |
| 3.3 weather-api | ⏳ | - | - |
| 3.4 planning-api | ⏳ | - | - |
| 3.5 assimilation-api | ⏳ | - | - |
| 3.6 observation-api | ⏳ | - | - |
| 3.7 airworthiness-api | ⏳ | - | - |
| 3.8 utm-api | ⏳ | - | - |

## 阶段四：Python 服务迁移

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 4.1 合并去重算法代码 | ⏳ | - | - |
| 4.2 迁移 model-engine | ⏳ | - | - |
| 4.3 迁移 fengwu/tianzi/fenglei | ⏳ | - | - |
| 4.4 迁移 edge-cloud-coordinator | ⏳ | - | - |

## 阶段五：集成与验收

| Task | 状态 | 负责人 | 完成日期 |
|------|:----:|--------|----------|
| 5.1 开发者控制台 | ⏳ | - | - |
| 5.2 SDK 开发 | ⏳ | - | - |
| 5.3 端到端集成测试 | ⏳ | - | - |
| 5.4 文档完善 | ⏳ | - | - |
| 5.5 生产部署 | ⏳ | - | - |

## 旧模块 → 新模块映射

| 旧模块 | 新模块 | 迁移状态 |
|--------|--------|:--------:|
| common-utils | common/{core,security,resilience,web} | ⏳ |
| api-gateway | gateway/api-gateway | ⏳ |
| uav-platform-service | services/platform-api | ⏳ |
| wrf-processor-service | services/weather-api | ⏳ |
| meteor-forecast-service | services/weather-api | ⏳ |
| path-planning-service | services/planning-api | ⏳ |
| data-assimilation-service | services/assimilation-api | ⏳ |
| uav-weather-collector | services/weather-api | ⏳ |
| model-engine | python/model-engine | ⏳ |
| fengwu-service | python/fengwu-service | ⏳ |
| tianzi-service | python/tianzi-service | ⏳ |
| fenglei-service | python/fenglei-service | ⏳ |
| edge-cloud-coordinator | python/edge-cloud-coordinator | ⏳ |
| data-assimilation-platform | python/assimilation-core | ⏳ |
