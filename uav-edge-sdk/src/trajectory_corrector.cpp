#include "trajectory_corrector.h"
#include <algorithm>
#include <cmath>
#include <limits>

namespace uav_sdk {

namespace {
    constexpr double kPI = 3.14159265358979323846;
}  // anonymous namespace

// ─── PIDController ──────────────────────────────────────────────────────────

double TrajectoryCorrector::PIDController::compute(double error, double dt) {
    if (dt <= 0.0) {
        return 0.0;
    }

    // 积分项，带限幅
    integral += error * dt;
    integral = std::clamp(integral, -params.integral_limit, params.integral_limit);

    // 微分项
    double derivative = (error - prev_error) / dt;

    // PID 输出
    double output = params.kp * error + params.ki * integral + params.kd * derivative;
    output = std::clamp(output, -params.max_output, params.max_output);

    prev_error = error;
    return output;
}

void TrajectoryCorrector::PIDController::reset() {
    integral = 0.0;
    prev_error = 0.0;
}

// ─── TrajectoryCorrector ────────────────────────────────────────────────────

TrajectoryCorrector::TrajectoryCorrector()
    : current_waypoint_idx_(0)
    , last_error_{0.0, 0.0, 0.0, 0.0} {
}

TrajectoryCorrector::~TrajectoryCorrector() = default;

void TrajectoryCorrector::set_lateral_pid(const PIDParams& params) {
    lateral_pid_.params = params;
}

void TrajectoryCorrector::set_heading_pid(const PIDParams& params) {
    heading_pid_.params = params;
}

void TrajectoryCorrector::set_altitude_pid(const PIDParams& params) {
    altitude_pid_.params = params;
}

void TrajectoryCorrector::set_path(const std::vector<Point>& path) {
    path_ = path;
    current_waypoint_idx_ = 0;
}

Point TrajectoryCorrector::get_current_waypoint() const {
    if (path_.empty() || current_waypoint_idx_ >= path_.size()) {
        return Point(0, 0);
    }
    return path_[current_waypoint_idx_];
}

int TrajectoryCorrector::find_nearest_point(double x, double y) const {
    if (path_.empty()) {
        return -1;
    }

    int nearest_idx = 0;
    double min_dist = std::numeric_limits<double>::max();

    for (size_t i = 0; i < path_.size(); ++i) {
        double dx = x - static_cast<double>(path_[i].x);
        double dy = y - static_cast<double>(path_[i].y);
        double dist = dx * dx + dy * dy;

        if (dist < min_dist) {
            min_dist = dist;
            nearest_idx = static_cast<int>(i);
        }
    }

    return nearest_idx;
}

double TrajectoryCorrector::point_to_line_distance(double px, double py,
                                                    double lx1, double ly1,
                                                    double lx2, double ly2) const {
    double dx = lx2 - lx1;
    double dy = ly2 - ly1;

    // 线段退化为点
    if (dx == 0.0 && dy == 0.0) {
        double ex = px - lx1;
        double ey = py - ly1;
        return std::sqrt(ex * ex + ey * ey);
    }

    // 计算投影参数 t
    double t = ((px - lx1) * dx + (py - ly1) * dy) / (dx * dx + dy * dy);
    t = std::clamp(t, 0.0, 1.0);

    // 最近点坐标
    double proj_x = lx1 + t * dx;
    double proj_y = ly1 + t * dy;

    // 垂直距离
    double ex = px - proj_x;
    double ey = py - proj_y;
    return std::sqrt(ex * ex + ey * ey);
}

CorrectionCommand TrajectoryCorrector::compute_correction(double current_x, double current_y,
                                                           double current_yaw, double current_v,
                                                           double dt) {
    CorrectionCommand cmd = {0.0, 0.0, 0.0, 0.0};

    if (path_.empty() || is_path_complete()) {
        return cmd;
    }

    // 当前目标航点
    Point target = get_current_waypoint();
    double target_x = static_cast<double>(target.x);
    double target_y = static_cast<double>(target.y);

    // 计算到当前航点的距离
    double dx = target_x - current_x;
    double dy = target_y - current_y;
    double distance_to_waypoint = std::sqrt(dx * dx + dy * dy);

    // 计算侧向偏差（cross-track error）
    double cross_track = 0.0;
    if (current_waypoint_idx_ > 0) {
        Point prev = path_[current_waypoint_idx_ - 1];
        cross_track = point_to_line_distance(current_x, current_y,
                                             static_cast<double>(prev.x),
                                             static_cast<double>(prev.y),
                                             target_x, target_y);
        // 确定侧向偏差符号：根据点在路径左侧还是右侧
        double seg_dx = target_x - static_cast<double>(prev.x);
        double seg_dy = target_y - static_cast<double>(prev.y);
        double px = current_x - static_cast<double>(prev.x);
        double py = current_y - static_cast<double>(prev.y);
        double cross = seg_dx * py - seg_dy * px;
        if (cross < 0.0) {
            cross_track = -cross_track;
        }
    }

    // 计算航向偏差
    double desired_heading = std::atan2(dy, dx);
    double heading_error = desired_heading - current_yaw;

    // 将航向偏差归一化到 [-pi, pi]
    while (heading_error > kPI) heading_error -= 2.0 * kPI;
    while (heading_error < -kPI) heading_error += 2.0 * kPI;

    // 沿航向偏差（沿路径方向的偏差）
    double along_track = distance_to_waypoint;

    // PID 控制
    cmd.lateral_velocity = lateral_pid_.compute(cross_track, dt);
    cmd.heading_correction = heading_pid_.compute(heading_error, dt);
    cmd.altitude_correction = altitude_pid_.compute(0.0, dt);
    cmd.speed_adjustment = 0.0;

    // 更新跟踪误差
    last_error_.cross_track = cross_track;
    last_error_.along_track = along_track;
    last_error_.heading_error = heading_error;
    last_error_.distance_to_waypoint = distance_to_waypoint;

    // 当距离当前航点足够近时，切换到下一个航点
    const double WAYPOINT_REACHED_THRESHOLD = 3.0; // 3米
    if (distance_to_waypoint < WAYPOINT_REACHED_THRESHOLD &&
        current_waypoint_idx_ < static_cast<int>(path_.size()) - 1) {
        ++current_waypoint_idx_;
    }

    return cmd;
}

TrackError TrajectoryCorrector::get_current_error() const {
    return last_error_;
}

bool TrajectoryCorrector::is_path_complete() const {
    return path_.empty() || current_waypoint_idx_ >= static_cast<int>(path_.size());
}

void TrajectoryCorrector::reset() {
    path_.clear();
    current_waypoint_idx_ = 0;
    lateral_pid_.reset();
    heading_pid_.reset();
    altitude_pid_.reset();
    last_error_ = {0.0, 0.0, 0.0, 0.0};
}

}  // namespace uav_sdk
