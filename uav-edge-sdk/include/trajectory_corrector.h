#ifndef TRAJECTORY_CORRECTOR_H
#define TRAJECTORY_CORRECTOR_H

#include <vector>
#include <cmath>
#include <functional>
#include "path_planner.h"

namespace uav_sdk {

/**
 * @brief PID 控制器参数
 */
struct PIDParams {
    double kp = 1.0;               // 比例增益
    double ki = 0.01;              // 积分增益
    double kd = 0.1;               // 微分增益
    double max_output = 2.0;       // 最大输出
    double integral_limit = 10.0;  // 积分限幅
};

/**
 * @brief 航迹偏差
 */
struct TrackError {
    double cross_track;            // 侧向偏差 (m)
    double along_track;            // 沿航向偏差 (m)
    double heading_error;          // 航向偏差 (rad)
    double distance_to_waypoint;   // 到当前航点距离 (m)
};

/**
 * @brief 修正指令
 */
struct CorrectionCommand {
    double lateral_velocity;       // 侧向速度修正 (m/s)
    double heading_correction;     // 航向修正 (rad)
    double altitude_correction;    // 高度修正 (m)
    double speed_adjustment;       // 速度调整 (m/s)
};

/**
 * @brief 航迹修正器
 * 
 * 使用PID控制器实现路径跟踪和偏差修正
 */
class TrajectoryCorrector {
public:
    TrajectoryCorrector();
    ~TrajectoryCorrector();

    /**
     * @brief 设置PID参数
     */
    void set_lateral_pid(const PIDParams& params);
    void set_heading_pid(const PIDParams& params);
    void set_altitude_pid(const PIDParams& params);

    /**
     * @brief 设置航点路径
     */
    void set_path(const std::vector<Point>& path);

    /**
     * @brief 获取当前目标航点
     */
    Point get_current_waypoint() const;

    /**
     * @brief 计算修正指令
     * @param current_x, current_y, current_yaw 当前位置和朝向
     * @param current_v 当前速度
     * @param dt 时间步长
     * @return 修正指令
     */
    CorrectionCommand compute_correction(double current_x, double current_y,
                                          double current_yaw, double current_v,
                                          double dt);

    /**
     * @brief 获取当前跟踪误差
     */
    TrackError get_current_error() const;

    /**
     * @brief 是否到达终点
     */
    bool is_path_complete() const;

    /**
     * @brief 重置状态
     */
    void reset();

private:
    /**
     * @brief 计算点到线段的距离
     */
    double point_to_line_distance(double px, double py,
                                   double lx1, double ly1,
                                   double lx2, double ly2) const;

    /**
     * @brief 查找最近路径点索引
     */
    int find_nearest_point(double x, double y) const;

    struct PIDController {
        PIDParams params;
        double integral = 0;
        double prev_error = 0;
        
        double compute(double error, double dt);
        void reset();
    };

    std::vector<Point> path_;
    int current_waypoint_idx_{0};
    
    PIDController lateral_pid_;
    PIDController heading_pid_;
    PIDController altitude_pid_;
    
    mutable TrackError last_error_{0, 0, 0, 0};
};

}  // namespace uav_sdk

#endif  // TRAJECTORY_CORRECTOR_H
