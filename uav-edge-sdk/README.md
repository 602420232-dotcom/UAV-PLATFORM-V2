# UAV Edge SDK

无人机端侧 SDK，采用 **C++/Python 混合实现**，提供高性能的离线路径规划和气象风险评估功能。

## 📋 功能特性

- 🚀 **高性能**: 核心算法使用 C++ 实现（PyBind11），比纯 Python 快 10-100 倍
- 🐍 **易用性**: 提供纯 Python 封装，自动回退机制
- 📡 **飞控支持**: 支持 PX4/ArduPilot 通过 MAVLink 协议通信
- 🌦️ **气象评估**: 实时气象风险评估，支持批量评估
- 🗺️ **路径规划**: A* 算法实现，支持静态障碍物避障
- 🔧 **可扩展**: 模块化设计，易于扩展新功能

## 🏗️ 架构设计

```
uav-edge-sdk/
├── include/              # C++ 头文件
│   ├── path_planner.h    # 路径规划
│   ├── risk_assessor.h   # 风险评估
│   └── flight_controller.h # 飞控通信
├── src/                  # C++ 源文件
│   ├── path_planner.cpp
│   ├── risk_assessor.cpp
│   ├── flight_controller.cpp
│   └── bindings.cpp      # PyBind11 绑定
├── python/               # Python 封装层
│   ├── edge_sdk.py       # 主 SDK 类
│   ├── config.py         # 配置管理
│   ├── logger.py         # 日志模块
│   └── *_python.py       # 纯 Python 回退
├── tests/                # 测试文件
├── CMakeLists.txt        # CMake 构建配置
└── README.md
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- CMake 3.10+
- C++ 编译器 (GCC/MSVC/Clang)
- PyBind11

### 构建 C++ 模块

```bash
cd uav-edge-sdk

# 创建构建目录
mkdir build && cd build

# 配置 CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译
cmake --build . --config Release

# 安装到 python 目录
cmake --install .
```

### Windows (MSVC)

```bash
mkdir build && cd build
cmake .. -G "Visual Studio 16 2019" -A x64
cmake --build . --config Release
```

### Linux/macOS

```bash
mkdir build && cd build
cmake ..
make -j4
make install
```

### Python 使用

#### 基本用法

```python
from edge_sdk import EdgeSDK, create_sdk

# 创建 SDK 实例
sdk = EdgeSDK({
    'grid_width': 100,
    'grid_height': 100,
    'resolution': 1.0
})

# 路径规划
path = sdk.plan_path(
    start=(0, 0),
    goal=(50, 50),
    obstacles=[(10, 10), (10, 11)]
)

print(f"Path: {path}")

# 气象风险评估
weather = {
    'wind_speed': 8.0,         # m/s
    'wind_direction': 180,      # 度
    'temperature': 20.0,         # °C
    'humidity': 65.0,           # %
    'visibility': 10.0,          # km
    'precipitation': 0.0,       # mm/h
    'has_thunderstorm': False
}

assessment = sdk.assess_weather_risk(weather)
print(f"Risk: {assessment['level']} ({assessment['score']:.1f}/100)")
```

#### 飞控连接

```python
# 连接飞控
sdk.connect_flight_controller()

# 解锁
sdk.arm()

# 起飞到 10 米
sdk.takeoff(10.0)

# 上传任务
waypoints = [
    {'latitude': 31.23, 'longitude': 121.47, 'altitude': 20, 'speed': 10, 'action': True},
    {'latitude': 31.24, 'longitude': 121.48, 'altitude': 25, 'speed': 10, 'action': False}
]
sdk.upload_mission(waypoints)

# 执行任务
sdk.execute_mission()

# 降落
sdk.land()
```

### 纯 Python 回退

如果 C++ 模块未构建，SDK 会自动使用纯 Python 回退：

```python
# 自动检测，无需手动切换
from edge_sdk import EdgeSDK
sdk = EdgeSDK()  # 会自动选择 C++ 或 Python 实现
```

性能会有所下降，但功能完全一致。

## 📚 API 文档

### EdgeSDK 类

#### 路径规划

```python
sdk.plan_path(start, goal, obstacles=None)
```

- `start`: 起点坐标 `(x, y)`
- `goal`: 终点坐标 `(x, y)`
- `obstacles`: 障碍物列表 `[(x1, y1), (x2, y2), ...]`
- 返回: 路径点列表

#### 气象风险评估

```python
sdk.assess_weather_risk(weather)
```

- `weather`: 气象数据字典
  - `wind_speed`: 风速 (m/s)
  - `wind_direction`: 风向 (度)
  - `temperature`: 温度 (°C)
  - `humidity`: 湿度 (%)
  - `visibility`: 能见度 (km)
  - `precipitation`: 降水量 (mm/h)
  - `has_thunderstorm`: 是否有雷暴
- 返回: 风险评估字典
  - `level`: 风险等级 ('LOW', 'MEDIUM', 'HIGH', 'SEVERE')
  - `score`: 风险分数 (0-100)
  - `warnings`: 警告信息列表

#### 飞控控制

```python
sdk.connect_flight_controller()  # 连接飞控
sdk.disconnect_flight_controller()  # 断开连接
sdk.arm()  # 解锁
sdk.disarm()  # 上锁
sdk.takeoff(altitude)  # 起飞
sdk.land()  # 降落
sdk.return_to_launch()  # 返航
sdk.upload_mission(waypoints)  # 上传任务
sdk.execute_mission()  # 执行任务
sdk.get_uav_state()  # 获取无人机状态
```

## 🧪 测试

```bash
# 运行测试
cd tests
python test_edge_sdk.py

# 运行示例
cd python
python edge_sdk.py
```

## 📦 依赖

### C++ 依赖

- CMake 3.10+
- C++14 兼容编译器
- PyBind11 (自动下载或手动安装)

### Python 依赖

- Python 3.8+

## 📄 许可证

[Apache License 2.0](LICENSE)

## 👤 作者

**Dithiothreitol**

## 🙏 致谢

- 使用 [PyBind11](https://github.com/pybind/pybind11) 实现 C++/Python 绑定
- 参考 [A* 算法](https://en.wikipedia.org/wiki/A*_search_algorithm) 实现路径规划
- 参考 [MAVLink](https://mavlink.io/en/) 协议实现飞控通信
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
