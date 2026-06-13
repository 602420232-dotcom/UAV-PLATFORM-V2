#pragma once

/// @file path_planner.h
/// @brief 路径规划接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <memory>
#include <vector>
#include <functional>

namespace uav::edge {

// ============================================================================
// 路径规划抽象接口
// ============================================================================

/// 路径规划器抽象基类
/// 所有路径规划算法需实现此接口
class IPathPlanner {
public:
    virtual ~IPathPlanner() = default;

    /// 初始化规划器
    /// @param config 配置参数
    virtual void initialize(const std::string& config) = 0;

    /// 设置障碍物列表
    /// @param obstacles 障碍物集合
    virtual void set_obstacles(const std::vector<Obstacle>& obstacles) = 0;

    /// 设置禁飞区（多边形顶点列表）
    /// @param no_fly_zones 禁飞区集合，每个禁飞区由一组顶点定义
    virtual void set_no_fly_zones(const std::vector<std::vector<Position>>& no_fly_zones) = 0;

    /// 执行路径规划
    /// @param start 起始位置
    /// @param goal 目标位置
    /// @param max_altitude 最大飞行高度 (m)
    /// @param min_altitude 最小飞行高度 (m)
    /// @return 航路点序列，规划失败时返回空
    virtual std::vector<Waypoint> plan(
        const Position& start,
        const Position& goal,
        double max_altitude = 120.0,
        double min_altitude = 10.0
    ) = 0;

    /// 检查路径是否有效（无碰撞、在高度限制内）
    /// @param waypoints 待检查的航路点序列
    /// @return 路径是否有效
    virtual bool validate_path(const std::vector<Waypoint>& waypoints) const = 0;

    /// 获取上一次规划的计算耗时 (ms)
    [[nodiscard]] virtual double last_planning_time_ms() const = 0;

    /// 获取规划器名称
    [[nodiscard]] virtual std::string name() const = 0;
};

// ============================================================================
// A* 路径规划器
// ============================================================================

/// A* 路径规划器
/// 基于栅格化地图的 A* 搜索算法，适用于已知静态环境
class AStarPlanner : public IPathPlanner {
public:
    /// 构造函数
    /// @param resolution 栅格分辨率 (m)，默认 1.0m
    explicit AStarPlanner(double resolution = 1.0);

    void initialize(const std::string& config) override;
    void set_obstacles(const std::vector<Obstacle>& obstacles) override;
    void set_no_fly_zones(const std::vector<std::vector<Position>>& no_fly_zones) override;
    std::vector<Waypoint> plan(
        const Position& start,
        const Position& goal,
        double max_altitude = 120.0,
        double min_altitude = 10.0
    ) override;
    bool validate_path(const std::vector<Waypoint>& waypoints) const override;
    [[nodiscard]] double last_planning_time_ms() const override;
    [[nodiscard]] std::string name() const override { return "AStarPlanner"; }

    /// 设置启发式权重（>1 偏向速度，<1 偏向最优）
    void set_heuristic_weight(double weight);

    /// 设置是否启用路径平滑（B样条）
    void enable_smoothing(bool enable);

private:
    double resolution_;            ///< 栅格分辨率
    double heuristic_weight_;     ///< 启发式权重
    bool smoothing_enabled_;     ///< 是否启用路径平滑
    std::vector<Obstacle> obstacles_; ///< 障碍物列表
    std::vector<std::vector<Position>> no_fly_zones_; ///< 禁飞区
    double last_planning_time_ms_; ///< 上次规划耗时

    /// 构建栅格地图
    void build_grid();

    /// A* 搜索核心
    std::vector<Position> search(const Position& start, const Position& goal);

    /// B样条路径平滑
    std::vector<Position> smooth_path(const std::vector<Position>& raw_path);
};

// ============================================================================
// RRT* 路径规划器
// ============================================================================

/// RRT* (快速随机树星) 路径规划器
/// 基于采样的最优路径规划算法，适用于高维空间和复杂障碍环境
class RRTStarPlanner : public IPathPlanner {
public:
    /// 构造函数
    /// @param max_iterations 最大采样迭代次数
    /// @param step_size 树扩展步长 (m)
    /// @param goal_bias 目标偏向概率 (0-1)
    explicit RRTStarPlanner(
        uint32_t max_iterations = 5000,
        double step_size = 5.0,
        double goal_bias = 0.1
    );

    void initialize(const std::string& config) override;
    void set_obstacles(const std::vector<Obstacle>& obstacles) override;
    void set_no_fly_zones(const std::vector<std::vector<Position>>& no_fly_zones) override;
    std::vector<Waypoint> plan(
        const Position& start,
        const Position& goal,
        double max_altitude = 120.0,
        double min_altitude = 10.0
    ) override;
    bool validate_path(const std::vector<Waypoint>& waypoints) const override;
    [[nodiscard]] double last_planning_time_ms() const override;
    [[nodiscard]] std::string name() const override { return "RRTStarPlanner"; }

    /// 设置重连半径
    void set_rewire_radius(double radius);

    /// 设置是否启用路径优化
    void enable_optimization(bool enable);

private:
    uint32_t max_iterations_;     ///< 最大迭代次数
    double step_size_;            ///< 扩展步长
    double goal_bias_;            ///< 目标偏向概率
    double rewire_radius_;        ///< 重连半径
    bool optimization_enabled_;   ///< 是否启用路径优化
    std::vector<Obstacle> obstacles_; ///< 障碍物列表
    std::vector<std::vector<Position>> no_fly_zones_; ///< 禁飞区
    double last_planning_time_ms_; ///< 上次规划耗时

    /// 碰撞检测
    bool is_collision_free(const Position& p1, const Position& p2) const;

    /// 采样随机点
    Position sample_random(const Position& goal) const;

    /// 找到最近节点
    size_t find_nearest(const std::vector<Position>& nodes, const Position& point) const;

    /// 路径后处理优化
    std::vector<Position> optimize_path(const std::vector<Position>& raw_path);
};

// ============================================================================
// 工厂函数
// ============================================================================

/// 创建路径规划器实例
/// @param algorithm 算法名称 ("astar" 或 "rrt_star")
/// @return 路径规划器智能指针
std::unique_ptr<IPathPlanner> create_path_planner(const std::string& algorithm);

} // namespace uav::edge
