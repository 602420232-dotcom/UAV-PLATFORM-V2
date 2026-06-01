# Data Assimilation Platform 服务文档

## 概述

Data Assimilation Platform（数据同化平台）是一个独立的Python微服务模块，提供贝叶斯数据同化的核心算法实现。该服务运行在独立端口8094，与Java微服务通过REST API进行通信。

## 服务架构

```
┌──────────────────────────────────────────────────────────────┐
│                 Java微服务层 (8080-8088)                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐              │
│  │ Platform   │  │ WRF        │  │ Meteor     │              │
│  │ Service    │  │ Processor  │  │ Forecast   │              │
│  └────────────┘  └────────────┘  └────────────┘              │
│          │                 │                 │                │
│          └─────────────────┼─────────────────┘                │
│                            │                                  │
├────────────────────────────┼──────────────────────────────────┤
│           Data Assimilation Platform (8094)                   │
│     ┌──────────────────────────────────────────────┐         │
│     │             FastAPI应用层                     │         │
│     ├────────────────┬────────────┬────────────────┤         │
│     │ Assimilation   │ Batch      │ Monitoring     │         │
│     │ API            │ API        │ API            │         │
│     └────────────────┴────────────┴────────────────┘         │
│     ┌──────────────────────────────────────────────┐         │
│     │             Service层                         │         │
│     └──────────────────────────────────────────────┘         │
│                            │                                  │
│     ┌──────────────────────────────────────────────┐         │
│     │        Bayesian Assimilation Core             │         │
│     ├──────────────┬──────────────┬─────────────────┤         │
│     │   3D-VAR     │   4D-VAR     │      EnKF       │         │
│     └──────────────┴──────────────┴─────────────────┘         │
│     ┌──────────────────────────────────────────────┐         │
│     │          数据处理与基础设施                    │         │
│     ├──────────────┬──────────────┬─────────────────┤         │
│     │ 并行计算     │ 硬件加速     │ 可视化/存储     │         │
│     └──────────────┴──────────────┴─────────────────┘         │
└──────────────────────────────────────────────────────────────┘
```

## 端口配置

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `PORT` | `8094` | 服务监听端口 |
| `PYTHON_PATH` | `/app/python` | Python脚本路径 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `MAX_WORKERS` | `4` | 最大工作线程数 |
| `TIMEOUT` | `300` | 请求超时时间（秒） |

## API端点

### 1. 同化执行接口

**POST** `/api/assimilation/execute`

执行单次数据同化。

**请求参数**:
```json
{
  "method": "3dvar|enkf|hybrid",
  "background_field": "base64编码的numpy数组",
  "observations": [
    {
      "location": [lat, lon, level],
      "value": 23.5,
      "error_variance": 0.1
    }
  ],
  "config": {
    "max_iterations": 100,
    "convergence_threshold": 1e-6
  }
}
```

**响应**:
```json
{
  "status": "success",
  "analysis_field": "base64编码的分析场",
  "cost_function_value": 0.023,
  "iterations": 45,
  "computation_time_ms": 1250
}
```

### 2. 批量处理接口

**POST** `/api/assimilation/batch`

提交批量同化任务。

**请求参数**:
```json
{
  "tasks": [
    {
      "task_id": "task_001",
      "method": "3dvar",
      "background_field": "base64...",
      "observations": [...]
    }
  ],
  "priority": "normal|high"
}
```

**响应**:
```json
{
  "batch_id": "batch_12345",
  "status": "queued",
  "estimated_completion": "2026-05-09T10:15:00Z"
}
```

**查询任务状态**:
```
GET /api/assimilation/batch/{batch_id}
GET /api/assimilation/batch/{batch_id}/task/{task_id}
```

### 3. 监控接口

**GET** `/api/assimilation/monitoring/stats`

获取运行时统计信息。

**响应**:
```json
{
  "uptime_seconds": 3600,
  "total_requests": 150,
  "active_requests": 3,
  "average_latency_ms": 450,
  "error_rate": 0.02
}
```

---

> **最后更新**: 2026-06-01  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL