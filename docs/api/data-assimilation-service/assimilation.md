# 贝叶斯同化服务API

贝叶斯同化服务提供数据同化计算，融合多源气象观测数据。

## 接口列表

### 1. 执行贝叶斯同化

**接口地址**：`POST /api/assimilation/execute`

**功能**：执行贝叶斯同化

**请求参数**：JSON
```json
{
  "background": {...},
  "observations": {...},
  "method": "hybrid"
}
```

**响应**：
```json
{
  "success": true,
  "data": { "analysis": {...}, "uncertainty": {...} }
}
```

### 2. 计算方差场

**接口地址**：`POST /api/assimilation/variance`

**功能**：计算方差场

**请求参数**：JSON
```json
{
  "background": {...},
  "observations": {...}
}
```

**响应**：
```json
{
  "success": true,
  "data": { "variance": {...} }
}
```

### 3. 批量执行同化

**接口地址**：`POST /api/assimilation/batch`

**功能**：批量执行同化

**请求参数**：JSON
```json
{
  "tasks": [...]
}
```

**响应**：
```json
{
  "success": true,
  "data": { "results": [...] }
}
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
