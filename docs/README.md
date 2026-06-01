# 📚 UAV Path Planning System - Documentation Index

## 🎯 我需要...

### 🚀 快速开始
| 任务 | 文档 |
|------|------|
| 了解项目 | [README.md](../README.md) |
| 快速部署 | [DEPLOYMENT.md](DEPLOYMENT.md) |
| 常用命令速查 | [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) |

### 🏗️ 系统架构
| 任务 | 文档 |
|------|------|
| 了解项目结构 | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) |
| 架构设计详解 | [architecture.md](architecture.md) |
| 服务依赖关系 | [PROJECT_STRUCTURE.md#服务依赖关系图](PROJECT_STRUCTURE.md#服务依赖关系图) |

### 🛡️ 安全配置
| 任务 | 文档 |
|------|------|
| JWT配置 | [PRODUCTION_SECRETS_GUIDE.md](PRODUCTION_SECRETS_GUIDE.md) |
| 安全审计报告 | [security_audit_report.md](security_audit_report.md) |
| CSRF/CORS配置 | [common-utils/../README.md](../common-utils/README.md) |

### 🛡️ 熔断器 (Circuit Breaker)
| 任务 | 文档 |
|------|------|
| 熔断器使用指南 | [CIRCUIT_BREAKER_GUIDE.md](CIRCUIT_BREAKER_GUIDE.md) |
| 代码示例 | [CIRCUIT_BREAKER_USAGE_EXAMPLES.md](CIRCUIT_BREAKER_USAGE_EXAMPLES.md) |
| 实现报告 | [CIRCUIT_BREAKER_IMPLEMENTATION_REPORT.md](CIRCUIT_BREAKER_IMPLEMENTATION_REPORT.md) |

### 📊 监控与日志
| 任务 | 文档 |
|------|------|
| 监控配置 | [deployments/monitoring/README.md](../deployments/monitoring/README.md) |
| Prometheus配置 | [deployments/monitoring/prometheus/README.md](../deployments/monitoring/prometheus/README.md) |
| ELK日志聚合 | [deployments/monitoring/README.md#elk-stack-日志聚合](../deployments/monitoring/README.md#elk-stack-日志聚合) |

### 🔧 部署运维
| 任务 | 文档 |
|------|------|
| Docker部署 | [DOCKER.md](DOCKER.md) |
| Kubernetes部署 | [deployments/kubernetes/README.md](../deployments/kubernetes/README.md) |
| 生产环境配置 | [PRODUCTION_SECRETS_GUIDE.md](PRODUCTION_SECRETS_GUIDE.md) |

### 📈 代码质量
| 任务 | 文档 |
|------|------|
| 改进报告 | [IMPROVEMENTS_COMPLETED_REPORT.md](IMPROVEMENTS_COMPLETED_REPORT.md) |
| 自动修复总结 | [AUTO_FIXES_SUMMARY.md](AUTO_FIXES_SUMMARY.md) |
| 质量审计报告 | [PROJECT_QUALITY_AUDIT_FINAL_REPORT.md](PROJECT_QUALITY_AUDIT_FINAL_REPORT.md) |

### 📝 API文档
| 任务 | 文档 |
|------|------|
| API总览 | [api/README.md](api/README.md) |
| API调用示例 | [api/USAGE_EXAMPLES.md](api/USAGE_EXAMPLES.md) |

### 🧪 测试
| 任务 | 文档 |
|------|------|
| 单元测试 | [tests/README.md](../tests/README.md) |
| 集成测试 | [tests/INTEGRATION_TESTS.md](../tests/INTEGRATION_TESTS.md) |
| 性能测试 | [test_performance.py](../data-assimilation-platform/test_performance.py) |

---

## 📖 文档分类

### 🎓 新手入门
1. [README.md](../README.md) - 项目概述
2. [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
3. [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - 快速参考

### 👨‍💻 开发人员
1. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 项目结构
2. [CIRCUIT_BREAKER_GUIDE.md](CIRCUIT_BREAKER_GUIDE.md) - 熔断器使用
3. [api/README.md](api/README.md) - API文档

### 🛡️ 安全运维
1. [PRODUCTION_SECRETS_GUIDE.md](PRODUCTION_SECRETS_GUIDE.md) - 安全配置
2. [security_audit_report.md](security_audit_report.md) - 安全审计
3. [deployments/monitoring/README.md](../deployments/monitoring/README.md) - 监控运维

### 📊 项目管理
1. [IMPROVEMENTS_COMPLETED_REPORT.md](IMPROVEMENTS_COMPLETED_REPORT.md) - 改进报告
2. [CHANGELOG.md](../CHANGELOG.md) - 更新日志
3. [PROJECT_QUALITY_AUDIT_FINAL_REPORT.md](PROJECT_QUALITY_AUDIT_FINAL_REPORT.md) - 质量审计

---

## 🔍 按文件名查找

| 文件名 | 说明 |
|--------|------|
| [README.md](../README.md) | 项目总览 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署指南 |
| [DOCKER.md](DOCKER.md) | Docker说明 |
| [CHANGELOG.md](../CHANGELOG.md) | 更新日志 |
| [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) | 快速参考 |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 项目结构 |
| [CIRCUIT_BREAKER_GUIDE.md](CIRCUIT_BREAKER_GUIDE.md) | 熔断器指南 |
| [PRODUCTION_SECRETS_GUIDE.md](PRODUCTION_SECRETS_GUIDE.md) | 生产配置 |
| [IMPROVEMENTS_COMPLETED_REPORT.md](IMPROVEMENTS_COMPLETED_REPORT.md) | 改进报告 |
| [AUTO_FIXES_SUMMARY.md](AUTO_FIXES_SUMMARY.md) | 自动修复 |
| [PROJECT_QUALITY_AUDIT_FINAL_REPORT.md](PROJECT_QUALITY_AUDIT_FINAL_REPORT.md) | 质量审计 |
| [security_audit_report.md](security_audit_report.md) | 安全审计 |

---

## 📅 最近更新

### 2026-05-08
- ✅ 熔断器实现完成
- ✅ common-utils模块文档完善
- ✅ 所有Java服务添加熔断器保护
- ✅ 监控配置完成
- ✅ 改进报告发布

详见: [CHANGELOG.md](../CHANGELOG.md)

---

## 💡 提示

- 🔖 **收藏此页**: 快速访问所有文档
- 🔍 **使用搜索**: 按文件名或内容搜索
- 📝 **查看源码**: 直接阅读 `src/` 下的代码注释
- 🐛 **报告问题**: 在 GitHub Issues 提交
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
