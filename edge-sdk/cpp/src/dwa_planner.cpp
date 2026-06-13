/// @file dwa_planner.cpp
/// @brief DWA 局部路径规划器实现
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/dwa_planner.h"

#include <cmath>
#include <limits>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace uav::edge {

// ============================================================================
// DWAPlanner 参数管理
// ============================================================================

void DWAPlanner::set_params(const DWAParams& params) {
    params_ = params;
}

const DWAParams& DWAPlanner::get_params() const {
    return params_;
}

// ============================================================================
// DWA 规划核心
// ============================================================================

Trajectory DWAPlanner::plan(
    const Position& current,
    double current_yaw,
    double current_v,
    double current_w,
    const Position& goal,
    const std::vector<Obstacle>& obstacles
) {
    // 计算动态窗口（可达速度空间）
    auto vs = calc_dynamic_window(current_v, current_w);

    Trajectory best_traj;
    best_traj.cost = std::numeric_limits<double>::max();
    best_traj.is_valid = false;

    // 在速度空间中搜索最优轨迹
    int v_steps = static_cast<int>((vs.v_max - vs.v_min) / vs.v_resolution) + 1;
    int w_steps = static_cast<int>((vs.w_max - vs.w_min) / vs.w_resolution) + 1;

    for (int i = 0; i < v_steps; ++i) {
        double v = vs.v_min + i * vs.v_resolution;
        v = std::clamp(v, vs.v_min, vs.v_max);

        for (int j = 0; j < w_steps; ++j) {
            double w = vs.w_min + j * vs.w_resolution;
            w = std::clamp(w, vs.w_min, vs.w_max);

            // 预测轨迹
            Trajectory traj = predict_trajectory(current.x, current.y, current.z, current_yaw, v, w);

            // 计算航向代价
            double heading_cost = calc_heading_cost(traj, goal.x, goal.y);

            // 计算障碍物代价
            double obstacle_cost = calc_obstacle_cost(traj, obstacles);

            // 碰撞轨迹直接跳过
            if (obstacle_cost >= std::numeric_limits<double>::max() * 0.5) {
                continue;
            }

            // 计算速度代价
            double vel_cost = calc_velocity_cost(traj);

            // 加权总代价
            double total_cost = params_.alpha * heading_cost +
                                params_.beta * obstacle_cost +
                                params_.gamma * vel_cost;

            traj.cost = total_cost;
            traj.is_valid = true;

            if (total_cost < best_traj.cost) {
                best_traj = traj;
            }
        }
    }

    // 如果未找到有效轨迹，返回减速至零的轨迹
    if (!best_traj.is_valid) {
        best_traj = predict_trajectory(current.x, current.y, current.z, current_yaw, 0.0, 0.0);
        best_traj.cost = std::numeric_limits<double>::max();
        best_traj.is_valid = false;
    }

    return best_traj;
}

// ============================================================================
// 轨迹预测
// ============================================================================

Trajectory DWAPlanner::predict_trajectory(
    double x0, double y0, double z0, double yaw0,
    double v, double w
) const {
    Trajectory traj;
    traj.v = v;
    traj.w = w;
    traj.is_valid = true;
    traj.cost = 0.0;

    double x = x0;
    double y = y0;
    double z = z0;
    double yaw = yaw0;

    // 根据预测时间步数生成轨迹点
    int steps = static_cast<int>(params_.predict_time / params_.dt);

    for (int i = 0; i <= steps; ++i) {
        TrajectoryPoint pt;
        pt.x = x;
        pt.y = y;
        pt.z = z;
        pt.yaw = yaw;
        pt.v = v;
        pt.w = w;
        traj.points.push_back(pt);

        // 简化运动学模型更新（类似差速驱动）
        x += v * std::cos(yaw) * params_.dt;
        y += v * std::sin(yaw) * params_.dt;
        // 高度保持不变（简化模型）
        yaw += w * params_.dt;

        // 将 yaw 归一化到 [-pi, pi]
        yaw = std::atan2(std::sin(yaw), std::cos(yaw));
    }

    return traj;
}

// ============================================================================
// 动态窗口计算
// ============================================================================

DWAPlanner::VelocitySpace DWAPlanner::calc_dynamic_window(
    double current_v, double current_w
) const {
    VelocitySpace vs;

    // 速度极限
    vs.v_min = params_.v_min;
    vs.v_max = params_.v_max;
    vs.w_min = params_.w_min;
    vs.w_max = params_.w_max;
    vs.v_resolution = 0.05;
    vs.w_resolution = 0.1;

    // 考虑加速度限制的可达速度范围
    double reachable_v_min = current_v - params_.max_accel * params_.dt;
    double reachable_v_max = current_v + params_.max_accel * params_.dt;
    double reachable_w_min = current_w - params_.max_angular_accel * params_.dt;
    double reachable_w_max = current_w + params_.max_angular_accel * params_.dt;

    // 取速度极限与可达速度的交集
    vs.v_min = std::max(vs.v_min, reachable_v_min);
    vs.v_max = std::min(vs.v_max, reachable_v_max);
    vs.w_min = std::max(vs.w_min, reachable_w_min);
    vs.w_max = std::min(vs.w_max, reachable_w_max);

    // 确保边界有效
    if (vs.v_min > vs.v_max) {
        vs.v_min = vs.v_max;
    }
    if (vs.w_min > vs.w_max) {
        vs.w_min = vs.w_max;
    }

    return vs;
}

// ============================================================================
// 代价函数
// ============================================================================

double DWAPlanner::calc_heading_cost(const Trajectory& traj, double gx, double gy) const {
    if (traj.points.empty()) {
        return 0.0;
    }

    // 使用轨迹末端点计算航向偏差
    const auto& last_pt = traj.points.back();

    double dx = gx - last_pt.x;
    double dy = gy - last_pt.y;

    if (std::abs(dx) < 1e-6 && std::abs(dy) < 1e-6) {
        return 0.0; // 已到达目标
    }

    double goal_angle = std::atan2(dy, dx);
    double angle_diff = goal_angle - last_pt.yaw;

    // 归一化到 [-pi, pi]
    angle_diff = std::atan2(std::sin(angle_diff), std::cos(angle_diff));

    // 归一化到 [0, 1]
    return std::abs(angle_diff) / M_PI;
}

double DWAPlanner::calc_obstacle_cost(
    const Trajectory& traj,
    const std::vector<Obstacle>& obstacles
) const {
    if (obstacles.empty()) {
        return 0.0;
    }

    double min_dist = std::numeric_limits<double>::max();

    // 遍历轨迹上每个点与每个障碍物的距离
    for (const auto& pt : traj.points) {
        for (const auto& obs : obstacles) {
            double dx = pt.x - obs.position.x;
            double dy = pt.y - obs.position.y;
            double dist = std::sqrt(dx * dx + dy * dy);

            // 碰撞检测：距离小于障碍物半径加膨胀半径
            if (dist < obs.radius + params_.obstacle_radius) {
                return std::numeric_limits<double>::max(); // 碰撞，返回最大代价
            }

            min_dist = std::min(min_dist, dist);
        }
    }

    // 距离越近代价越高（反比关系）
    return 1.0 / (min_dist + 1e-6);
}

double DWAPlanner::calc_velocity_cost(const Trajectory& traj) const {
    if (params_.v_max <= 0.0) {
        return 0.0;
    }
    // 偏好高速：速度越接近 v_max 代价越低
    return (params_.v_max - std::abs(traj.v)) / params_.v_max;
}

} // namespace uav::edge
