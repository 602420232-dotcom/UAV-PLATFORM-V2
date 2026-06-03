#ifndef DWA_PLANNER_H
#define DWA_PLANNER_H

#include <vector>
#include <cmath>
#include <algorithm>
#include <functional>
#include "path_planner.h"

namespace uav_sdk {

/**
 * @brief 速度采样空间
 */
struct VelocitySpace {
    double v_min, v_max;           // 线速度范围 (m/s)
    double w_min, w_max;          // 角速度范围 (rad/s)
    double v_resolution;           // 线速度分辨率
    double w_resolution;           // 角速度分辨率
};

/**
 * @brief 轨迹预测参数
 */
struct DWAParams {
    double dt = 0.1;               // 模拟时间步长 (s)
    double predict_time = 3.0;     // 预测时间 (s)
    double max_accel = 0.5;        // 最大线加速度 (m/s²)
    double max_angular_accel = 1.0; // 最大角加速度 (rad/s²)
    double v_max = 0.5;            // 最大线速度 (m/s)
    double v_min = 0.0;            // 最小线速度
    double w_max = 1.0;            // 最大角速度 (rad/s)
    double w_min = -1.0;           // 最小角速度
    
    // 成本函数权重
    double alpha = 0.05;           // 目标方向偏差权重
    double beta = 0.2;             // 障碍物距离权重
    double gamma = 0.1;            // 速度权重
    double obstacle_radius = 0.5;  // 障碍物膨胀半径 (m)
    double goal_radius = 0.3;      // 到达目标半径 (m)
};

/**
 * @brief 轨迹点
 */
struct TrajectoryPoint {
    double x, y;                   // 位置 (m)
    double yaw;                    // 朝向 (rad)
    double v;                      // 线速度 (m/s)
    double w;                      // 角速度 (rad/s)
};

/**
 * @brief 轨迹
 */
struct Trajectory {
    std::vector<TrajectoryPoint> points;
    double cost;                   // 总成本
    double v;                      // 使用的线速度
    double w;                      // 使用的角速度
    bool is_valid;                 // 是否有效（未碰撞）
};

/**
 * @brief DWA 局部避障规划器
 * 
 * Dynamic Window Approach (DWA) 避障算法
 * 在速度空间搜索最优避障轨迹
 */
class DWAPlanner {
public:
    DWAPlanner();
    ~DWAPlanner();

    /**
     * @brief 设置参数
     */
    void set_params(const DWAParams& params);
    DWAParams get_params() const;

    /**
     * @brief 规划局部轨迹
     * @param current_x 当前x
     * @param current_y 当前y
     * @param current_yaw 当前朝向
     * @param current_v 当前线速度
     * @param current_w 当前角速度
     * @param goal_x 目标x
     * @param goal_y 目标y
     * @param obstacles 障碍物点集
     * @return 最优轨迹
     */
    Trajectory plan(double current_x, double current_y, double current_yaw,
                    double current_v, double current_w,
                    double goal_x, double goal_y,
                    const std::vector<Point>& obstacles);

    /**
     * @brief 预测轨迹
     * @param x0, y0, yaw0 初始状态
     * @param v, w 速度控制
     * @return 预测轨迹
     */
    Trajectory predict_trajectory(double x0, double y0, double yaw0,
                                   double v, double w) const;

private:
    /**
     * @brief 计算动态窗口
     * @param current_v, current_w 当前速度
     * @return 可达速度空间
     */
    VelocitySpace calc_dynamic_window(double current_v, double current_w) const;

    /**
     * @brief 轨迹成本函数
     */
    double calc_heading_cost(const Trajectory& traj, double gx, double gy) const;
    double calc_obstacle_cost(const Trajectory& traj, const std::vector<Point>& obstacles) const;
    double calc_velocity_cost(const Trajectory& traj) const;

    DWAParams params_;
};

}  // namespace uav_sdk

#endif  // DWA_PLANNER_H
