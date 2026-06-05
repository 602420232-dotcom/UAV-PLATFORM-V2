# 文档更新检查清单

## 📋 概述

本文档提供了在进行系统架构、功能或服务发生变更时，必须同步更新的文档清单，确保文档与实际代码实现保持一致。

---

## ✅ 新增服务检查清单

### 1. 架构文档

| 检查项 | 文档 | 状态 |
|--------|------|
| 添加服务到架构图 | [architecture.md](architecture.md) | ☐
| 添加服务到模块列表 | [architecture.md](architecture.md) | ☐
| 更新模块边界定义 | [architecture.md](architecture.md) | ☐

### 2. 项目结构文档

| 检查项 | 文档 | 状态 |
|--------|------|------|
| 添加服务到目录树 | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | ☐
| 更新后端服务端口映射表 | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | ☐
| 更新 API Gateway 路由配置 | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | ☐

### 3. 端口配置文档

| 检查项 | 文档 | 状态 |
|--------|------|------|
| 添加服务到微服务列表 | [PORTS_CONFIGURATION.md](PORTS_CONFIGURATION.md) | ☐
| 更新端口分配到健康检查端点 | [PORTS_CONFIGURATION.md](PORTS_CONFIGURATION.md) | ☐
| 添加健康检查端点 | [PORTS_CONFIGURATION.md](PORTS_CONFIGURATION.md) | ☐
| 添加 API 网关路由映射 | [PORTS_CONFIGURATION.md](PORTS_CONFIGURATION.md) | ☐

### 4. API 文档

| 检查项 | 文档 | 状态 |
|--------|------|------|
| 添加服务到 API 服务列表 | [api/README.md](api/README.md) | ☐
| 创建服务 API 文档 | api/<service>/README.md | ☐
| 更新 API 网关路由说明 | [api/README.md](api/README.md) | ☐

### 5. 主 README

| 检查项 | 文档 | 状态 |
|--------|------|------|
| 更新项目结构部分 | [README.md](../README.md) | ☐
| 更新模块文档索引 | [README.md](../README.md) | ☐

### 6. 服务自身文档

| 检查项 | 文档 | 状态 |
|--------|------|------|
| 创建服务 README.md | <service>/README.md | ☐
| 描述服务概述、技术栈、项目结构 | <service>/README.md | ☐
| 描述 API 端点、部署指南 | <service>/README.md | ☐

---

## 🔄 修改服务检查清单

### 1. 端口变更

- [ ] 更新 [PORTS_CONFIGURATION.md](PORTS_CONFIGURATION.md) 中的微服务列表
- [ ] 更新 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 中的端口映射表
- [ ] 更新 [api/README.md](api/README.md) 中的路由配置
- [ ] 更新服务自身的 README.md

### 2. API 路由变更

- [ ] 更新 [api/README.md](api/README.md) 中的路由映射
- [ ] 更新 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 中的路由配置
- [ ] 更新 [PORTS_CONFIGURATION.md](PORTS_CONFIGURATION.md) 中的 API 网关路由
- [ ] 更新服务 API 文档中的端点说明

### 3. 功能变更

- [ ] 更新 [architecture.md](architecture.md) 中的模块边界说明
- [ ] 更新服务 README.md 中的功能描述
- [ ] 如有需要，更新 CHANGELOG.md

---

## 🏗️ 架构变更检查清单

### 1. 新增微服务架构变更

- [ ] 更新 [architecture.md](architecture.md) 中的架构图
- [ ] 更新 [architecture.md](architecture.md) 中的模块边界定义
- [ ] 更新 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 中的服务端口映射表
- [ ] 更新 [PORTS_CONFIGURATION.md](PORTS_CONFIGURATION.md) 中的微服务列表

### 2. 技术栈变更

- [ ] 更新 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 中的技术栈说明
- [ ] 更新相关服务 README.md 中的技术栈
- [ ] 更新 [DEPLOYMENT.md](DEPLOYMENT.md) 中的部署配置

---

## 📝 文档版本管理

### 所有文档的版本约定

```
文件末尾必须包含：
> **最后更新**: YYYY-MM-DD
> **版本**: X.X
> **维护者**: [维护者名称]
```

### 版本号规则

- **主版本号**: 重大架构变更
- **次版本号**: 新增服务或功能
- **修订号**: 文档修复或小更新

---

## 🔍 文档审核检查清单

### 文档一致性检查

在提交文档更新时，请检查：

- [ ] 所有相关文档同步更新
- [ ] 版本号正确递增
- [ ] 最后更新日期更新为当前日期
- [ ] 所有链接可访问
- [ ] 技术栈描述准确
- [ ] 端口配置一致
- [ ] API 路由配置一致

### 文档完整性检查

- [ ] 所有服务有 README.md
- [ ] 服务概述完整
- [ ] 技术栈说明清晰
- [ ] 项目结构描述清楚
- [ ] API 端点文档完整
- [ ] 部署指南详细

---

## 📅 文档快速参考表

### 关键文档索引

| 文档 | 主要变更类型 | 文档路径 |
|------|------------|
| **架构文档** | 新增/修改服务、架构变更 | [architecture.md |
| **项目结构** | 新增/修改服务 | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) |
| **端口配置** | 端口/路由变更 | [PORTS_CONFIGURATION.md](PORTS_CONFIGURATION.md) |
| **API 文档** | API 端点变更 | [api/README.md](api/README.md) |
| **部署文档** | 部署流程变更 | [DEPLOYMENT.md](DEPLOYMENT.md) |
| **变更日志** | 功能变更 | [CHANGELOG.md](CHANGELOG.md) |

---

## 🎯 使用指南

### 新增服务步骤

1. 创建服务目录结构
2. 复制本清单复制到服务目录
3. 更新所有相关文档
4. 进行文档审核
5. 提交更改

### 修改服务步骤

1. 更新服务
2. 使用本清单检查所有需要更新的文档
3. 更新相关文档
4. 文档审核
5. 提交更改

---

## 📞 技术支持

如有问题，请联系：

- **维护者**: DITHIOTHREITOL
- **问题反馈**: 通过 GitHub Issues

---

> **最后更新**: 2026-06-05
> **版本**: 1.0
> **维护者**: DITHIOTHREITOL
