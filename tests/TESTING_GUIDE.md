# 测试合规检查脚本

本目录包含以下测试与质量检查脚本：

## 测试脚本

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `check_syntax.py` | Python语法检查 | `python check_syntax.py` |
| `check_security.py` | 安全漏洞扫描 | `python check_security.py` |
| `check_imports.py` | 无用导入检查 | `python check_imports.py` |
| `check_system.py` | 系统完整性检查 | `python check_system.py` |

## 单元测试

Java单元测试通过Maven Surefire执行：

```bash
# 运行所有测试
mvn test

# 运行特定模块测试
mvn test -pl common-utils -am

# 生成覆盖率报告
mvn jacoco:report

# 检查覆盖率阈值（80% line, 70% branch）
mvn jacoco:check
```

## 测试覆盖率要求

| 模块 | Line覆盖率 | Branch覆盖率 |
|------|:--------:|:----------:|
| common-utils | 90%+ | 80%+ |
| api-gateway | 85%+ | 75%+ |
| wrf-processor-service | 85%+ | 75%+ |
| meteor-forecast-service | 85%+ | 75%+ |
| path-planning-service | 85%+ | 75%+ |
| data-assimilation-service | 85%+ | 75%+ |
| uav-platform-service | 80%+ | 70%+ |
| uav-path-planning-system | 80%+ | 70%+ |
| uav-weather-collector | 80%+ | 70%+ |
| data-assimilation-platform | 80%+ | 70%+ |

## CI/CD集成

测试在GitHub Actions中自动运行，每次push都会执行：

1. `mvn test` - 单元测试
2. `python check_security.py` - 安全扫描
3. `mvn jacoco:check` - 覆盖率检查
4. `mvn dependency-check:check` - 依赖漏洞扫描

## 新增测试规范

1. 测试类使用`@DisplayName`注解描述测试目的
2. 每个测试方法使用`@DisplayName`描述场景
3. 遵循AAA模式：Arrange-Act-Assert
4. 测试需要独立、可重复
5. Mock外部依赖，使用Mockito

## 测试文件清单

```
src/test/java/com/uav/common/exception/ExceptionTests.java
src/test/java/com/uav/common/dto/AssimilationRequestTest.java
src/test/java/com/uav/common/dto/DtoValidationTests.java
src/test/java/com/uav/common/utils/PythonExecutorTest.java
src/test/java/com/uav/common/utils/PythonScriptInvokerTest.java
src/test/java/com/uav/common/config/ConfigTests.java
src/test/java/com/wrf/processor/controller/WrfControllerTest.java
src/test/java/com/wrf/processor/controller/WrfControllerEnhancedTest.java
src/test/java/com/meteor/forecast/controller/ForecastControllerTest.java
src/test/java/com/path/planning/controller/PlanningControllerTest.java
src/test/java/com/assimilation/service/controller/AssimilationControllerTest.java
src/test/java/com/uav/controller/AuthControllerTest.java
src/test/java/com/uav/controller/UserControllerTest.java
src/test/java/com/uav/controller/PathPlanningControllerTest.java
src/test/java/com/uav/controller/PlatformControllerTests.java
src/test/java/com/uav/config/JwtUtilTest.java
src/test/java/com/uav/config/SecurityConfigTest.java
src/test/java/com/uav/model/ModelTests.java
src/test/java/com/uav/utils/PythonAlgorithmUtilTest.java
src/test/java/com/uav/gateway/GatewayTests.java
src/test/java/com/uav/weather/WeatherCollectorTests.java
src/test/java/com/bayesian/DataAssimilationModelTests.java
src/test/java/com/bayesian/config/DataAssimilationConfigTests.java
src/test/java/com/bayesian/controller/DataAssimilationControllerTests.java
src/test/java/com/bayesian/resilience/ResilienceTest.java
```


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
