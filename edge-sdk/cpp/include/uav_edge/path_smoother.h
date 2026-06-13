#pragma once

/// @file path_smoother.h
/// @brief 路径平滑器接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <vector>

namespace uav::edge {

// ============================================================================
// 路径平滑器
// ============================================================================

/// 路径平滑器
/// 提供多种路径平滑算法：Bezier曲线、Catmull-Rom样条、Douglas-Peucker简化
class PathSmoother {
public:
    PathSmoother() = default;
    ~PathSmoother() = default;

    // ========================================================================
    // Bezier 曲线平滑
    // ========================================================================

    /// Bezier 曲线平滑
    /// @param path 输入航路点序列
    /// @param smoothness 平滑度 (3-10)，值越大越平滑
    /// @return 平滑后的航路点序列
    std::vector<Waypoint> bezier_smooth(
        const std::vector<Waypoint>& path,
        int smoothness = 5
    );

    // ========================================================================
    // Catmull-Rom 样条插值
    // ========================================================================

    /// Catmull-Rom 样条插值
    /// @param path 输入航路点序列
    /// @param num_samples 每段插值采样点数
    /// @return 插值后的航路点序列
    std::vector<Waypoint> catmull_rom_smooth(
        const std::vector<Waypoint>& path,
        int num_samples = 10
    );

    // ========================================================================
    // Douglas-Peucker 路径简化
    // ========================================================================

    /// Douglas-Peucker 路径简化
    /// @param path 输入航路点序列
    /// @param epsilon 简化容差 (m)
    /// @return 简化后的航路点序列
    std::vector<Waypoint> douglas_peucker_simplify(
        const std::vector<Waypoint>& path,
        double epsilon = 1.0
    );

    // ========================================================================
    // 备选路径生成
    // ========================================================================

    /// 生成备选路径
    /// @param path 主路径
    /// @param num_alternatives 备选数量
    /// @param offset 偏移量 (m)
    /// @return 备选路径列表
    std::vector<std::vector<Waypoint>> generate_alternatives(
        const std::vector<Waypoint>& path,
        int num_alternatives = 3,
        double offset = 5.0
    );

private:
    /// Bezier 曲线求值 (de Casteljau 算法)
    Position bezier_point(const std::vector<Position>& control_points, double t) const;

    /// 线性插值
    Position lerp(const Position& a, const Position& b, double t) const;

    /// 计算两点距离
    double distance(const Position& a, const Position& b) const;

    /// 点到线段距离
    double point_to_segment_distance(
        const Position& p,
        const Position& a,
        const Position& b
    ) const;
};

} // namespace uav::edge
