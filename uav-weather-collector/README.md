# 无人机气象信息收集模块

## 概述

无人机气象信息收集模块（uav-weather-collector），对接多源气象数据，为路径规划提供实时气象数据支撑。

## 技术栈

- **框架**: Spring Boot 3.2.0
- **语言**: Java 17
- **构建工具**: Maven
- **服务发现**: Nacos
- **存储**: MySQL + Redis

## 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/weather/collect/uav` | POST | 采集无人机传感器数据 |
| `/api/weather/collect/wrf` | POST | 采集WRF预报数据 |
| `/api/weather/collect/ground` | POST | 采集地面站数据 |
| `/api/weather/drone/{id}` | GET | 获取无人机实时气象 |
| `/api/weather/drone/{id}/history` | GET | 获取气象历史(默认10分钟) |
| `/api/weather/fusion/{id}` | GET | 获取多源融合气象 |
| `/api/weather/alert` | POST | 气象告警评估 |
| `/api/weather/alerts/{id}` | GET | 获取告警记录 |
| `/api/weather/sources` | GET | 获取数据源列表 |

## 配置

详见 `src/main/resources/application.yml`。

## 构建与运行

```bash
# 构建
mvn clean package -DskipTests -pl uav-weather-collector -am

# 运行
mvn spring-boot:run -pl uav-weather-collector
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
