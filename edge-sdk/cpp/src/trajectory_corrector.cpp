/// @file trajectory_corrector.cpp
/// @brief 轨迹修正器实现（PID 控制器）
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/trajectory_corrector.h"

#include <cmath>
#include <algorithm>
#include <limits>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace uav::edge {

// ============================================================================
// PIDController 实现
// ============================================================================

double TrajectoryCorrector::PIDController::compute(double error, double dt) {
    if (dt <= 0.0) {
        return 0.0;
    }

    // 积分项（带抗饱和限幅）
    integral += error * dt;
    integral = std::clamp(integral, -params.integral_limit, params.integral_limit);

    // 微分项（使用误差变化率）
    double derivative = (error - prev_error) / dt;

    // PID 输出 = P + I + D
    double output = params.kp * error + params.ki * integral + params.kd * derivative;

    // 输出限幅
    output = std::clamp(output, -params.max_output, params.max_output);

    // 更新上一次误差
    prev_error = error;

    return output;
}

void TrajectoryCorrector::PIDController::reset() {
    integral = 0.0;
    prev_error = 0.0;
}

// ============================================================================
// TrajectoryCorrector 参数设置
// ============================================================================

void TrajectoryCorrector::set_lateral_pid(const PIDParams& params) {
    lateral_pid_.params = params;
}

void TrajectoryCorrector::set_heading_pid(const PIDParams& params) {
    heading_pid_.params = params;
}

void TrajectoryCorrector::set_altitude_pid(const PIDParams& params) {
    altitude_pid_.params = params;
}

void TrajectoryCorrector::set_path(const std::vector<Waypoint>& path) {
    path_ = path;
    current_waypoint_idx_ = 0;
    // 重置 PID 状态
    lateral_pid_.reset();
    heading_pid_.reset();
    altitude_pid_.reset();
}

// ============================================================================
// 航点查询
// ============================================================================

Waypoint TrajectoryCorrector::get_current_waypoint() const {
    if (path_.empty() || current_waypoint_idx_ >= path_.size()) {
        return Waypoint{};
    }
    return path_[current_waypoint_idx_];
}

// ============================================================================
// 点到线段距离
// ============================================================================

double TrajectoryCorrector::point_to_segment_distance(
    const Position& p,
    const Position& a,
    const Position& b
) const {
    double dx = b.x - a.x;
    double dy = b.y - a.y;
    double dz = b.z - a.z;
    double len_sq = dx * dx + dy * dy + dz * dz;

    if (len_sq < 1e-12) {
        // 线段退化为点
        return p.distance_to(a);
    }

    // 计算投影参数 t
    double t = ((p.x - a.x) * dx + (p.y - a.y) * dy + (p.z - a.z) * dz) / len_sq;
    t = std::clamp(t, 0.0, 1.0);

    // 投影点
    Position proj;
    proj.x = a.x + t * dx;
    proj.y = a.y + t * dy;
    proj.z = a.z + t * dz;

    return p.distance_to(proj);
}

// ============================================================================
// 修正指令计算
// ============================================================================

CorrectionCommand TrajectoryCorrector::compute_correction(
    const Position& current,
    double current_yaw,
    double current_v,
    double dt
) {
    CorrectionCommand cmd;

    if (path_.empty() || is_path_complete()) {
        return cmd;
    }

    // 当前目标航点
    Waypoint target_wp = get_current_waypoint();
    const Position& target = target_wp.position;

    // 计算到当前航点的距离
    double dx = target.x - current.x;
    double dy = target.y - current.y;
    double dz = target.z - current.z;
    double distance_to_waypoint = std::sqrt(dx * dx + dy * dy + dz * dz);

    // 计算侧向偏差（cross-track error）
    double cross_track = 0.0;
    if (current_waypoint_idx_ > 0) {
        const Position& prev = path_[current_waypoint_idx_ - 1].position;
        cross_track = point_to_segment_distance(current, prev, target);

        // 确定侧向偏差符号（左偏为正，右偏为负）
        double seg_dx = target.x - prev.x;
        double seg_dy = target.y - prev.y;
        double px = current.x - prev.x;
        double py = current.y - prev.y;
        double cross = seg_dx * py - seg_dy * px;
        if (cross < 0.0) {
            cross_track = -cross_track;
        }
    }

    // 计算航向偏差
    double desired_heading = std::atan2(dy, dx);
    double heading_error = desired_heading - current_yaw;

    // 将航向偏差归一化到 [-pi, pi]
    while (heading_error > M_PI) heading_error -= 2.0 * M_PI;
    while (heading_error < -M_PI) heading_error += 2.0 * M_PI;

    // 沿航向偏差
    double along_track = distance_to_waypoint;

    // PID 控制
    cmd.lateral_velocity = lateral_pid_.compute(cross_track, dt);
    cmd.heading_correction = heading_pid_.compute(heading_error, dt);
    cmd.altitude_correction = altitude_pid_.compute(dz, dt);
    cmd.speed_adjustment = 0.0;

    // 更新跟踪误差
    last_error_.cross_track = cross_track;
    last_error_.along_track = along_track;
    last_error_.heading_error = heading_error;
    last_error_.distance_to_waypoint = distance_to_waypoint;

    // 当距离当前航点足够近时，切换到下一个航点
    const double WAYPOINT_REACHED_THRESHOLD = 3.0; // 3米
    if (distance_to_waypoint < WAYPOINT_REACHED_THRESHOLD &&
        current_waypoint_idx_ < path_.size() - 1) {
        ++current_waypoint_idx_;
    }

    return cmd;
}

// ============================================================================
// 状态查询
// ============================================================================

TrackError TrajectoryCorrector::get_current_error() const {
    return last_error_;
}

bool TrajectoryCorrector::is_path_complete() const {
    return path_.empty() || current_waypoint_idx_ >= path_.size();
}

void TrajectoryCorrector::reset() {
    path_.clear();
    current_waypoint_idx_ = 0;
    lateral_pid_.reset();
    heading_pid_.reset();
    altitude_pid_.reset();
    last_error_ = TrackError{};
}

} // namespace uav::edge
