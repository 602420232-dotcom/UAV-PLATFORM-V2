/// @file path_smoother.cpp
/// @brief 路径平滑器实现（Bezier / Catmull-Rom / Douglas-Peucker）
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/path_smoother.h"

#include <cmath>
#include <algorithm>
#include <limits>

namespace uav::edge {

// ============================================================================
// 辅助方法
// ============================================================================

double PathSmoother::distance(const Position& a, const Position& b) const {
    return a.distance_to(b);
}

Position PathSmoother::lerp(const Position& a, const Position& b, double t) const {
    t = std::clamp(t, 0.0, 1.0);
    return Position{
        a.x + t * (b.x - a.x),
        a.y + t * (b.y - a.y),
        a.z + t * (b.z - a.z)
    };
}

Position PathSmoother::bezier_point(
    const std::vector<Position>& control_points, double t
) const {
    if (control_points.empty()) {
        return Position{};
    }

    // de Casteljau 算法：递归线性插值
    std::vector<Position> points = control_points;

    while (points.size() > 1) {
        std::vector<Position> next;
        next.reserve(points.size() - 1);
        for (size_t i = 0; i < points.size() - 1; ++i) {
            next.push_back(lerp(points[i], points[i + 1], t));
        }
        points = std::move(next);
    }

    return points[0];
}

double PathSmoother::point_to_segment_distance(
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
// Bezier 曲线平滑
// ============================================================================

std::vector<Waypoint> PathSmoother::bezier_smooth(
    const std::vector<Waypoint>& path,
    int smoothness
) {
    if (path.size() < 2) {
        return path;
    }

    smoothness = std::clamp(smoothness, 3, 10);
    std::vector<Waypoint> result;

    // 对每对相邻航点使用三次 Bezier 曲线插值
    for (size_t i = 0; i < path.size() - 1; ++i) {
        const Position& p0 = path[i].position;
        const Position& p3 = path[i + 1].position;

        // 计算辅助控制点
        Position p1, p2;

        if (i == 0) {
            // 第一段：简单方向控制点
            p1.x = p0.x + (p3.x - p0.x) / 3.0;
            p1.y = p0.y + (p3.y - p0.y) / 3.0;
            p1.z = p0.z + (p3.z - p0.z) / 3.0;
            p2.x = p0.x + 2.0 * (p3.x - p0.x) / 3.0;
            p2.y = p0.y + 2.0 * (p3.y - p0.y) / 3.0;
            p2.z = p0.z + 2.0 * (p3.z - p0.z) / 3.0;
        } else {
            // 使用前一个点确定切线方向
            const Position& prev = path[i - 1].position;
            double dx = (p3.x - prev.x) / 6.0;
            double dy = (p3.y - prev.y) / 6.0;
            double dz = (p3.z - prev.z) / 6.0;
            p1.x = p0.x + dx;
            p1.y = p0.y + dy;
            p1.z = p0.z + dz;
            p2.x = p3.x - dx;
            p2.y = p3.y - dy;
            p2.z = p3.z - dz;
        }

        // 构造控制点序列
        std::vector<Position> control_points = {p0, p1, p2, p3};

        // 沿曲线采样
        for (int s = 0; s < smoothness; ++s) {
            double t = static_cast<double>(s) / smoothness;
            Position pt = bezier_point(control_points, t);

            // 去重：避免添加与上一个点重合的点
            if (result.empty() ||
                distance(pt, result.back().position) > 0.01) {
                Waypoint wp;
                wp.position = pt;
                result.push_back(wp);
            }
        }
    }

    // 确保终点被包含
    if (result.empty() ||
        distance(path.back().position, result.back().position) > 0.01) {
        result.push_back(path.back());
    }

    return result;
}

// ============================================================================
// Catmull-Rom 样条插值
// ============================================================================

std::vector<Waypoint> PathSmoother::catmull_rom_smooth(
    const std::vector<Waypoint>& path,
    int num_samples
) {
    if (path.size() < 2) {
        return path;
    }

    num_samples = std::max(num_samples, 2);
    std::vector<Waypoint> result;

    // Catmull-Rom 样条：对每对相邻控制点 Pi 和 Pi+1
    // 使用 Pi-1, Pi, Pi+1, Pi+2 四个控制点计算插值
    for (size_t i = 0; i < path.size() - 1; ++i) {
        // 确定四个控制点
        Position p0, p1, p2, p3;

        p1 = path[i].position;
        p2 = path[i + 1].position;

        // 边界处理：首尾点重复
        if (i == 0) {
            p0 = p1;
        } else {
            p0 = path[i - 1].position;
        }

        if (i + 2 >= path.size()) {
            p3 = p2;
        } else {
            p3 = path[i + 2].position;
        }

        // 在两个控制点之间采样
        for (int s = 0; s < num_samples; ++s) {
            double t = static_cast<double>(s) / num_samples;

            // Catmull-Rom 基函数矩阵
            double t2 = t * t;
            double t3 = t2 * t;

            // x 分量
            double x = 0.5 * (
                (2.0 * p1.x) +
                (-p0.x + p2.x) * t +
                (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2 +
                (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3
            );

            // y 分量
            double y = 0.5 * (
                (2.0 * p1.y) +
                (-p0.y + p2.y) * t +
                (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2 +
                (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3
            );

            // z 分量
            double z = 0.5 * (
                (2.0 * p1.z) +
                (-p0.z + p2.z) * t +
                (2.0 * p0.z - 5.0 * p1.z + 4.0 * p2.z - p3.z) * t2 +
                (-p0.z + 3.0 * p1.z - 3.0 * p2.z + p3.z) * t3
            );

            Waypoint wp;
            wp.position = Position{x, y, z};

            // 去重
            if (result.empty() ||
                distance(wp.position, result.back().position) > 0.01) {
                result.push_back(wp);
            }
        }
    }

    // 确保终点被包含
    if (result.empty() ||
        distance(path.back().position, result.back().position) > 0.01) {
        result.push_back(path.back());
    }

    return result;
}

// ============================================================================
// Douglas-Peucker 路径简化
// ============================================================================

std::vector<Waypoint> PathSmoother::douglas_peucker_simplify(
    const std::vector<Waypoint>& path,
    double epsilon
) {
    if (path.size() <= 2) {
        return path;
    }

    // 找到距离首尾连线最远的点
    double max_dist = 0.0;
    size_t max_idx = 0;

    const Position& start = path.front().position;
    const Position& end = path.back().position;

    for (size_t i = 1; i < path.size() - 1; ++i) {
        double dist = point_to_segment_distance(
            path[i].position, start, end
        );

        if (dist > max_dist) {
            max_dist = dist;
            max_idx = i;
        }
    }

    // 如果最大距离小于容差，只保留首尾点
    if (max_dist < epsilon) {
        std::vector<Waypoint> simplified;
        simplified.push_back(path.front());
        simplified.push_back(path.back());
        return simplified;
    }

    // 递归简化两个子段
    std::vector<Waypoint> left(path.begin(), path.begin() + max_idx + 1);
    std::vector<Waypoint> right(path.begin() + max_idx, path.end());

    auto simplified_left = douglas_peucker_simplify(left, epsilon);
    auto simplified_right = douglas_peucker_simplify(right, epsilon);

    // 合并结果（去掉右侧重复的起点）
    std::vector<Waypoint> result = simplified_left;
    result.insert(result.end(), simplified_right.begin() + 1, simplified_right.end());

    return result;
}

// ============================================================================
// 备选路径生成
// ============================================================================

std::vector<std::vector<Waypoint>> PathSmoother::generate_alternatives(
    const std::vector<Waypoint>& path,
    int num_alternatives,
    double offset
) {
    std::vector<std::vector<Waypoint>> alternatives;

    if (path.size() < 2) {
        alternatives.push_back(path);
        return alternatives;
    }

    num_alternatives = std::max(num_alternatives, 1);

    // 生成不同偏移量的备选路径
    for (int alt = 0; alt < num_alternatives; ++alt) {
        // 偏移量：正负交替，逐渐增大
        double current_offset = offset * (1.0 + static_cast<double>(alt) * 0.5);
        if (alt % 2 == 1) {
            current_offset = -current_offset;
        }

        std::vector<Waypoint> alternative;
        alternative.reserve(path.size());

        for (size_t i = 0; i < path.size(); ++i) {
            // 计算该点的法线方向（垂直于路径方向）
            double nx = 0.0, ny = 0.0;

            if (i == 0) {
                // 起点：使用第一个线段的方向
                double dx = path[i + 1].position.x - path[i].position.x;
                double dy = path[i + 1].position.y - path[i].position.y;
                double len = std::sqrt(dx * dx + dy * dy);
                if (len > 1e-6) {
                    nx = -dy / len; // 法线方向
                    ny = dx / len;
                }
            } else if (i == path.size() - 1) {
                // 终点：使用最后一个线段的方向
                double dx = path[i].position.x - path[i - 1].position.x;
                double dy = path[i].position.y - path[i - 1].position.y;
                double len = std::sqrt(dx * dx + dy * dy);
                if (len > 1e-6) {
                    nx = -dy / len;
                    ny = dx / len;
                }
            } else {
                // 中间点：使用前后线段方向的平均
                double dx1 = path[i].position.x - path[i - 1].position.x;
                double dy1 = path[i].position.y - path[i - 1].position.y;
                double len1 = std::sqrt(dx1 * dx1 + dy1 * dy1);

                double dx2 = path[i + 1].position.x - path[i].position.x;
                double dy2 = path[i + 1].position.y - path[i].position.y;
                double len2 = std::sqrt(dx2 * dx2 + dy2 * dy2);

                if (len1 > 1e-6 && len2 > 1e-6) {
                    double avg_dx = dx1 / len1 + dx2 / len2;
                    double avg_dy = dy1 / len1 + dy2 / len2;
                    double avg_len = std::sqrt(avg_dx * avg_dx + avg_dy * avg_dy);
                    if (avg_len > 1e-6) {
                        nx = -avg_dy / avg_len;
                        ny = avg_dx / avg_len;
                    }
                }
            }

            // 沿法线方向偏移
            Waypoint wp = path[i];
            wp.position.x += nx * current_offset;
            wp.position.y += ny * current_offset;
            alternative.push_back(wp);
        }

        alternatives.push_back(alternative);
    }

    return alternatives;
}

} // namespace uav::edge
