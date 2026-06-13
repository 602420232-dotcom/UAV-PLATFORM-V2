/// @file edge_core.cpp
/// @brief UAVEdge 核心类实现（初始化/启动/停止）
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/uav_edge.h"
#include "uav_edge/config.h"
#include "uav_edge/path_planner.h"
#include "uav_edge/dwa_planner.h"
#include "uav_edge/risk_assessor.h"
#include "uav_edge/flight_controller.h"
#include "uav_edge/path_smoother.h"
#include "uav_edge/trajectory_corrector.h"
#include "uav_edge/offline_cache.h"
#include "uav_edge/v2x_client.h"
#include "uav_edge/federated_client.h"
#include "uav_edge/model_runtime.h"

#include <iostream>
#include <fstream>
#include <sstream>
#include <chrono>
#include <mutex>
#include <memory>
#include <atomic>

namespace uav::edge {

// ============================================================================
// 全局状态管理
// ============================================================================

namespace {

/// SDK 全局初始化状态
std::atomic<bool> g_initialized{false};

/// 全局配置
EdgeConfig g_config;

/// 全局互斥锁（用于初始化/清理）
std::mutex g_init_mutex;

/// 路径规划器实例
std::unique_ptr<IPathPlanner> g_path_planner;

/// DWA 局部规划器
std::unique_ptr<DWAPlanner> g_dwa_planner;

/// 风险评估器
std::unique_ptr<IRiskAssessor> g_risk_assessor;

/// 飞行控制器
std::unique_ptr<FlightController> g_flight_controller;

/// 路径平滑器
std::unique_ptr<PathSmoother> g_path_smoother;

/// 轨迹修正器
std::unique_ptr<TrajectoryCorrector> g_trajectory_corrector;

/// 离线缓存
std::unique_ptr<OfflineCache> g_offline_cache;

/// V2X 通信客户端
std::unique_ptr<IV2XClient> g_v2x_client;

/// 联邦学习客户端
std::unique_ptr<IFederatedClient> g_federated_client;

/// 模型推理运行时
std::unique_ptr<IModelRuntime> g_model_runtime;

} // anonymous namespace

// ============================================================================
// SDK 初始化与清理
// ============================================================================

bool initialize(const std::string& config_path) {
    std::lock_guard<std::mutex> lock(g_init_mutex);

    if (g_initialized) {
        return true; // 已初始化
    }

    // 1. 加载配置
    if (!config_path.empty()) {
        if (!g_config.load_from_file(config_path)) {
            // 配置文件加载失败，使用默认配置
            std::cerr << "[UAVEdge] 警告: 配置文件加载失败，使用默认配置"
                      << std::endl;
        }
    }

    // 2. 创建路径规划器
    std::string planner_algo = g_config.path_planner_algorithm();
    if (planner_algo.empty()) planner_algo = "astar";
    g_path_planner = create_path_planner(planner_algo);
    g_path_planner->initialize("");

    // 3. 创建 DWA 局部规划器
    g_dwa_planner = std::make_unique<DWAPlanner>();

    // 4. 创建风险评估器
    g_risk_assessor = create_risk_assessor("weather");
    g_risk_assessor->initialize("");

    // 5. 创建飞行控制器
    g_flight_controller = std::make_unique<FlightController>("serial", "COM3:57600");

    // 6. 创建路径平滑器
    g_path_smoother = std::make_unique<PathSmoother>();

    // 7. 创建轨迹修正器
    g_trajectory_corrector = std::make_unique<TrajectoryCorrector>();

    // 8. 创建离线缓存
    g_offline_cache = std::make_unique<OfflineCache>("./offline_cache");

    // 9. 创建 V2X 通信客户端
    V2XTechnology v2x_tech = g_config.v2x_technology();
    g_v2x_client = create_v2x_client(v2x_tech);
    g_v2x_client->initialize("");

    // 10. 创建联邦学习客户端
    std::string fl_server = g_config.federated_server_url();
    g_federated_client = create_federated_client();
    g_federated_client->initialize("");

    // 11. 创建模型推理运行时
    std::string runtime_backend = g_config.model_runtime_backend();
    if (runtime_backend.empty()) runtime_backend = "onnxruntime";
    g_model_runtime = create_model_runtime(runtime_backend);

    g_initialized = true;

    std::cout << "[UAVEdge] SDK 初始化完成 (v" << version() << ")" << std::endl;
    std::cout << "  路径规划器: " << g_path_planner->name() << std::endl;
    std::cout << "  风险评估器: " << g_risk_assessor->name() << std::endl;
    std::cout << "  V2X 技术: " << (v2x_tech == V2XTechnology::DSRC ? "DSRC" : "C-V2X") << std::endl;
    std::cout << "  推理后端: " << g_model_runtime->runtime_name()
              << " " << g_model_runtime->runtime_version() << std::endl;

    return true;
}

void shutdown() {
    std::lock_guard<std::mutex> lock(g_init_mutex);

    if (!g_initialized) {
        return;
    }

    // 按照创建的逆序释放资源
    std::cout << "[UAVEdge] 正在关闭 SDK..." << std::endl;

    // 11. 释放模型运行时
    if (g_model_runtime) {
        g_model_runtime->unload_model();
        g_model_runtime.reset();
    }

    // 10. 断开联邦学习
    if (g_federated_client) {
        g_federated_client->disconnect();
        g_federated_client.reset();
    }

    // 9. 停止 V2X 通信
    if (g_v2x_client) {
        g_v2x_client->stop();
        g_v2x_client.reset();
    }

    // 8. 释放离线缓存（析构自动保存索引）
    g_offline_cache.reset();

    // 7. 释放轨迹修正器
    g_trajectory_corrector.reset();

    // 6. 释放路径平滑器
    g_path_smoother.reset();

    // 5. 断开飞行控制器
    if (g_flight_controller) {
        g_flight_controller->disconnect();
        g_flight_controller.reset();
    }

    // 4. 释放风险评估器
    g_risk_assessor.reset();

    // 3. 释放 DWA 规划器
    g_dwa_planner.reset();

    // 2. 释放路径规划器
    g_path_planner.reset();

    g_initialized = false;

    std::cout << "[UAVEdge] SDK 已关闭" << std::endl;
}

bool is_initialized() {
    return g_initialized.load();
}

} // namespace uav::edge
