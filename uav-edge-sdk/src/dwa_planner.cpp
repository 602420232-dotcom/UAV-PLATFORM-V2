#include "dwa_planner.h"
#include <limits>

namespace uav_sdk {

DWAPlanner::DWAPlanner() {}

DWAPlanner::~DWAPlanner() {}

void DWAPlanner::set_params(const DWAParams& params) {
    params_ = params;
}

DWAParams DWAPlanner::get_params() const {
    return params_;
}

Trajectory DWAPlanner::plan(double current_x, double current_y, double current_yaw,
                             double current_v, double current_w,
                             double goal_x, double goal_y,
                             const std::vector<Point>& obstacles) {
    VelocitySpace vs = calc_dynamic_window(current_v, current_w);

    Trajectory best_traj;
    best_traj.cost = std::numeric_limits<double>::max();
    best_traj.is_valid = false;

    int v_steps = static_cast<int>((vs.v_max - vs.v_min) / vs.v_resolution) + 1;
    int w_steps = static_cast<int>((vs.w_max - vs.w_min) / vs.w_resolution) + 1;

    for (int i = 0; i < v_steps; ++i) {
        double v = vs.v_min + i * vs.v_resolution;
        v = std::clamp(v, vs.v_min, vs.v_max);

        for (int j = 0; j < w_steps; ++j) {
            double w = vs.w_min + j * vs.w_resolution;
            w = std::clamp(w, vs.w_min, vs.w_max);

            Trajectory traj = predict_trajectory(current_x, current_y, current_yaw, v, w);

            double heading_cost = calc_heading_cost(traj, goal_x, goal_y);
            double obstacle_cost = calc_obstacle_cost(traj, obstacles);

            if (obstacle_cost >= std::numeric_limits<double>::max() * 0.5) {
                continue;
            }

            double vel_cost = calc_velocity_cost(traj);

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
        best_traj = predict_trajectory(current_x, current_y, current_yaw, 0.0, 0.0);
        best_traj.cost = std::numeric_limits<double>::max();
        best_traj.is_valid = false;
    }

    return best_traj;
}

Trajectory DWAPlanner::predict_trajectory(double x0, double y0, double yaw0,
                                           double v, double w) const {
    Trajectory traj;
    traj.v = v;
    traj.w = w;
    traj.is_valid = true;
    traj.cost = 0.0;

    double x = x0;
    double y = y0;
    double yaw = yaw0;

    int steps = static_cast<int>(params_.predict_time / params_.dt);

    for (int i = 0; i <= steps; ++i) {
        TrajectoryPoint pt;
        pt.x = x;
        pt.y = y;
        pt.yaw = yaw;
        pt.v = v;
        pt.w = w;
        traj.points.push_back(pt);

        // 简化自行车模型运动学更新
        x += v * std::cos(yaw) * params_.dt;
        y += v * std::sin(yaw) * params_.dt;
        yaw += w * params_.dt;

        // 将 yaw 归一化到 [-pi, pi]
        yaw = std::atan2(std::sin(yaw), std::cos(yaw));
    }

    return traj;
}

VelocitySpace DWAPlanner::calc_dynamic_window(double current_v, double current_w) const {
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

double DWAPlanner::calc_heading_cost(const Trajectory& traj, double gx, double gy) const {
    if (traj.points.empty()) {
        return 0.0;
    }

    const auto& last_pt = traj.points.back();

    double dx = gx - last_pt.x;
    double dy = gy - last_pt.y;

    if (std::abs(dx) < 1e-6 && std::abs(dy) < 1e-6) {
        return 0.0;
    }

    double goal_angle = std::atan2(dy, dx);
    double angle_diff = goal_angle - last_pt.yaw;

    // 归一化到 [-pi, pi]
    angle_diff = std::atan2(std::sin(angle_diff), std::cos(angle_diff));

    return std::abs(angle_diff) / M_PI;
}

double DWAPlanner::calc_obstacle_cost(const Trajectory& traj, const std::vector<Point>& obstacles) const {
    if (obstacles.empty()) {
        return 0.0;
    }

    double min_dist = std::numeric_limits<double>::max();

    for (const auto& pt : traj.points) {
        for (const auto& obs : obstacles) {
            double dx = pt.x - static_cast<double>(obs.x);
            double dy = pt.y - static_cast<double>(obs.y);
            double dist = std::sqrt(dx * dx + dy * dy);

            if (dist < params_.obstacle_radius) {
                // 碰撞：返回最大代价
                return std::numeric_limits<double>::max();
            }

            min_dist = std::min(min_dist, dist);
        }
    }

    // 距离越近代价越高
    return 1.0 / (min_dist + 1e-6);
}

double DWAPlanner::calc_velocity_cost(const Trajectory& traj) const {
    if (params_.v_max <= 0.0) {
        return 0.0;
    }
    // 偏好高速：速度越接近 v_max 代价越低
    return (params_.v_max - std::abs(traj.v)) / params_.v_max;
}

}  // namespace uav_sdk
