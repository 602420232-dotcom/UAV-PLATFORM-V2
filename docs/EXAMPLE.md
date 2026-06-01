# 无人机路径规划系统使用示例

## 1. 系统部署

### 1.1 快速启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 1.2 服务访问地址

- API网关：http://localhost:8088/api
- 主平台服务：http://localhost:8080/api
- WRF处理服务：http://localhost:8081/api/wrf
- 贝叶斯同化服务：http://localhost:8084/api/assimilation
- 气象预测服务：http://localhost:8082/api/forecast
- 路径规划服务：http://localhost:8083/api/planning
- 气象收集服务：http://localhost:8086/api/weather
- 边云协同服务：http://localhost:8000/docs
- 前端界面：http://localhost:5173

## 2. 完整路径规划示例

### 2.1 前端操作流程

1. **登录系统**：访问前端界面，使用默认账号密码（admin/admin）登录

2. **进入路径规划页面**：点击左侧菜单中的"路径规划"

3. **配置任务点**：
   - 点击"添加任务点"按钮
   - 或在地图上点击添加任务点
   - 每个任务点包含位置、需求等信息

4. **选择无人机**：从下拉菜单中选择无人机数量和类型

5. **选择气象数据**：选择"最新数据"或"自定义数据"

6. **设置风险阈值**：调整风险阈值滑块，控制路径规划的安全性

7. **执行路径规划**：点击"执行路径规划"按钮

8. **查看结果**：
   - 地图上显示规划路径
   - 下方显示规划结果详情，包括无人机数量、任务点数量、总距离、总时间等
   - 查看每条路径的详细信息

### 2.2 API调用示例

#### 完整路径规划

```python
import requests
import json

url = "http://localhost:8080/api/platform/plan"

payload = {
    "droneCount": 2,
    "taskPoints": [
        {"id": 1, "lat": 39.9042, "lng": 116.4074, "demand": 1},
        {"id": 2, "lat": 39.9142, "lng": 116.4174, "demand": 2},
        {"id": 3, "lat": 39.9242, "lng": 116.4274, "demand": 1}
    ],
    "baseLocation": {"lat": 39.9042, "lng": 116.4074},
    "timeWindow": {"start": "2024-01-01T08:00:00", "end": "2024-01-01T18:00:00"},
    "riskThreshold": 3.0
}

response = requests.post(url, json=payload)
print(response.json())
```

#### 获取气象数据

```python
import requests

url = "http://localhost:8080/api/platform/weather"

params = {
    "time": "2024-01-01T12:00:00",
    "height": 100,
    "lat": 39.9042,
    "lng": 116.4074
}

response = requests.get(url, params=params)
print(response.json())
```

## 3. 贝叶斯同化服务使用示例

### 3.1 执行贝叶斯同化

```python
import requests
import json

url = "http://localhost:8084/api/assimilation/execute"

payload = {
    "jobId": "job-123",
    "algorithm": "three_dimensional_var",
    "background": {
        "grid": {
            "lat": [39.8, 39.9, 40.0],
            "lon": [116.3, 116.4, 116.5],
            "lev": [100, 200, 500]
        },
        "variables": {
            "temperature": [[[25.0, 25.5, 26.0], [25.2, 25.7, 26.2], [25.4, 25.9, 26.4]],
                           [[24.0, 24.5, 25.0], [24.2, 24.7, 25.2], [24.4, 24.9, 25.4]],
                           [[23.0, 23.5, 24.0], [23.2, 23.7, 24.2], [23.4, 23.9, 24.4]]]
        }
    },
    "observations": [
        {"lat": 39.9, "lon": 116.4, "lev": 200, "variable": "temperature", "value": 25.0, "error": 0.5}
    ],
    "config": {
        "max_iterations": 10,
        "tolerance": 1e-6,
        "parallel": true
    }
}

response = requests.post(url, json=payload)
print(response.json())
```

### 3.2 获取方差场

```python
import requests
import json

url = "http://localhost:8084/api/assimilation/variance"

payload = {
    "background": {
        "grid": {
            "lat": [39.8, 39.9, 40.0],
            "lon": [116.3, 116.4, 116.5],
            "lev": [100, 200, 500]
        }
    },
    "observations": [
        {"lat": 39.9, "lon": 116.4, "lev": 200, "variable": "temperature", "value": 25.0, "error": 0.5}
    ],
    "config": {
        "correlation_length": 10000,
        "vertical_correlation": 500
    }
}

response = requests.post(url, json=payload)
print(response.json())
```

## 4. 气象预测服务使用示例

### 4.1 执行气象预测

```python
import requests
import json

url = "http://localhost:8082/api/forecast/predict"

payload = {
    "model": "lstm_xgboost",
    "inputData": {
        "timeSteps": ["2024-01-01T00:00:00", "2024-01-01T03:00:00", "2024-01-01T06:00:00"],
        "variables": {
            "temperature": [25.0, 24.5, 24.0],
            "humidity": [60, 65, 70],
            "windSpeed": [5.0, 4.5, 4.0]
        }
    },
    "forecastHours": 24
}

response = requests.post(url, json=payload)
print(response.json())
```

## 5. 路径规划服务使用示例

### 5.1 执行VRPTW任务调度

```python
import requests
import json

url = "http://localhost:8083/api/planning/vrptw"

payload = {
    "vehicles": [
        {"id": 1, "capacity": 10, "speed": 10},
        {"id": 2, "capacity": 10, "speed": 10}
    ],
    "customers": [
        {"id": 1, "lat": 39.9142, "lng": 116.4174, "demand": 2, "timeWindow": {"start": 0, "end": 3600}},
        {"id": 2, "lat": 39.9242, "lng": 116.4274, "demand": 1, "timeWindow": {"start": 0, "end": 3600}},
        {"id": 3, "lat": 39.9342, "lng": 116.4374, "demand": 3, "timeWindow": {"start": 0, "end": 3600}}
    ],
    "depot": {"lat": 39.9042, "lng": 116.4074}
}

response = requests.post(url, json=payload)
print(response.json())
```

### 5.2 执行完整路径规划

```python
import requests
import json

url = "http://localhost:8083/api/planning/full"

payload = {
    "droneCount": 2,
    "taskPoints": [
        {"id": 1, "lat": 39.9142, "lng": 116.4174, "demand": 2},
        {"id": 2, "lat": 39.9242, "lng": 116.4274, "demand": 1},
        {"id": 3, "lat": 39.9342, "lng": 116.4374, "demand": 3}
    ],
    "baseLocation": {"lat": 39.9042, "lng": 116.4074},
    "timeWindow": {"start": "2024-01-01T08:00:00", "end": "2024-01-01T18:00:00"},
    "weatherData": {
        "windSpeed": 5.0,
        "windDirection": 135,
        "temperature": 25.5,
        "humidity": 65,
        "turbulence": "低",
        "visibility": 10,
        "risk": "低"
    }
}

response = requests.post(url, json=payload)
print(response.json())
```

## 6. 系统监控

### 6.1 访问监控页面

1. 登录系统后，点击左侧菜单中的"系统监控"
2. 查看系统状态、服务状态、算法性能等信息
3. 查看系统负载趋势图表
4. 查看最近任务执行情况

### 6.2 监控API

```python
import requests

# 获取系统状态
url = "http://localhost:8080/api/platform/status"
response = requests.get(url)
print(response.json())

# 获取服务健康状态
url = "http://localhost:8080/api/platform/health"
response = requests.get(url)
print(response.json())
```

## 7. 数据管理

### 7.1 任务管理

```python
import requests
import json

# 创建任务
url = "http://localhost:8080/api/platform/task"
payload = {
    "name": "配送任务",
    "description": "城市末端配送",
    "taskPoints": [
        {"id": 1, "lat": 39.9142, "lng": 116.4174, "demand": 2},
        {"id": 2, "lat": 39.9242, "lng": 116.4274, "demand": 1}
    ],
    "startTime": "2024-01-01T08:00:00",
    "endTime": "2024-01-01T18:00:00"
}
response = requests.post(url, json=payload)
print(response.json())

# 获取任务列表
url = "http://localhost:8080/api/platform/task"
response = requests.get(url)
print(response.json())
```

### 7.2 无人机管理

```python
import requests
import json

# 获取无人机列表
url = "http://localhost:8080/api/platform/drones"
response = requests.get(url)
print(response.json())

# 添加无人机
url = "http://localhost:8080/api/platform/drones"
payload = {
    "id": 3,
    "name": "无人机3",
    "model": "DJI Mavic 3",
    "maxSpeed": 20,
    "maxLoad": 5,
    "batteryCapacity": 5000,
    "status": "available"
}
response = requests.post(url, json=payload)
print(response.json())
```

## 8. 常见问题解决

### 8.1 服务启动失败

- 检查Docker服务是否正常运行
- 检查端口是否被占用
- 检查数据库连接配置
- 查看服务日志：`docker-compose logs <服务名>`

### 8.2 路径规划失败

- 检查任务点是否合理
- 检查无人机数量是否足够
- 检查时间窗设置是否合理
- 检查气象数据是否有效

### 8.3 气象数据加载失败

- 检查WRF文件是否存在
- 检查WRF文件格式是否正确
- 检查服务配置是否正确

### 8.4 性能优化

- 启用Redis缓存
- 调整Dask集群配置
- 优化数据库索引
- 调整算法参数

## 9. 高级功能

### 9.1 自定义算法配置

```python
import requests
import json

# 自定义贝叶斯同化配置
url = "http://localhost:8084/api/assimilation/execute"
payload = {
    "jobId": "custom-job",
    "algorithm": "hybrid",
    "config": {
        "three_dimensional_var": {
            "max_iterations": 20,
            "tolerance": 1e-8
        },
        "enkf": {
            "ensemble_size": 50,
            "inflation": 1.05
        },
        "hybrid_weight": 0.7
    }
    # 其他参数...
}
response = requests.post(url, json=payload)
print(response.json())
```

### 9.2 批量处理

```python
import requests
import json

# 批量执行贝叶斯同化
url = "http://localhost:8084/api/assimilation/batch"
payload = {
    "jobs": [
        {
            "jobId": "job-1",
            "algorithm": "three_dimensional_var",
            # 其他参数...
        },
        {
            "jobId": "job-2",
            "algorithm": "enkf",
            # 其他参数...
        }
    ]
}
response = requests.post(url, json=payload)
print(response.json())
```

## 10. 系统集成

### 10.1 与第三方系统集成

```python
# 示例：与物流系统集成
import requests
import json

def integrate_with_logistics():
    # 从物流系统获取订单
    logistics_url = "http://logistics-system/api/orders"
    orders = requests.get(logistics_url).json()
    
    # 转换为任务点
    task_points = []
    for order in orders:
        task_points.append({
            "id": order["id"],
            "lat": order["deliveryAddress"]["lat"],
            "lng": order["deliveryAddress"]["lng"],
            "demand": order["items"]["count"]
        })
    
    # 执行路径规划
    planning_url = "http://localhost:8080/api/platform/plan"
    payload = {
        "droneCount": 3,
        "taskPoints": task_points,
        "baseLocation": {"lat": 39.9042, "lng": 116.4074},
        "timeWindow": {"start": "2024-01-01T08:00:00", "end": "2024-01-01T18:00:00"}
    }
    result = requests.post(planning_url, json=payload).json()
    
    # 将规划结果返回给物流系统
    logistics_callback_url = "http://logistics-system/api/planning-result"
    requests.post(logistics_callback_url, json=result)

# 执行集成
integrate_with_logistics()
```

### 10.2 WebSocket实时通信

前端可以通过WebSocket与后端建立实时通信，获取任务执行状态和路径更新：

```javascript
// 前端WebSocket连接
const ws = new WebSocket('ws://localhost:8080/api/ws');

ws.onopen = function() {
    console.log('WebSocket连接已建立');
    // 订阅任务状态
    ws.send(JSON.stringify({ type: 'subscribe', taskId: 'task-123' }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'taskUpdate') {
        // 更新任务状态
        updateTaskStatus(data.task);
    } else if (data.type === 'pathUpdate') {
        // 更新路径显示
        updatePathDisplay(data.path);
    }
};

ws.onclose = function() {
    console.log('WebSocket连接已关闭');
};
```

## 11. 总结

本系统提供了完整的无人机路径规划解决方案，包括：

- **气象数据处理**：基于WRF模型的气象数据解析和处理
- **贝叶斯同化**：多源数据融合和不确定性评估
- **气象预测**：基于LSTM+XGBoost的气象预测和订正
- **路径规划**：三层路径规划架构（VRPTW、A*、DWA）
- **系统监控**：实时监控系统状态和性能
- **用户界面**：直观的Web前端界面

通过本示例文档，您可以快速了解系统的使用方法和集成方式，为您的无人机应用场景提供有力支持。
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
