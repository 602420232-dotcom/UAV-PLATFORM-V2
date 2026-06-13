/// @file flight_controller.cpp
/// @brief 飞行控制器实现
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/flight_controller.h"

#include <cmath>
#include <algorithm>
#include <sstream>
#include <chrono>
#include <thread>

namespace uav::edge {

// ============================================================================
// 构造/析构
// ============================================================================

FlightController::FlightController(
    const std::string& connection_type,
    const std::string& connection_params
)
    : connection_type_(connection_type)
    , connection_params_(connection_params)
{
}

FlightController::~FlightController() {
    disconnect();
}

// ============================================================================
// 连接管理
// ============================================================================

bool FlightController::connect() {
    if (connected_) {
        return true; // 已连接
    }

    // 模拟连接（实际实现需对接串口/UDP通信）
    // 在仿真模式下，直接标记为已连接
    connected_ = true;
    running_ = true;

    // 初始化默认状态
    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        current_state_ = UAVState{};
        current_state_.mode = FlightMode::Stabilize;
        current_state_.battery_percent = 100.0;
        current_state_.last_heartbeat = std::chrono::system_clock::now();
    }

    return true;
}

void FlightController::disconnect() {
    if (!connected_) return;

    running_ = false;
    connected_ = false;
}

bool FlightController::is_connected() const {
    return connected_;
}

// ============================================================================
// 状态获取
// ============================================================================

UAVState FlightController::get_state() {
    std::lock_guard<std::mutex> lock(state_mutex_);
    return current_state_;
}

std::chrono::system_clock::time_point FlightController::last_heartbeat() const {
    std::lock_guard<std::mutex> lock(state_mutex_);
    return current_state_.last_heartbeat;
}

double FlightController::connection_quality() const {
    if (!connected_) return 0.0;

    auto now = std::chrono::system_clock::now();
    std::lock_guard<std::mutex> lock(state_mutex_);
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        now - current_state_.last_heartbeat).count();

    if (elapsed > 10000) return 0.0;     // 10秒无心跳
    if (elapsed > 5000) return 50.0;     // 5秒无心跳
    if (elapsed > 2000) return 80.0;     // 2秒
    return 100.0;                         // 正常
}

// ============================================================================
// 飞控指令
// ============================================================================

bool FlightController::arm() {
    if (!connected_) return false;

    std::lock_guard<std::mutex> lock(state_mutex_);
    current_state_.armed = true;

    // 通知状态回调
    if (state_callback_) {
        state_callback_(current_state_);
    }

    return true;
}

bool FlightController::disarm() {
    if (!connected_) return false;

    std::lock_guard<std::mutex> lock(state_mutex_);
    current_state_.armed = false;
    current_state_.flying = false;

    if (state_callback_) {
        state_callback_(current_state_);
    }

    return true;
}

bool FlightController::set_mode(FlightMode mode) {
    if (!connected_) return false;

    std::lock_guard<std::mutex> lock(state_mutex_);
    current_state_.mode = mode;

    if (state_callback_) {
        state_callback_(current_state_);
    }

    return true;
}

bool FlightController::set_mode(const std::string& mode_name) {
    // 模式名称到枚举的映射
    static const std::pair<const char*, FlightMode> mode_map[] = {
        {"MANUAL",    FlightMode::Manual},
        {"STABILIZE", FlightMode::Stabilize},
        {"ALT_HOLD",  FlightMode::AltHold},
        {"POSITION",  FlightMode::Position},
        {"AUTO",      FlightMode::Auto},
        {"RTL",       FlightMode::RTL},
        {"LAND",      FlightMode::Land},
        {"TAKEOFF",   FlightMode::Takeoff},
        {"GUIDED",    FlightMode::Guided},
        {"LOITER",    FlightMode::Loiter},
        {"FOLLOW",    FlightMode::Follow},
        {"CIRCLE",    FlightMode::Circle}
    };

    for (const auto& [name, mode] : mode_map) {
        if (mode_name == name) {
            return set_mode(mode);
        }
    }

    return false; // 未知模式
}

bool FlightController::takeoff(double altitude) {
    if (!connected_) return false;
    if (altitude <= 0.0 || altitude > 500.0) return false; // 高度范围检查

    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        current_state_.mode = FlightMode::Takeoff;
        current_state_.position.z = altitude;
        current_state_.flying = true;
        current_state_.armed = true;
    }

    if (state_callback_) {
        state_callback_(current_state_);
    }

    return true;
}

bool FlightController::land() {
    if (!connected_) return false;

    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        current_state_.mode = FlightMode::Land;
        current_state_.position.z = 0.0;
        current_state_.flying = false;
    }

    if (state_callback_) {
        state_callback_(current_state_);
    }

    return true;
}

bool FlightController::return_to_launch() {
    if (!connected_) return false;

    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        current_state_.mode = FlightMode::RTL;
    }

    if (state_callback_) {
        state_callback_(current_state_);
    }

    return true;
}

bool FlightController::goto_position(const Position& target) {
    if (!connected_) return false;

    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        current_state_.position = target;
        current_state_.mode = FlightMode::Guided;
    }

    if (state_callback_) {
        state_callback_(current_state_);
    }

    return true;
}

// ============================================================================
// 任务管理
// ============================================================================

bool FlightController::upload_mission(const std::vector<Waypoint>& waypoints) {
    if (!connected_) return false;
    if (waypoints.empty()) return false;

    // 模拟上传任务
    // 实际实现需通过 MAVLink 协议逐个发送航点
    (void)waypoints;
    return true;
}

bool FlightController::execute_mission() {
    if (!connected_) return false;
    return set_mode(FlightMode::Auto);
}

bool FlightController::pause_mission() {
    if (!connected_) return false;
    return set_mode(FlightMode::Loiter);
}

bool FlightController::clear_mission() {
    if (!connected_) return false;
    // 模拟清除任务
    return true;
}

// ============================================================================
// 回调
// ============================================================================

void FlightController::on_state_changed(StateCallback callback) {
    state_callback_ = std::move(callback);
}

} // namespace uav::edge
