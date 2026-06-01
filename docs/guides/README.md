# guides

本目录包含 UAV 路径规划系统面向开发者的各类技术指南和使用手册。涵盖断路器使用、异常处理与 HTTP 状态码规范、生产环境密钥管理以及常见问题排查，帮助开发者快速上手并遵循项目的最佳实践。

| 文件 | 描述 |
|------|------|
| [CIRCUIT_BREAKER_GUIDE.md](CIRCUIT_BREAKER_GUIDE.md) | 断路器使用指南，介绍 Resilience4j 断路器在微服务中的配置方式、策略参数和降级处理 |
| [CIRCUIT_BREAKER_USAGE_EXAMPLES.md](CIRCUIT_BREAKER_USAGE_EXAMPLES.md) | 断路器使用示例，提供各微服务场景下的断路器集成代码示例和最佳实践 |
| [EXCEPTION_HTTP_STATUS_GUIDE.md](EXCEPTION_HTTP_STATUS_GUIDE.md) | 异常与 HTTP 状态码规范指南，定义全局异常处理策略和各业务场景对应的标准 HTTP 状态码 |
| [PRODUCTION_SECRETS_GUIDE.md](PRODUCTION_SECRETS_GUIDE.md) | 生产环境密钥管理指南，说明敏感配置的加密存储、环境隔离和密钥轮换策略 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 故障排查指南，汇总系统常见问题的诊断方法和解决方案，包括服务不可用、数据同步异常等 |

---
> **最后更新**: 2026-06-01  
> **版本**: 1.0  
> **维护者**: DITHIOTHREITOL
