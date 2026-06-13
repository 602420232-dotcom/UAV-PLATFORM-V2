#pragma once

/// @file dwa_planner.h
/// @brief DWA 局部路径规划器接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <vector>
#include <string>

namespace uav::edge {

// ============================================================================
// DWA 规划参数
// ============================================================================

/// DWA (Dynamic Window Approach) 规划参数
struct DWAParams {
    double dt{0.1};                ///< 模拟时间步长 (s)
    double predict_time{3.0};      ///< 预测时间 (s)
    double max_accel{0.5};         ///< 最大线加速度 (m/s^2)
    double max_angular_accel{1.0}; ///< 最大角加速度 (rad/s^2)
    double v_max{5.0};             ///< 最大线速度 (m/s)
    double v_min{0.0};             ///< 最小线速度 (m/s)
    double w_max{1.0};             ///< 最大角速度 (rad/s)
    double w_min{-1.0};            ///< 最小角速度 (rad/s)

    /// 成本函数权重
    double alpha{0.05};            ///< 目标方向偏差权重
    double beta{0.2};              ///< 障碍物距离权重
    double gamma{0.1};             ///< 速度权重
    double obstacle_radius{0.5};   ///< 障碍物膨胀半径 (m)
    double goal_radius{0.3};       ///< 到达目标半径 (m)
};

// ============================================================================
// 轨迹数据结构
// ============================================================================

/// 轨迹点
struct TrajectoryPoint {
    double x{0.0};  ///< 位置 x (m)
    double y{0.0};  ///< 位置 y (m)
    double z{0.0};  ///< 位置 z (m)
    double yaw{0.0}; ///< 朝向 (rad)
    double v{0.0};   ///< 线速度 (m/s)
    double w{0.0};   ///< 角速度 (rad/s)
};

/// 轨迹
struct Trajectory {
    std::vector<TrajectoryPoint> points; ///< 轨迹点序列
    double cost{0.0};   ///< 总成本
    double v{0.0};      ///< 使用的线速度 (m/s)
    double w{0.0};      ///< 使用的角速度 (rad/s)
    bool is_valid{false}; ///< 是否有效（未碰撞）
};

// ============================================================================
// DWA 局部规划器
// ============================================================================

/// DWA 局部路径规划器
/// Dynamic Window Approach (DWA) 避障算法
/// 在速度空间中搜索最优避障轨迹
class DWAPlanner {
public:
    DWAPlanner() = default;
    ~DWAPlanner() = default;

    /// 设置规划参数
    void set_params(const DWAParams& params);

    /// 获取当前参数
    [[nodiscard]] const DWAParams& get_params() const;

    /// 规划局部轨迹
    /// @param current 当前位置
    /// @param current_yaw 当前朝向 (rad)
    /// @param current_v 当前线速度 (m/s)
    /// @param current_w 当前角速度 (rad/s)
    /// @param goal 目标位置
    /// @param obstacles 障碍物列表
    /// @return 最优轨迹
    Trajectory plan(
        const Position& current,
        double current_yaw,
        double current_v,
        double current_w,
        const Position& goal,
        const std::vector<Obstacle>& obstacles
    );

    /// 预测轨迹
    /// @param x0, y0, z0, yaw0 初始状态
    /// @param v, w 速度控制
    /// @return 预测轨迹
    Trajectory predict_trajectory(
        double x0, double y0, double z0, double yaw0,
        double v, double w
    ) const;

    /// 获取规划器名称
    [[nodiscard]] std::string name() const { return "DWAPlanner"; }

private:
    DWAParams params_;

    /// 计算动态窗口（可达速度空间）
    struct VelocitySpace {
        double v_min, v_max;
        double w_min, w_max;
        double v_resolution;
        double w_resolution;
    };

    VelocitySpace calc_dynamic_window(double current_v, double current_w) const;

    /// 轨迹成本函数
    double calc_heading_cost(const Trajectory& traj, double gx, double gy) const;
    double calc_obstacle_cost(const Trajectory& traj, const std::vector<Obstacle>& obstacles) const;
    double calc_velocity_cost(const Trajectory& traj) const;
};

} // namespace uav::edge
