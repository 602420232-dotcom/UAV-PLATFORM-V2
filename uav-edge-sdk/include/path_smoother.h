#ifndef PATH_SMOOTHER_H
#define PATH_SMOOTHER_H

#include <vector>
#include <cmath>
#include "path_planner.h"

namespace uav_sdk {

/**
 * @brief 路径平滑器
 * 
 * 使用Bezier曲线平滑路径，并提供多路径备选
 */
class PathSmoother {
public:
    PathSmoother();
    ~PathSmoother();

    /**
     * @brief Bezier曲线平滑
     * @param input_path 输入路径
     * @param smoothness 平滑度 (3-10)
     * @return 平滑后的路径
     */
    std::vector<Point> bezier_smooth(const std::vector<Point>& input_path,
                                      int smoothness = 5);

    /**
     * @brief 三次样条插值
     * @param input_path 输入路径
     * @param num_samples 采样点数
     * @return 插值后的路径
     */
    std::vector<Point> spline_smooth(const std::vector<Point>& input_path,
                                      int num_samples = 50);

    /**
     * @brief 生成多路径备选
     * @param path 主路径
     * @param num_alternatives 备选数量
     * @param offset 偏移量
     * @return 备选路径列表
     */
    std::vector<std::vector<Point>> generate_alternatives(
        const std::vector<Point>& path,
        int num_alternatives = 3,
        double offset = 2.0);

    /**
     * @brief 简化路径（减少点数）
     * @param path 输入路径
     * @param epsilon 简化精度
     * @return 简化后的路径
     */
    std::vector<Point> simplify_path(const std::vector<Point>& path,
                                      double epsilon = 1.0);

private:
    /**
     * @brief 计算Bezier曲线上的点
     */
    Point bezier_point(const std::vector<Point>& control_points, double t) const;

    /**
     * @brief 计算两点距离
     */
    double distance(const Point& a, const Point& b) const;

    /**
     * @brief 线性插值
     */
    Point lerp(const Point& a, const Point& b, double t) const;
};

}  // namespace uav_sdk

#endif  // PATH_SMOOTHER_H
