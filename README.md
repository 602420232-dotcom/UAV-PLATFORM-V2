# UAV Platform V2

面向低空无人机的风险感知路径规划 API 平台

## 项目定位

纯技术平台，提供气象驱动路径规划算法能力 API，不碰业务层（订单/支付/客户管理由集成方负责）。

## 核心能力

- 多模型融合气象预报（WRF + 风乌 + 天资 + 风雷）
- 贝叶斯不确定性量化（3D-VAR / 4D-VAR / EnKF）
- 风险感知路径规划（VRPTW + DE-RRT* + DWA + MPC）
- 主动观测决策（观测-同化-规划闭环）
- UTM 监管对接（空域管理、飞行审批、合规校验）

## 技术栈

- JDK 21 + Spring Boot 4.0 + Spring Cloud 2025.1
- Nacos 3.2 + Undertow + MyBatis Plus 3.5.9
- MySQL 8.4.7 LTS + Redis 7.2
- FastAPI + PyTorch + ONNX Runtime
- Vue 3.5 + Vite 7 + TypeScript + CesiumJS
- Docker + K8s + SkyWalking + Prometheus + Grafana

## 快速开始

```bash
# 1. 启动基础设施
docker compose up -d nacos mysql redis kafka

# 2. 构建 Java 服务
mvn clean package -DskipTests

# 3. 启动网关
docker compose up -d api-gateway

# 4. 验证
open http://localhost:8088/actuator/health
```

## 目录结构

```
uav-platform-v2/
├── common/          # 公共模块
├── gateway/         # API 网关
├── services/        # 核心 API 服务
├── python/          # Python 算法服务
├── console/         # 开发者控制台
├── sdk/             # 客户端 SDK
├── deployments/     # 部署配置
└── docs/            # 技术文档
```

## 开发规范

- Trunk Based 分支策略
- 2 人代码审查
- 提交前运行 pre-commit
- 按需发布

## 许可证

MIT
