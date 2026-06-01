# API 参考

## REST API

### 基础信息

- **Base URL**: `http://localhost:8000`
- **默认端口**: 8000 (FastAPI)
- **API 文档**: `http://localhost:8000/docs` (Swagger UI)
- **数据格式**: JSON

### 1. 执行同化

**接口**：`POST /assimilate`

执行贝叶斯数据同化计算。

**请求体**：

```json
{
  "algorithm": "3dvar",
  "background": {
    "grid": {"lat": [...], "lon": [...], "lev": [...]},
    "variables": {"temperature": [...], "wind_u": [...], "wind_v": [...]}
  },
  "observations": {
    "values": [...],
    "locations": [[lat, lon, lev], ...],
    "errors": [...]
  },
  "config": {
    "max_iterations": 10,
    "tolerance": 1e-6,
    "parallel": true
  }
}
```

**响应**：

```json
{
  "status": "success",
  "analysis": {"variables": {...}, "grid": {...}},
  "variance": {"values": [...], "grid": {...}},
  "metrics": {
    "rmse": 0.05,
    "reduction_rate": 0.35,
    "iterations": 5
  }
}
```

### 2. 质量控制

**接口**：`POST /quality-control`

**请求体**：

```json
{
  "data": {"temperature": [...], "wind_speed": [...]},
  "data_type": "wind_speed",
  "method": "iqr",
  "params": {"threshold": 3.0}
}
```

### 3. 风险评估

**接口**：`POST /risk-assessment`

**请求体**：

```json
{
  "wind_speed": [[...]],
  "turbulence": [[...]],
  "config": {
    "risk_threshold": 0.7,
    "output_heatmap": true
  }
}
```

### 4. 时间序列分析

**接口**：`POST /timeseries/analyze`

**请求体**：

```json
{
  "data": {"temperature": [...], "timestamp": [...]},
  "analysis_type": "trend",
  "params": {"seasonal_period": 24}
}
```

### 5. 健康检查

**接口**：`GET /health`

**响应**：

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "gpu_available": true,
  "memory_usage": "45%"
}
```

## CLI 接口

### 常用命令

```bash
# 运行同化
assimilate run --config config.yaml --input data.nc --output result.nc

# 质量控制
assimilate qc --input data.nc --output qc_result.nc

# 风险评估
assimilate risk --input analysis.nc --output risk_map.nc

# 可视化
assimilate visualize --input analysis.nc --output figure.png

# 启动 API 服务
assimilate serve --host 0.0.0.0 --port 8000
```

## Python API

### 核心类

```python
from bayesian_assimilation.core.assimilator import BayesianAssimilator

assim = BayesianAssimilator()
assim.initialize_grid(domain_size=(100, 100, 50))
assim.set_algorithm("3dvar", max_iterations=10)
result = assim.run(background, observations, obs_locations)
```

### 模型类

```python
from bayesian_assimilation.models.enkf import EnKF
from bayesian_assimilation.models.three_dimensional_var import ThreeDimensionalVar
from bayesian_assimilation.models.four_dimensional_var import FourDimensionalVar

# 3D-VAR
model_3dvar = ThreeDimensionalVar(max_iterations=10)

# 4D-VAR
model_4dvar = FourDimensionalVar(time_window=6, assimilation_window=3600)

# EnKF
enkf = EnKF(ensemble_size=50, inflation=1.05)
```

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |
| 503 | 服务暂不可用（资源不足） |
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
