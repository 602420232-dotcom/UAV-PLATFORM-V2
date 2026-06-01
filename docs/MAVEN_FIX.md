# Maven 依赖问题修复指南

## 问题现象

IDE 提示以下错误：
```
Missing artifact org.hibernate:hibernate-*
Missing artifact org.assertj:assertj-*
Missing artifact org.springframework.boot:*
```

## 问题原因

1. Maven 本地仓库的依赖没有正确下载或缓存损坏
2. 网络问题导致依赖下载失败
3. IDE 缓存未更新

**注意**：这些依赖实际上已经在 `pom.xml` 中通过以下 starter 声明了：
- `spring-boot-starter-data-jpa` 自动包含 Hibernate
- `spring-boot-starter-test` 自动包含 AssertJ

## 项目结构说明

本项目采用 **多模块 Maven 项目** 结构：

```
trae/
├── pom.xml                          # 根目录聚合 pom（新增）
├── .mvn/settings.xml               # 项目级别 Maven 配置（新增）
├── data-assimilation-platform/
│   └── service_spring/
│       └── pom.xml
├── data-assimilation-service/
│   └── pom.xml
├── meteor-forecast-service/
│   └── pom.xml
├── path-planning-service/
│   └── pom.xml
├── uav-platform-service/
│   └── pom.xml
├── wrf-processor-service/
│   └── pom.xml
└── uav-path-planning-system/
    └── backend-spring/
        └── pom.xml
```

## 解决方案

### 方案一：使用根目录 pom 统一构建（推荐）

在项目根目录执行：

```bash
# 1. 强制刷新所有模块依赖
mvn clean install -U -DskipTests

# 说明：
# -U: 强制更新 release 和 snapshot 依赖
# -DskipTests: 跳过测试以加快速度
```

### 方案二：使用自动化脚本

Windows 用户直接双击运行：
```
fix-maven-deps.bat
```

### 方案三：使用项目内置的 Maven 配置（自动应用阿里云镜像）

项目根目录已包含 `.mvn/settings.xml` 配置文件，使用阿里云 Maven 镜像源加速下载。

IDE 配置步骤：

1. **IntelliJ IDEA**:
   - File → Settings → Build, Execution, Deployment → Build Tools → Maven
   - User settings file: 勾选 Override，选择项目根目录 `.mvn/settings.xml`
   - Local repository: 可以保持默认或自定义
   - 点击 Apply → OK

2. **Eclipse**:
   - Window → Preferences → Maven → User Settings
   - User Settings: 选择项目根目录 `.mvn/settings.xml`
   - 点击 Apply and Close

### 方案四：配置用户级镜像源（如果不使用项目配置）

编辑 `~/.m2/settings.xml` 文件：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 
                              http://maven.apache.org/xsd/settings-1.0.0.xsd">
    <mirrors>
        <mirror>
            <id>aliyun</id>
            <mirrorOf>central</mirrorOf>
            <name>Aliyun Maven</name>
            <url>https://maven.aliyun.com/repository/public</url>
        </mirror>
    </mirrors>
</settings>
```

### 方案五：彻底清理缓存（极端情况）

如果以上方案都不行，尝试删除本地缓存：

1. 找到 Maven 本地仓库位置（通常在 `C:\Users\<你的用户名>\.m2\repository`）
2. 删除以下目录：
   - `org/hibernate/`
   - `org/assertj/`
   - `org/springframework/`
3. 重新运行方案一或方案二

## 验证步骤

1. 在 IDE 中刷新 Maven 项目（右键项目 → Maven → Reload Project）
2. 等待依赖索引重建完成
3. 检查 `problems_and_diagnostics` 面板，错误应该会消失

## 项目中的 pom.xml 文件

| 项目 | 位置 | Spring Boot 版本 | Java 版本 |
|------|------|------------------|-----------|
| wrf-processor-service | `wrf-processor-service/pom.xml` | 2.7.0 | 11 |
| meteor-forecast-service | `meteor-forecast-service/pom.xml` | 2.7.0 | 11 |
| path-planning-service | `path-planning-service/pom.xml` | 2.7.0 | 11 |
| uav-platform-service | `uav-platform-service/pom.xml` | 2.7.0 | 11 |
| data-assimilation-service | `data-assimilation-service/pom.xml` | 2.7.0 | 11 |
| uav-path-planning-system | `uav-path-planning-system/backend-spring/pom.xml` | 3.2.0 | 17 |

## 常见问题

**Q: 根目录 pom.xml 有什么用？**

A: 根目录 pom.xml 是聚合 pom，统一管理所有 Spring Boot 子模块的版本和依赖，方便一次性构建所有项目。

**Q: 为什么需要 .mvn/settings.xml？**

A: 项目级别的 Maven 配置，自动应用阿里云镜像源，解决国内下载速度慢的问题。

**Q: 如何在单个模块中构建？**

A: 可以进入各个服务目录执行 `mvn clean install -U -DskipTests`，也可以在根目录执行完整构建。
