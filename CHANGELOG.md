# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 项目骨架搭建
- 父 POM 配置（JDK 21 + Spring Boot 4.0）
- CI/CD 流水线（GitHub Actions）
- Docker Compose 基础设施编排
- pre-commit 代码规范配置

## [2.0.0] - 2026-06-12

### Added
- 全新架构设计，面向 API 平台定位
- 多租户独立 Schema 隔离
- Header 版本 API 策略
- 7 个核心 API 服务规划

### Changed
- JDK 17 → 21
- Spring Boot 3.5 → 4.0
- Nacos 2.3 → 3.2
- Vite 5 → 7

### Removed
- 业务层代码（订单/支付/客户管理）
- Jython 依赖
- 5 个骨架服务
- 论坛模块
