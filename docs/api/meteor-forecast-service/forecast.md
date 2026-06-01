# 气象预测服务API

气象预测服务提供气象数据的预测和订正功能，使用LSTM和XGBoost模型进行气象预测。

## 接口列表

### 1. 执行气象预测

**接口地址**：`POST /api/forecast/predict`

**功能**：执行气象预测

**请求参数**：JSON
```json
{
  "data": [...],
  "method": "lstm"
}
```

**响应**：
```json
{
  "success": true,
  "data": { "predictions": [...] }
}
```

### 2. 气象数据订正

**接口地址**：`POST /api/forecast/correct`

**功能**：执行气象数据订正

**请求参数**：JSON
```json
{
  "forecast_data": [...],
  "observed_data": [...]
}
```

**响应**：
```json
{
  "success": true,
  "data": { "corrected": [...] }
}
```

### 3. 获取可用模型列表

**接口地址**：`GET /api/forecast/models`

**功能**：获取可用模型列表

**响应**：
```json
{
  "success": true,
  "data": { "models": ["lstm", "xgboost", "convlstm", "gpr"] }
}
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
