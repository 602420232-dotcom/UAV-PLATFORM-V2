# UAV Edge SDK (C++)

> 无人机边缘计算 C++ SDK -- 在机载计算平台上实现路径规划、风险评估、模型推理、V2X 通信和联邦学习

## 1. 概述

UAV Edge SDK 是面向低空无人机边缘计算场景的 C++17 SDK，运行在机载计算平台（如 NVIDIA Jetson、树莓派 5 等）上，提供以下核心能力：

- **全局路径规划**：A* / RRT* 算法，支持障碍物和禁飞区
- **局部避障**：DWA (Dynamic Window Approach) 实时避障
- **路径平滑**：Bezier 曲线 / Catmull-Rom 样条 / Douglas-Peucker 简化
- **航迹跟踪**：PID 控制器实时修正飞行偏差
- **风险评估**：基于气象参数的定量风险评估
- **模型推理**：ONNX Runtime 高性能推理（支持 FP32/FP16/INT8）
- **V2X 通信**：DSRC (IEEE 802.11p) / C-V2X 通信
- **联邦学习**：边缘端本地训练与模型更新上传（FedAvg / FedProx）
- **离线缓存**：本地数据持久化，支持断网运行
- **飞控通信**：MAVLink v2 协议，兼容 PX4 / ArduPilot

### 1.1 架构

```
+---------------------------------------------------------------+
|                    UAV Edge Application                        |
+---------------------------------------------------------------+
|  FlightController  |  PathPlanner  |  DWAPlanner             |
|  (MAVLink v2)      |  (A*/RRT*)    |  (Local Avoidance)      |
+---------------------------------------------------------------+
|  PathSmoother  |  TrajectoryCorrector  |  RiskAssessor         |
|  (Bezier/Catmull-Rom)  |  (PID)      |  (Weather Risk)        |
+---------------------------------------------------------------+
|  ModelRuntime (ONNX)  |  V2XClient (DSRC/C-V2X)               |
|  FederatedClient     |  OfflineCache  |  EdgeConfig           |
+---------------------------------------------------------------+
|              OS / Hardware (Jetson / RPi5 / x86)               |
+---------------------------------------------------------------+
```

## 2. 编译指南

### 2.1 依赖

| 依赖 | 最低版本 | 用途 | 是否必须 |
|------|---------|------|---------|
| CMake | 3.16+ | 构建系统 | 是 |
| C++17 编译器 | GCC 8 / Clang 7 / MSVC 2019 | C++17 支持 | 是 |
| ONNX Runtime | 1.14+ | 模型推理后端 | 可选（缺失时 stub 化） |
| nlohmann/json | 3.11+ | JSON 配置解析 | 可选（缺失时功能受限） |

### 2.2 编译步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-org/uav-platform-v2.git
cd uav-platform-v2/edge-sdk/cpp

# 2. 安装依赖（Ubuntu/Debian）
sudo apt-get install -y cmake g++ libonnxruntime-dev nlohmann-json3-dev

# 3. 配置与构建
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# 4. 安装（可选）
sudo make install
# 头文件安装到 /usr/local/include/uav_edge/
# 库文件安装到 /usr/local/lib/
```

### 2.3 交叉编译（ARM64 / Jetson）

```bash
# 安装 ARM64 交叉编译工具链
sudo apt-get install -y gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

# 配置 CMake 交叉编译
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_SYSTEM_NAME=Linux \
  -DCMAKE_SYSTEM_PROCESSOR=aarch64 \
  -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc \
  -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++ \
  -DONNXRuntime_ROOT=/path/to/onnxruntime-arm64

make -j$(nproc)
```

### 2.4 CMake 选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `CMAKE_BUILD_TYPE` | `Release` | 构建类型（Debug/Release/RelWithDebInfo） |
| `UAV_EDGE_BUILD_TESTS` | `OFF` | 是否编译单元测试（需要 GTest） |

### 2.5 编译宏

| 宏 | 说明 |
|----|------|
| `UAV_EDGE_HAS_ONNXRUNTIME` | ONNX Runtime 可用时自动定义，启用模型推理 |
| `UAV_EDGE_HAS_JSON` | nlohmann_json 可用时自动定义，启用 JSON 配置 |

## 3. API 参考

### 3.1 核心类一览

| 类/接口 | 头文件 | 说明 |
|---------|--------|------|
| `uav::edge::initialize()` / `shutdown()` | `<uav_edge/uav_edge.h>` | SDK 全局初始化与清理 |
| `AStarPlanner` | `<uav_edge/path_planner.h>` | A* 栅格路径规划器 |
| `RRTStarPlanner` | `<uav_edge/path_planner.h>` | RRT* 采样路径规划器 |
| `DWAPlanner` | `<uav_edge/dwa_planner.h>` | DWA 局部避障规划器 |
| `PathSmoother` | `<uav_edge/path_smoother.h>` | 路径平滑（Bezier/Catmull-Rom/Douglas-Peucker） |
| `TrajectoryCorrector` | `<uav_edge/trajectory_corrector.h>` | PID 航迹跟踪修正 |
| `FlightController` | `<uav_edge/flight_controller.h>` | MAVLink v2 飞控通信 |
| `WeatherRiskAssessor` | `<uav_edge/risk_assessor.h>` | 气象风险定量评估 |
| `DSRCClient` | `<uav_edge/v2x_client.h>` | DSRC V2X 通信客户端 |
| `FederatedClient` | `<uav_edge/federated_client.h>` | 联邦学习边缘端客户端 |
| `ONNXRuntime` | `<uav_edge/model_runtime.h>` | ONNX 模型推理运行时 |
| `OfflineCache` | `<uav_edge/offline_cache.h>` | 本地数据持久化与离线缓存 |
| `EdgeConfig` | `<uav_edge/config.h>` | JSON 配置管理 |

### 3.2 SDK 初始化

```cpp
#include <uav_edge/uav_edge.h>

// 使用默认配置初始化
uav::edge::initialize();

// 使用配置文件初始化
uav::edge::initialize("/path/to/edge_config.json");

// 检查初始化状态
if (uav::edge::is_initialized()) {
    // ...
}

// 清理资源
uav::edge::shutdown();
```

### 3.3 路径规划

```cpp
#include <uav_edge/path_planner.h>

using namespace uav::edge;

// 创建 A* 规划器（栅格分辨率 1.0m）
auto planner = create_path_planner("astar");
// 或创建 RRT* 规划器
// auto planner = create_path_planner("rrt_star");

// 设置障碍物
std::vector<Obstacle> obstacles = {
    {{100, 200, 50}, 10.0, 30.0, "building"}
};
planner->set_obstacles(obstacles);

// 设置禁飞区
std::vector<std::vector<Position>> no_fly_zones = {
    {{0, 0, 0}, {500, 0, 0}, {500, 500, 0}, {0, 500, 0}}
};
planner->set_no_fly_zones(no_fly_zones);

// 执行路径规划
Position start{0, 0, 50};
Position goal{1000, 1000, 80};
auto waypoints = planner->plan(start, goal, 120.0, 10.0);

// 验证路径
if (planner->validate_path(waypoints)) {
    printf("Planning time: %.2f ms\n", planner->last_planning_time_ms());
}
```

### 3.4 DWA 局部避障

```cpp
#include <uav_edge/dwa_planner.h>

using namespace uav::edge;

DWAPlanner dwa;
DWAParams params;
params.predict_time = 3.0;
params.v_max = 5.0;
params.obstacle_radius = 0.5;
dwa.set_params(params);

// 实时避障规划
Trajectory traj = dwa.plan(
    current_pos,    // 当前位置
    current_yaw,    // 当前朝向
    current_v,      // 当前线速度
    current_w,      // 当前角速度
    goal_pos,       // 目标位置
    obstacles       // 障碍物列表
);

if (traj.is_valid) {
    // 使用 traj.v 和 traj.w 作为速度控制指令
}
```

### 3.5 风险评估

```cpp
#include <uav_edge/risk_assessor.h>

using namespace uav::edge;

auto assessor = create_risk_assessor("weather");

WeatherData weather;
weather.wind_speed = 12.5;
weather.visibility = 1500.0;
weather.precipitation = 3.0;

FlightPlan plan;
plan.waypoints = { ... };

auto result = assessor->assess(weather, obstacles, plan);
printf("Risk Level: %d, Score: %.2f\n", (int)result.level, result.score);
// RiskLevel: 0=Low, 1=Medium, 2=High, 3=Critical
```

### 3.6 模型推理

```cpp
#include <uav_edge/model_runtime.h>

using namespace uav::edge;

#ifdef UAV_EDGE_HAS_ONNXRUNTIME
auto runtime = create_model_runtime("onnxruntime");
runtime->set_device("CUDA");
runtime->set_num_threads(4);
runtime->set_precision(InferencePrecision::FP16);

if (runtime->load_model("/models/weather_forecast.onnx")) {
    std::vector<Tensor> inputs = {
        { {1, 3, 224, 224}, input_data, "float32" }
    };
    auto result = runtime->infer(inputs);
    printf("Inference time: %.2f ms\n", result.inference_time_ms);
}
#endif
```

### 3.7 V2X 通信

```cpp
#include <uav_edge/v2x_client.h>

using namespace uav::edge;

auto v2x = create_v2x_client(V2XTechnology::DSRC, "uav-001");
v2x->initialize(R"({"channel": 178, "tx_power": 20.0})");
v2x->start();

// 注册消息回调
v2x->on_message_received([](const V2XMessage& msg) {
    printf("Received from %s\n", msg.sender_id.c_str());
});

// 广播位置信息
V2XMessage msg;
msg.sender_id = "uav-001";
msg.sender_position = {100, 200, 50};
v2x->broadcast(msg);

// 评估信道质量
auto quality = v2x->evaluate_channel({500, 500, 50});
printf("SNR: %.1f dB, Latency: %.1f ms\n", quality.snr, quality.latency_ms);
```

### 3.8 联邦学习

```cpp
#include <uav_edge/federated_client.h>

using namespace uav::edge;

auto client = create_federated_client("uav-001");
client->initialize(R"({"aggregation": "fedprox", "mu": 0.01})");
client->set_local_dataset_path("/data/local_flight_data");

if (client->connect("https://fl-server.uav-platform.com:8443")) {
    // 执行一轮联邦学习
    auto update = client->federated_round(5, 0.001);
    printf("Loss: %.4f, Samples: %u\n", update.loss, update.num_samples);
}
```

### 3.9 离线缓存

```cpp
#include <uav_edge/offline_cache.h>

using namespace uav::edge;

OfflineCache cache("/data/offline_cache");

// 缓存路径规划结果
cache.cache_path("route_A_to_B", waypoints);

// 读取缓存
auto cached = cache.get_cached_path("route_A_to_B");

// 缓存气象数据
WeatherData weather = { ... };
cache.cache_weather("station_001", weather);

// 检查缓存状态
printf("Cached paths: %d\n", cache.count(CacheType::PathPlan));
```

### 3.10 飞控通信

```cpp
#include <uav_edge/flight_controller.h>

using namespace uav::edge;

FlightController fc("serial", "/dev/ttyACM0:57600");

if (fc.connect()) {
    fc.arm();
    fc.takeoff(50.0);  // 起飞到 50m

    // 上传并执行任务
    fc.upload_mission(waypoints);
    fc.execute_mission();

    // 监听状态
    fc.on_state_changed([](const UAVState& state) {
        printf("Pos: (%.1f, %.1f, %.1f) Bat: %.1f%%\n",
               state.position.x, state.position.y, state.position.z,
               state.battery_percent);
    });
}
```

## 4. 集成示例 -- 无人机端完整集成

以下示例展示在无人机机载计算平台上集成 Edge SDK 的典型步骤：

```cpp
#include <uav_edge/uav_edge.h>
#include <uav_edge/path_planner.h>
#include <uav_edge/dwa_planner.h>
#include <uav_edge/path_smoother.h>
#include <uav_edge/trajectory_corrector.h>
#include <uav_edge/risk_assessor.h>
#include <uav_edge/flight_controller.h>
#include <uav_edge/offline_cache.h>
#include <uav_edge/model_runtime.h>
#include <uav_edge/v2x_client.h>

#include <iostream>
#include <thread>
#include <chrono>

int main() {
    // 1. 初始化 SDK
    uav::edge::initialize("/config/edge_config.json");

    // 2. 创建各组件
    auto planner = uav::edge::create_path_planner("rrt_star");
    uav::edge::DWAPlanner dwa;
    uav::edge::PathSmoother smoother;
    uav::edge::TrajectoryCorrector corrector;
    auto assessor = uav::edge::create_risk_assessor("weather");
    uav::edge::OfflineCache cache("/data/offline_cache");
    auto v2x = uav::edge::create_v2x_client(
        uav::edge::V2XTechnology::DSRC, "uav-001"
    );

    // 3. 连接飞控
    uav::edge::FlightController fc("serial", "/dev/ttyACM0:57600");
    if (!fc.connect()) {
        std::cerr << "Failed to connect flight controller" << std::endl;
        return 1;
    }

    // 4. 起飞
    fc.arm();
    fc.takeoff(50.0);

    // 5. 全局路径规划
    uav::edge::Position start{0, 0, 50};
    uav::edge::Position goal{1000, 1000, 80};
    auto waypoints = planner->plan(start, goal);

    // 6. 路径平滑
    auto smooth_path = smoother.bezier_smooth(waypoints, 5);

    // 7. 设置航迹跟踪
    corrector.set_path(smooth_path);

    // 8. 启动 V2X 通信
    v2x->initialize(R"({"channel": 178})");
    v2x->start();
    v2x->on_message_received([](const uav::edge::V2XMessage& msg) {
        // 处理来自其他 UAV 的消息
    });

    // 9. 主循环：实时避障 + 航迹跟踪
    while (!corrector.is_path_complete()) {
        auto state = fc.get_state();

        // DWA 局部避障
        auto traj = dwa.plan(
            state.position, state.heading,
            state.velocity.speed(), 0.0,
            goal, {}
        );

        // 航迹修正
        auto correction = corrector.compute_correction(
            state.position, state.heading,
            state.velocity.speed(), 0.1
        );

        // 风险评估
        uav::edge::WeatherData weather = cache.get_cached_weather("nearest");
        auto risk = assessor->assess(weather, {}, {});

        if (risk.level == uav::edge::RiskLevel::Critical) {
            fc.return_to_launch();
            break;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    // 10. 降落
    fc.land();

    // 11. 清理
    uav::edge::shutdown();
    return 0;
}
```

## 5. 配置说明

### 5.1 配置文件格式

EdgeConfig 支持从 JSON 文件加载配置，示例配置：

```json
{
  "path_planner": {
    "algorithm": "rrt_star",
    "resolution": 1.0,
    "rrt_max_iterations": 5000
  },
  "risk": {
    "wind_speed_threshold": 15.0,
    "visibility_threshold": 2000.0,
    "precipitation_threshold": 5.0
  },
  "v2x": {
    "technology": "dsrc",
    "dsrc_channel": 178,
    "tx_power": 20.0
  },
  "federated": {
    "server_url": "https://fl-server.uav-platform.com:8443",
    "aggregation_strategy": "fedprox"
  },
  "model_runtime": {
    "backend": "onnxruntime",
    "device": "CUDA",
    "precision": "fp16",
    "num_threads": 4
  },
  "cache": {
    "dir": "/data/offline_cache",
    "default_ttl": 3600
  }
}
```

### 5.2 编程式配置

```cpp
#include <uav_edge/config.h>

uav::edge::EdgeConfig config;

// 从文件加载
config.load_from_file("/config/edge_config.json");

// 编程式设置
config.set("path_planner.algorithm", "astar");
config.set("path_planner.resolution", 0.5);
config.set("risk.wind_speed_threshold", 12.0);

// 读取
auto algo = config.path_planner_algorithm();
auto res = config.path_planner_resolution();

// 保存
config.save_to_file("/config/edge_config_updated.json");
```

### 5.3 环境变量

SDK 支持通过环境变量覆盖配置：

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `UAV_EDGE_CONFIG_PATH` | 配置文件路径 | （空，使用默认配置） |
| `UAV_EDGE_CACHE_DIR` | 离线缓存目录 | `./offline_cache` |
| `UAV_EDGE_LOG_LEVEL` | 日志级别 | `INFO` |

## 6. 目录结构

```
edge-sdk/cpp/
├── CMakeLists.txt              # CMake 构建配置
├── .clangd                    # clangd LSP 配置
├── include/
│   └── uav_edge/
│       ├── uav_edge.h         # 主头文件（聚合所有子模块）
│       ├── types.h            # 基础类型定义
│       ├── config.h           # 配置管理
│       ├── path_planner.h     # 路径规划接口
│       ├── dwa_planner.h      # DWA 局部规划器
│       ├── path_smoother.h    # 路径平滑器
│       ├── trajectory_corrector.h  # 轨迹修正器
│       ├── flight_controller.h # 飞行控制器
│       ├── risk_assessor.h    # 风险评估
│       ├── v2x_client.h       # V2X 通信
│       ├── federated_client.h # 联邦学习
│       ├── model_runtime.h    # 模型推理运行时
│       └── offline_cache.h     # 离线缓存
└── src/
    ├── edge_core.cpp          # SDK 初始化/清理
    ├── config.cpp             # 配置管理实现
    ├── path_planner.cpp       # 路径规划实现
    ├── dwa_planner.cpp        # DWA 规划器实现
    ├── path_smoother.cpp      # 路径平滑实现
    ├── trajectory_corrector.cpp # 轨迹修正实现
    ├── flight_controller.cpp  # 飞控通信实现
    ├── risk_assessor.cpp      # 风险评估实现
    ├── v2x_client.cpp         # V2X 通信实现
    ├── federated_client.cpp   # 联邦学习实现
    ├── model_runtime.cpp      # 模型推理实现
    └── offline_cache.cpp      # 离线缓存实现
```

## 7. 许可证

MIT
