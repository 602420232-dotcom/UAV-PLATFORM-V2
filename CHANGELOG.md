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

## [2.0.1] - 2026-06-13

### Fixed
- Fix Docker network conflict (172.28.0.0/16) and Kafka port (19092)
- Upgrade MyBatis Plus to 3.5.16 with boot4 starter for Spring Boot 4.0
- Add MySQL allowPublicKeyRetrieval for caching_sha2_password authentication
- Remove Nacos config and discovery dependencies for local E2E testing
- Fix HmacAuthenticationFilter conditional bean registration and List<HandlerMapping> injection
- Add RedisConfig bean for RedisTemplate auto-configuration
- Fix DynamicDataSource @Primary annotation and exclude DataSourceAutoConfiguration
- Add spring-boot-starter-kafka for KafkaTemplate auto-configuration
- Fix api-gateway Redis reactive auto-configuration compatibility
- Fix CI/CD frontend build path (developer-console -> console)
- Fix Console Dockerfile COPY path

### Added
- Standalone gateway build (Spring Boot 3.4.x + Spring Cloud 2024.0.3)
- Gateway local profile with explicit localhost routes
- VERSION_STATUS.md version dashboard
- MVP Phase 1 audit report and remediation plan
- E2E test script with mock/real dual mode
- Service startup script (PowerShell)

### Changed
- Gateway route configuration: old service names -> actual service names
- All services use offset ports (18080-18087) for local E2E testing

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
