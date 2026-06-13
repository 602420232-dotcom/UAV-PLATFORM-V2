#pragma once

/// @file trajectory_corrector.h
/// @brief 轨迹修正器接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <vector>

namespace uav::edge {

// ============================================================================
// PID 控制器参数
// ============================================================================

/// PID 控制器参数
struct PIDParams {
    double kp{1.0};              ///< 比例增益
    double ki{0.01};             ///< 积分增益
    double kd{0.1};              ///< 微分增益
    double max_output{2.0};      ///< 最大输出限幅
    double integral_limit{10.0}; ///< 积分限幅
};

// ============================================================================
// 航迹偏差
// ============================================================================

/// 航迹跟踪偏差
struct TrackError {
    double cross_track{0.0};          ///< 侧向偏差 (m)
    double along_track{0.0};          ///< 沿航向偏差 (m)
    double heading_error{0.0};        ///< 航向偏差 (rad)
    double distance_to_waypoint{0.0}; ///< 到当前航点距离 (m)
};

// ============================================================================
// 修正指令
// ============================================================================

/// 轨迹修正指令
struct CorrectionCommand {
    double lateral_velocity{0.0};    ///< 侧向速度修正 (m/s)
    double heading_correction{0.0};  ///< 航向修正 (rad/s)
    double altitude_correction{0.0}; ///< 高度修正 (m/s)
    double speed_adjustment{0.0};    ///< 速度调整 (m/s)
};

// ============================================================================
// 轨迹修正器
// ============================================================================

/// 轨迹修正器
/// 使用 PID 控制器实现路径跟踪和偏差修正
class TrajectoryCorrector {
public:
    TrajectoryCorrector() = default;
    ~TrajectoryCorrector() = default;

    /// 设置侧向 PID 参数
    void set_lateral_pid(const PIDParams& params);

    /// 设置航向 PID 参数
    void set_heading_pid(const PIDParams& params);

    /// 设置高度 PID 参数
    void set_altitude_pid(const PIDParams& params);

    /// 设置跟踪路径（航路点序列）
    void set_path(const std::vector<Waypoint>& path);

    /// 获取当前目标航点
    [[nodiscard]] Waypoint get_current_waypoint() const;

    /// 计算修正指令
    /// @param current 当前位置
    /// @param current_yaw 当前航向 (rad)
    /// @param current_v 当前速度 (m/s)
    /// @param dt 时间步长 (s)
    /// @return 修正指令
    CorrectionCommand compute_correction(
        const Position& current,
        double current_yaw,
        double current_v,
        double dt
    );

    /// 获取当前跟踪误差
    [[nodiscard]] TrackError get_current_error() const;

    /// 检查路径是否已完成
    [[nodiscard]] bool is_path_complete() const;

    /// 重置所有状态
    void reset();

private:
    /// PID 控制器内部实现
    struct PIDController {
        PIDParams params;
        double integral{0.0};
        double prev_error{0.0};

        double compute(double error, double dt);
        void reset();
    };

    /// 点到线段距离
    double point_to_segment_distance(
        const Position& p,
        const Position& a,
        const Position& b
    ) const;

    std::vector<Waypoint> path_;     ///< 跟踪路径
    size_t current_waypoint_idx_{0}; ///< 当前航点索引

    PIDController lateral_pid_;   ///< 侧向 PID
    PIDController heading_pid_;   ///< 航向 PID
    PIDController altitude_pid_;  ///< 高度 PID

    TrackError last_error_;       ///< 最后一次误差
};

} // namespace uav::edge
