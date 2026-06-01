# Data Assimilation Service - Spring Boot

## 📋 服务概述

Spring Boot 微服务，提供数据同化功能的 REST API 接口。

**技术栈**:
- Spring Boot 3.2.0
- Java 17
- Maven
- Spring Data JPA
- Spring Security

**服务端口**: 8084

---

## 📁 项目结构

```
service_spring/
├── src/
│   ├── main/
│   │   ├── java/com/uav/assimilation/
│   │   │   ├── controller/      # REST 控制器
│   │   │   ├── service/         # 业务逻辑
│   │   │   ├── repository/      # 数据访问
│   │   │   ├── model/           # 数据模型
│   │   │   ├── config/          # 配置类
│   │   │   └── dto/             # 数据传输对象
│   │   └── resources/
│   │       ├── application.yml  # 应用配置
│   │       ├── application-dev.yml
│   │       ├── application-prod.yml
│   │       └── application-test.yml
│   └── test/
│       ├── java/               # 单元测试
│       └── resources/          # 测试配置
├── pom.xml                     # Maven 配置
└── README.md                   # 本文档
```

---

## 🚀 快速开始

### 构建

```bash
# 清理构建
mvn clean

# 打包（跳过测试）
mvn package -DskipTests

# 运行测试
mvn test

# 完整构建
mvn clean package
```

### 运行

```bash
# 开发模式
mvn spring-boot:run

# 生产模式
java -jar target/service_spring-1.0.0.jar

# 指定配置文件
java -jar target/service_spring-1.0.0.jar --spring.profiles.active=prod
```

---

## 🔧 配置

### application.yml

```yaml
server:
  port: 8084

spring:
  application:
    name: data-assimilation-service
  
  datasource:
    url: jdbc:mysql://localhost:3306/uav_data_assimilation
    username: root
    password: ${DB_PASSWORD}
  
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
  
  redis:
    host: localhost
    port: 6379

# 算法配置
assimilation:
  python-script: classpath:python/bayesian_assimilation.py
  timeout: 300000

# JWT 配置
uav:
  jwt:
    enabled: true
    secret: ${JWT_SECRET}
    expiration: 86400000
```

---

## 🔌 API 接口

### REST 控制器

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/assimilation/execute` | POST | 执行同化 |
| `/api/assimilation/variance` | POST | 计算方差 |
| `/api/assimilation/batch` | POST | 批量同化 |
| `/api/assimilation/status/{id}` | GET | 查询状态 |
| `/actuator/health` | GET | 健康检查 |

---

## 🧪 测试

```bash
# 运行所有测试
mvn test

# 运行特定测试类
mvn test -Dtest=AssimilationControllerTest

# 生成覆盖率报告
mvn test jacoco:report
```

---

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t uav-assimilation-service:latest .

# 运行容器
docker run -d -p 8084:8084 \
  -e DB_PASSWORD=secret \
  uav-assimilation-service:latest
```

---

## 📚 相关文档

- [Data Assimilation Platform](../README.md)
- [Algorithm Core](../algorithm_core/README.md)
- [API Documentation](../../docs/api/)

---

**最后更新**: 2026-05-08
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
