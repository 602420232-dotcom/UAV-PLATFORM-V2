#include "path_smoother.h"
#include <cmath>
#include <algorithm>
#include <limits>
#include <stdexcept>

namespace uav_sdk {

PathSmoother::PathSmoother() = default;
PathSmoother::~PathSmoother() = default;

double PathSmoother::distance(const Point& a, const Point& b) const {
    double dx = static_cast<double>(a.x - b.x);
    double dy = static_cast<double>(a.y - b.y);
    return std::sqrt(dx * dx + dy * dy);
}

Point PathSmoother::lerp(const Point& a, const Point& b, double t) const {
    t = std::clamp(t, 0.0, 1.0);
    int x = static_cast<int>(std::round(static_cast<double>(a.x) + t * static_cast<double>(b.x - a.x)));
    int y = static_cast<int>(std::round(static_cast<double>(a.y) + t * static_cast<double>(b.y - a.y)));
    return Point(x, y);
}

Point PathSmoother::bezier_point(const std::vector<Point>& control_points, double t) const {
    if (control_points.empty()) {
        return Point(0, 0);
    }

    // de Casteljau 算法
    std::vector<Point> points = control_points;

    while (points.size() > 1) {
        std::vector<Point> next;
        for (size_t i = 0; i < points.size() - 1; ++i) {
            next.push_back(lerp(points[i], points[i + 1], t));
        }
        points = next;
    }

    return points.empty() ? Point(0, 0) : points[0];
}

std::vector<Point> PathSmoother::bezier_smooth(const std::vector<Point>& input_path,
                                                 int smoothness) {
    if (input_path.size() < 2) {
        return input_path;
    }

    smoothness = std::clamp(smoothness, 3, 10);
    std::vector<Point> result;

    // 对每对相邻航点使用贝塞尔曲线插值
    for (size_t i = 0; i < input_path.size() - 1; ++i) {
        std::vector<Point> control_points;

        // 生成控制点：当前点和下一个点，以及前后相邻点
        Point p0 = input_path[i];
        Point p3 = input_path[i + 1];

        // 计算辅助控制点（方向向量）
        Point p1, p2;
        if (i == 0) {
            // 第一个段：使用起点自身作为第一个控制点
            double dx = static_cast<double>(p3.x - p0.x) / 3.0;
            double dy = static_cast<double>(p3.y - p0.y) / 3.0;
            p1 = Point(static_cast<int>(std::round(static_cast<double>(p0.x) + dx)),
                       static_cast<int>(std::round(static_cast<double>(p0.y) + dy)));
            p2 = Point(static_cast<int>(std::round(static_cast<double>(p3.x) - dx)),
                       static_cast<int>(std::round(static_cast<double>(p3.y) - dy)));
        } else {
            // 使用前一个点来帮助确定方向
            Point prev = input_path[i - 1];
            double dx1 = static_cast<double>(p3.x - prev.x) / 6.0;
            double dy1 = static_cast<double>(p3.y - prev.y) / 6.0;
            p1 = Point(static_cast<int>(std::round(static_cast<double>(p0.x) + dx1)),
                       static_cast<int>(std::round(static_cast<double>(p0.y) + dy1)));

            double dx2 = static_cast<double>(p3.x - prev.x) / 6.0;
            double dy2 = static_cast<double>(p3.y - prev.y) / 6.0;
            p2 = Point(static_cast<int>(std::round(static_cast<double>(p3.x) - dx2)),
                       static_cast<int>(std::round(static_cast<double>(p3.y) - dy2)));
        }

        control_points.push_back(p0);
        control_points.push_back(p1);
        control_points.push_back(p2);
        control_points.push_back(p3);

        // 沿曲线采样
        int num_samples = smoothness;
        for (int s = 0; s < num_samples; ++s) {
            double t = static_cast<double>(s) / static_cast<double>(num_samples);
            Point pt = bezier_point(control_points, t);
            // 去重
            if (result.empty() || pt != result.back()) {
                result.push_back(pt);
            }
        }
    }

    // 确保终点被包含
    if (result.empty() || result.back() != input_path.back()) {
        result.push_back(input_path.back());
    }

    return result;
}

std::vector<Point> PathSmoother::spline_smooth(const std::vector<Point>& input_path,
                                                 int num_samples) {
    if (input_path.size() < 2) {
        return input_path;
    }

    num_samples = std::max(num_samples, static_cast<int>(input_path.size()));
    std::vector<Point> result;

    // Catmull-Rom 样条插值
    // 对于每对相邻控制点 Pi 和 Pi+1，使用 Pi-1, Pi, Pi+1, Pi+2 计算
    for (size_t i = 0; i < input_path.size() - 1; ++i) {
        // 确定四个控制点
        Point p0, p1, p2, p3;

        p1 = input_path[i];
        p2 = input_path[i + 1];

        if (i == 0) {
            p0 = p1;  // 起始点重复第一个点
        } else {
            p0 = input_path[i - 1];
        }

        if (i + 2 >= input_path.size()) {
            p3 = p2;  // 终点重复最后一个点
        } else {
            p3 = input_path[i + 2];
        }

        // 在两个控制点之间采样
        int segment_samples = num_samples / static_cast<int>(input_path.size() - 1);
        if (segment_samples < 1) segment_samples = 1;

        for (int s = 0; s < segment_samples; ++s) {
            double t = static_cast<double>(s) / static_cast<double>(segment_samples);

            // Catmull-Rom 基函数
            double t2 = t * t;
            double t3 = t2 * t;

            double x = 0.5 * (
                (2.0 * p1.x) +
                (-p0.x + p2.x) * t +
                (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2 +
                (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3
            );

            double y = 0.5 * (
                (2.0 * p1.y) +
                (-p0.y + p2.y) * t +
                (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2 +
                (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3
            );

            Point pt(static_cast<int>(std::round(x)),
                     static_cast<int>(std::round(y)));

            if (result.empty() || pt != result.back()) {
                result.push_back(pt);
            }
        }
    }

    // 确保终点被包含
    if (result.empty() || result.back() != input_path.back()) {
        result.push_back(input_path.back());
    }

    return result;
}

std::vector<Point> PathSmoother::simplify_path(const std::vector<Point>& path,
                                                 double epsilon) {
    if (path.size() <= 2) {
        return path;
    }

    // Douglas-Peucker 算法
    // 找到距离首尾连线最远的点
    double max_dist = 0.0;
    int max_idx = 0;

    double line_dx = static_cast<double>(path.back().x - path.front().x);
    double line_dy = static_cast<double>(path.back().y - path.front().y);
    double line_len_sq = line_dx * line_dx + line_dy * line_dy;

    for (size_t i = 1; i < path.size() - 1; ++i) {
        double dist = 0.0;

        if (line_len_sq == 0.0) {
            // 首尾重合，使用欧氏距离
            double dx = static_cast<double>(path[i].x - path.front().x);
            double dy = static_cast<double>(path[i].y - path.front().y);
            dist = std::sqrt(dx * dx + dy * dy);
        } else {
            // 点到直线的垂直距离
            double t = ((static_cast<double>(path[i].x - path.front().x) * line_dx +
                         static_cast<double>(path[i].y - path.front().y) * line_dy)) / line_len_sq;
            t = std::clamp(t, 0.0, 1.0);
            double proj_x = static_cast<double>(path.front().x) + t * line_dx;
            double proj_y = static_cast<double>(path.front().y) + t * line_dy;
            double dx = static_cast<double>(path[i].x) - proj_x;
            double dy = static_cast<double>(path[i].y) - proj_y;
            dist = std::sqrt(dx * dx + dy * dy);
        }

        if (dist > max_dist) {
            max_dist = dist;
            max_idx = static_cast<int>(i);
        }
    }

    // 如果最大距离小于 epsilon，只保留首尾点
    if (max_dist < epsilon) {
        return {path.front(), path.back()};
    }

    // 否则递归简化两个子段
    std::vector<Point> left(path.begin(), path.begin() + max_idx + 1);
    std::vector<Point> right(path.begin() + max_idx, path.end());

    std::vector<Point> simplified_left = simplify_path(left, epsilon);
    std::vector<Point> simplified_right = simplify_path(right, epsilon);

    // 合并结果（去掉右侧的重复起点）
    std::vector<Point> result = simplified_left;
    result.insert(result.end(), simplified_right.begin() + 1, simplified_right.end());

    return result;
}

std::vector<std::vector<Point>> PathSmoother::generate_alternatives(
    const std::vector<Point>& path,
    int num_alternatives,
    double offset) {
    std::vector<std::vector<Point>> alternatives;

    if (path.size() < 2) {
        alternatives.push_back(path);
        return alternatives;
    }

    num_alternatives = std::max(num_alternatives, 1);

    // 生成不同偏移量的备选路径
    for (int alt = 0; alt < num_alternatives; ++alt) {
        // 计算当前备选的偏移量：正负交替，逐渐增大
        double current_offset = offset * (1.0 + static_cast<double>(alt) * 0.5);
        if (alt % 2 == 1) {
            current_offset = -current_offset;
        }

        std::vector<Point> alternative;

        for (size_t i = 0; i < path.size(); ++i) {
            // 计算该点的法线方向
            double nx = 0.0, ny = 0.0;

            if (i == 0) {
                // 起点：使用第一个线段的方向
                double dx = static_cast<double>(path[i + 1].x - path[i].x);
                double dy = static_cast<double>(path[i + 1].y - path[i].y);
                double len = std::sqrt(dx * dx + dy * dy);
                if (len > 0.0) {
                    nx = -dy / len;
                    ny = dx / len;
                }
            } else if (i == path.size() - 1) {
                // 终点：使用最后一个线段的方向
                double dx = static_cast<double>(path[i].x - path[i - 1].x);
                double dy = static_cast<double>(path[i].y - path[i - 1].y);
                double len = std::sqrt(dx * dx + dy * dy);
                if (len > 0.0) {
                    nx = -dy / len;
                    ny = dx / len;
                }
            } else {
                // 中间点：使用前后线段方向的平均
                double dx1 = static_cast<double>(path[i].x - path[i - 1].x);
                double dy1 = static_cast<double>(path[i].y - path[i - 1].y);
                double len1 = std::sqrt(dx1 * dx1 + dy1 * dy1);

                double dx2 = static_cast<double>(path[i + 1].x - path[i].x);
                double dy2 = static_cast<double>(path[i + 1].y - path[i].y);
                double len2 = std::sqrt(dx2 * dx2 + dy2 * dy2);

                if (len1 > 0.0 && len2 > 0.0) {
                    double avg_dx = dx1 / len1 + dx2 / len2;
                    double avg_dy = dy1 / len1 + dy2 / len2;
                    double avg_len = std::sqrt(avg_dx * avg_dx + avg_dy * avg_dy);
                    if (avg_len > 0.0) {
                        nx = -avg_dy / avg_len;
                        ny = avg_dx / avg_len;
                    }
                }
            }

            int new_x = static_cast<int>(std::round(static_cast<double>(path[i].x) + nx * current_offset));
            int new_y = static_cast<int>(std::round(static_cast<double>(path[i].y) + ny * current_offset));
            alternative.push_back(Point(new_x, new_y));
        }

        alternatives.push_back(alternative);
    }

    return alternatives;
}

}  // namespace uav_sdk
