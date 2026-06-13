#pragma once

/// @file flight_controller.h
/// @brief 飞行控制器接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <string>
#include <vector>
#include <functional>
#include <mutex>
#include <atomic>
#include <chrono>
#include <cstdint>

namespace uav::edge {

// ============================================================================
// 飞行模式
// ============================================================================

/// 飞行模式枚举
enum class FlightMode : uint8_t {
    Manual = 0,     ///< 手动模式
    Stabilize = 1,  ///< 自稳模式
    AltHold = 2,    ///< 定高模式
    Position = 3,   ///< 定点模式
    Auto = 4,       ///< 自动模式
    RTL = 5,        ///< 返航模式
    Land = 6,       ///< 降落模式
    Takeoff = 7,    ///< 起飞模式
    Guided = 8,     ///< 引导模式
    Loiter = 9,     ///< 留待模式
    Follow = 10,    ///< 跟随模式
    Circle = 11     ///< 绕圈模式
};

// ============================================================================
// 无人机状态
// ============================================================================

/// 无人机实时状态
struct UAVState {
    Position position;             ///< 当前位置
    Velocity velocity;             ///< 当前速度
    double heading{0.0};           ///< 航向角 (rad)
    double roll{0.0};              ///< 横滚角 (rad)
    double pitch{0.0};             ///< 俯仰角 (rad)
    double yaw{0.0};               ///< 偏航角 (rad)
    double battery_percent{100.0};  ///< 电池电量 (%)
    FlightMode mode{FlightMode::Manual}; ///< 飞行模式
    bool armed{false};             ///< 是否解锁
    bool flying{false};            ///< 是否在飞行中
    std::chrono::system_clock::time_point last_heartbeat; ///< 最后心跳时间
};

// ============================================================================
// 飞行控制器
// ============================================================================

/// 飞行控制器
/// 基于 MAVLink v2 协议的飞控通信实现
/// 支持 PX4 和 ArduPilot 飞控系统
class FlightController {
public:
    /// 构造函数
    /// @param connection_type 连接类型 ("serial" 或 "udp")
    /// @param connection_params 连接参数（串口设备名或UDP地址:端口）
    explicit FlightController(
        const std::string& connection_type = "serial",
        const std::string& connection_params = "COM3:57600"
    );

    /// 析构函数
    ~FlightController();

    // 禁止拷贝
    FlightController(const FlightController&) = delete;
    FlightController& operator=(const FlightController&) = delete;

    // ========================================================================
    // 连接管理
    // ========================================================================

    /// 连接飞控
    bool connect();

    /// 断开连接
    void disconnect();

    /// 检查是否已连接
    [[nodiscard]] bool is_connected() const;

    // ========================================================================
    // 状态获取
    // ========================================================================

    /// 获取当前无人机状态
    UAVState get_state();

    /// 获取最后心跳时间
    [[nodiscard]] std::chrono::system_clock::time_point last_heartbeat() const;

    /// 获取连接质量 (0-100)
    [[nodiscard]] double connection_quality() const;

    // ========================================================================
    // 飞控指令
    // ========================================================================

    /// 解锁电机
    bool arm();

    /// 上锁电机
    bool disarm();

    /// 设置飞行模式
    bool set_mode(FlightMode mode);

    /// 通过名称设置飞行模式
    bool set_mode(const std::string& mode_name);

    /// 起飞到指定高度
    bool takeoff(double altitude);

    /// 降落
    bool land();

    /// 返航
    bool return_to_launch();

    /// 飞向指定位置
    bool goto_position(const Position& target);

    // ========================================================================
    // 任务管理
    // ========================================================================

    /// 上传任务（航路点序列）
    bool upload_mission(const std::vector<Waypoint>& waypoints);

    /// 执行任务
    bool execute_mission();

    /// 暂停任务
    bool pause_mission();

    /// 清除任务
    bool clear_mission();

    // ========================================================================
    // 回调
    // ========================================================================

    /// 状态更新回调类型
    using StateCallback = std::function<void(const UAVState&)>;

    /// 注册状态更新回调
    void on_state_changed(StateCallback callback);

private:
    std::string connection_type_;    ///< 连接类型
    std::string connection_params_;  ///< 连接参数
    bool connected_{false};         ///< 连接状态
    UAVState current_state_;         ///< 当前状态
    mutable std::mutex state_mutex_; ///< 状态互斥锁
    std::atomic<bool> running_{false}; ///< 运行标志
    StateCallback state_callback_;   ///< 状态回调
};

} // namespace uav::edge
