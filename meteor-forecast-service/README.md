# 气象预测服务

## 概述

气象预测服务基于 CLSTM 和 XGBoost 模型，通过分析历史气象数据进行预测和订正，为路径规划提供高精度的气象预报数据。

## 技术栈

- **框架**: Spring Boot 3.2.0
- **语言**: Java 17 + Python 3.8+
- **构建工具**: Maven
- **AI模型**: LSTM + XGBoost + GPR + ConvLSTM
- **算法引擎**: Python (meteor_forecast.py, mlops_pipeline.py)

## 服务信息

- **服务端口**: 8082
- **服务名称**: meteor-forecast-service

## 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/forecast/predict` | POST | 执行气象预测 |
| `/api/forecast/correct` | POST | 执行气象数据订正 |
| `/api/forecast/models` | GET | 获取可用模型列表 |

## Python 依赖

| 包 | 版本 | 用途 |
|---|------|------|
| tensorflow | >=2.9.0 | LSTM/ConvLSTM 深度学习 |
| xgboost | >=1.5.0 | XGBoost 气象订正 |
| scikit-learn | >=1.0.0 | GPR 高斯过程回归 |
| numpy | >=1.24.0 | 数值计算 |
| pandas | >=2.0.0 | 数据处理 |

## 模型文件

预训练模型文件存放路径：`src/main/python/models/`
- `lstm_model.h5` - LSTM 时间序列预测模型
- `xgb_model.json` - XGBoost 数据订正模型
- `gpr_model.pkl` - GPR 高斯过程回归模型

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_PASSWORD` | （必填） | 数据库密码 |
| `forecast.python-script` | `src/main/python/meteor_forecast.py` | Python 脚本路径 |
| `SERVER_PORT` | `8082` | 服务端口 |

## 构建与运行

```bash
# 构建
mvn clean package -DskipTests

# 运行
mvn spring-boot:run
```

## 配置

详见 `src/main/resources/application.yml`。
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
