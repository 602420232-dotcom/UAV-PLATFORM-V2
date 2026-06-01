# backend-spring 后端服务

## 概述

`uav-path-planning-system/backend-spring` 是旧版系统的 Spring Boot 后端服务，提供认证授权、用户管理、路径规划接口。

## 技术栈

- **框架**: Spring Boot 3.2.0
- **安全**: Spring Security + JWT (jjwt 0.11.5)
- **ORM**: MyBatis-Plus 3.5.5 + JPA
- **通信**: gRPC
- **数据库**: MySQL + Redis

## 构建与运行

```bash
# 从项目根目录
mvn clean package -pl uav-path-planning-system/backend-spring -am -DskipTests
mvn spring-boot:run -pl uav-path-planning-system/backend-spring
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
