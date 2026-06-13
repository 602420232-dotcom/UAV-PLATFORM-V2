/// @file path_planner.cpp
/// @brief A* 和 RRT* 路径规划器实现
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/path_planner.h"

#include <cmath>
#include <queue>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>
#include <limits>
#include <numeric>
#include <random>
#include <chrono>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace uav::edge {

// ============================================================================
// 辅助类型：栅格坐标
// ============================================================================

namespace {

/// 栅格坐标
struct GridCoord {
    int64_t gx{0};
    int64_t gy{0};

    bool operator==(const GridCoord& other) const noexcept {
        return gx == other.gx && gy == other.gy;
    }
    bool operator!=(const GridCoord& other) const noexcept {
        return !(*this == other);
    }
};

/// 栅格坐标哈希函数
struct GridCoordHash {
    size_t operator()(const GridCoord& c) const noexcept {
        // 将两个 int64_t 组合成一个 size_t
        size_t h = static_cast<size_t>(c.gx);
        h ^= static_cast<size_t>(c.gy) + 0x9e3779b9 + (h << 6) + (h >> 2);
        return h;
    }
};

/// A* 搜索节点
struct AStarNode {
    GridCoord coord;
    double g_cost{0.0};  ///< 从起点到当前节点的实际代价
    double f_cost{0.0};  ///< g_cost + 启发式估计代价
    GridCoord parent;

    /// 优先队列比较：f_cost 越小优先级越高
    bool operator>(const AStarNode& other) const noexcept {
        return f_cost > other.f_cost;
    }
};

/// 检查点是否在禁飞区内
bool is_in_no_fly_zone(
    const Position& p,
    const std::vector<std::vector<Position>>& no_fly_zones
) {
    for (const auto& zone : no_fly_zones) {
        if (zone.size() < 3) continue;

        // 射线法判断点是否在多边形内
        bool inside = false;
        size_t n = zone.size();
        for (size_t i = 0, j = n - 1; i < n; j = i++) {
            if (((zone[i].y > p.y) != (zone[j].y > p.y)) &&
                (p.x < (zone[j].x - zone[i].x) * (p.y - zone[i].y) /
                 (zone[j].y - zone[i].y) + zone[i].x)) {
                inside = !inside;
            }
        }
        if (inside) return true;
    }
    return false;
}

/// 检查点是否与障碍物碰撞
bool is_collision(
    const Position& p,
    const std::vector<Obstacle>& obstacles,
    double safety_margin = 2.0
) {
    for (const auto& obs : obstacles) {
        double dx = p.x - obs.position.x;
        double dy = p.y - obs.position.y;
        double dist_2d = std::sqrt(dx * dx + dy * dy);
        double safe_radius = obs.radius + safety_margin;

        // 检查水平距离和高度
        if (dist_2d < safe_radius && p.z < obs.height + safety_margin) {
            return true;
        }
    }
    return false;
}

} // anonymous namespace

// ============================================================================
// AStarPlanner 实现
// ============================================================================

AStarPlanner::AStarPlanner(double resolution)
    : resolution_(resolution)
    , heuristic_weight_(1.0)
    , smoothing_enabled_(false)
    , last_planning_time_ms_(0.0)
{
}

void AStarPlanner::initialize(const std::string& config) {
    // 简单配置解析：格式 "resolution:1.0,weight:1.2,smoothing:true"
    // 暂不实现复杂 JSON 解析，使用默认值
    (void)config;
}

void AStarPlanner::set_obstacles(const std::vector<Obstacle>& obstacles) {
    obstacles_ = obstacles;
}

void AStarPlanner::set_no_fly_zones(const std::vector<std::vector<Position>>& no_fly_zones) {
    no_fly_zones_ = no_fly_zones;
}

void AStarPlanner::set_heuristic_weight(double weight) {
    heuristic_weight_ = (weight > 0.0) ? weight : 1.0;
}

void AStarPlanner::enable_smoothing(bool enable) {
    smoothing_enabled_ = enable;
}

std::vector<Waypoint> AStarPlanner::plan(
    const Position& start,
    const Position& goal,
    double max_altitude,
    double min_altitude
) {
    auto begin_time = std::chrono::steady_clock::now();

    std::vector<Waypoint> result;

    // 检查起点和终点是否有效
    if (is_collision(start, obstacles_) || is_collision(goal, obstacles_)) {
        last_planning_time_ms_ = 0.0;
        return result;
    }

    if (is_in_no_fly_zone(start, no_fly_zones_) ||
        is_in_no_fly_zone(goal, no_fly_zones_)) {
        last_planning_time_ms_ = 0.0;
        return result;
    }

    // 执行 A* 搜索
    std::vector<Position> raw_path = search(start, goal);

    if (raw_path.empty()) {
        last_planning_time_ms_ = 0.0;
        return result;
    }

    // 可选路径平滑
    if (smoothing_enabled_ && raw_path.size() > 2) {
        raw_path = smooth_path(raw_path);
    }

    // 转换为航路点序列
    for (const auto& pos : raw_path) {
        // 确保高度在限制范围内
        Waypoint wp;
        wp.position = pos;
        wp.position.z = std::clamp(pos.z, min_altitude, max_altitude);
        result.push_back(wp);
    }

    auto end_time = std::chrono::steady_clock::now();
    last_planning_time_ms_ = std::chrono::duration<double, std::milli>(
        end_time - begin_time).count();

    return result;
}

bool AStarPlanner::validate_path(const std::vector<Waypoint>& waypoints) const {
    if (waypoints.empty()) return false;

    for (const auto& wp : waypoints) {
        // 检查碰撞
        if (is_collision(wp.position, obstacles_)) {
            return false;
        }
        // 检查禁飞区
        if (is_in_no_fly_zone(wp.position, no_fly_zones_)) {
            return false;
        }
    }

    // 检查相邻航路点间是否有碰撞（简化：检查中点）
    for (size_t i = 0; i + 1 < waypoints.size(); ++i) {
        Position mid;
        mid.x = (waypoints[i].position.x + waypoints[i + 1].position.x) / 2.0;
        mid.y = (waypoints[i].position.y + waypoints[i + 1].position.y) / 2.0;
        mid.z = (waypoints[i].position.z + waypoints[i + 1].position.z) / 2.0;

        if (is_collision(mid, obstacles_)) {
            return false;
        }
    }

    return true;
}

double AStarPlanner::last_planning_time_ms() const {
    return last_planning_time_ms_;
}

// ============================================================================
// A* 核心搜索
// ============================================================================

void AStarPlanner::build_grid() {
    // 栅格化在 search() 中动态进行，此处预留扩展
}

std::vector<Position> AStarPlanner::search(const Position& start, const Position& goal) {
    // 世界坐标转栅格坐标
    auto to_grid = [this](const Position& p) -> GridCoord {
        return GridCoord{
            static_cast<int64_t>(std::round(p.x / resolution_)),
            static_cast<int64_t>(std::round(p.y / resolution_))
        };
    };

    // 栅格坐标转世界坐标
    auto to_world = [this](const GridCoord& c, double z) -> Position {
        return Position{c.gx * resolution_, c.gy * resolution_, z};
    };

    GridCoord start_grid = to_grid(start);
    GridCoord goal_grid = to_grid(goal);

    // 起点终点重合
    if (start_grid == goal_grid) {
        return {start};
    }

    // 启发式函数：欧氏距离
    auto heuristic = [this, &goal_grid](const GridCoord& c) -> double {
        double dx = static_cast<double>(c.gx - goal_grid.gx) * resolution_;
        double dy = static_cast<double>(c.gy - goal_grid.gy) * resolution_;
        return heuristic_weight_ * std::sqrt(dx * dx + dy * dy);
    };

    // 开放列表（最小堆）
    std::priority_queue<AStarNode, std::vector<AStarNode>, std::greater<AStarNode>> open_set;

    // 已访问集合
    std::unordered_set<GridCoord, GridCoordHash> closed_set;

    // g_score 表
    std::unordered_map<GridCoord, double, GridCoordHash> g_score;

    // 父节点表
    std::unordered_map<GridCoord, GridCoord, GridCoordHash> came_from;

    // 初始化起点
    AStarNode start_node;
    start_node.coord = start_grid;
    start_node.g_cost = 0.0;
    start_node.f_cost = heuristic(start_grid);
    start_node.parent = start_grid;

    open_set.push(start_node);
    g_score[start_grid] = 0.0;

    // 8方向邻居偏移
    static const int8_t dx[] = {-1, -1, -1, 0, 0, 1, 1, 1};
    static const int8_t dy[] = {-1, 0, 1, -1, 1, -1, 0, 1};
    // 对角线移动代价为 sqrt(2)，直线为 1
    static const double move_cost[] = {
        std::sqrt(2.0), 1.0, std::sqrt(2.0),
        1.0, 1.0,
        std::sqrt(2.0), 1.0, std::sqrt(2.0)
    };

    // 搜索范围限制
    const int64_t max_range = 10000;
    int64_t min_gx = std::min(start_grid.gx, goal_grid.gx) - max_range;
    int64_t max_gx = std::max(start_grid.gx, goal_grid.gx) + max_range;
    int64_t min_gy = std::min(start_grid.gy, goal_grid.gy) - max_range;
    int64_t max_gy = std::max(start_grid.gy, goal_grid.gy) + max_range;

    // A* 主循环
    while (!open_set.empty()) {
        AStarNode current = open_set.top();
        open_set.pop();

        // 到达目标
        if (current.coord == goal_grid) {
            // 回溯路径
            std::vector<GridCoord> grid_path;
            GridCoord node = goal_grid;
            while (node != start_grid) {
                grid_path.push_back(node);
                auto it = came_from.find(node);
                if (it == came_from.end()) break;
                node = it->second;
            }
            grid_path.push_back(start_grid);
            std::reverse(grid_path.begin(), grid_path.end());

            // 转换为世界坐标，高度线性插值
            std::vector<Position> path;
            path.reserve(grid_path.size());
            for (size_t i = 0; i < grid_path.size(); ++i) {
                double t = (grid_path.size() > 1)
                    ? static_cast<double>(i) / (grid_path.size() - 1)
                    : 0.0;
                double z = start.z + t * (goal.z - start.z);
                path.push_back(to_world(grid_path[i], z));
            }
            return path;
        }

        // 已处理过则跳过
        if (closed_set.count(current.coord)) continue;
        closed_set.insert(current.coord);

        // 遍历 8 个邻居
        for (int i = 0; i < 8; ++i) {
            GridCoord neighbor;
            neighbor.gx = current.coord.gx + dx[i];
            neighbor.gy = current.coord.gy + dy[i];

            // 边界检查
            if (neighbor.gx < min_gx || neighbor.gx > max_gx ||
                neighbor.gy < min_gy || neighbor.gy > max_gy) {
                continue;
            }

            // 已处理过则跳过
            if (closed_set.count(neighbor)) continue;

            // 碰撞检查
            Position world_pos = to_world(neighbor, start.z);
            if (is_collision(world_pos, obstacles_)) continue;
            if (is_in_no_fly_zone(world_pos, no_fly_zones_)) continue;

            // 计算新代价
            double tentative_g = current.g_cost + move_cost[i] * resolution_;

            auto it = g_score.find(neighbor);
            if (it == g_score.end() || tentative_g < it->second) {
                g_score[neighbor] = tentative_g;
                came_from[neighbor] = current.coord;

                AStarNode neighbor_node;
                neighbor_node.coord = neighbor;
                neighbor_node.g_cost = tentative_g;
                neighbor_node.f_cost = tentative_g + heuristic(neighbor);
                neighbor_node.parent = current.coord;
                open_set.push(neighbor_node);
            }
        }
    }

    // 未找到路径
    return {};
}

// ============================================================================
// B 样条路径平滑
// ============================================================================

std::vector<Position> AStarPlanner::smooth_path(const std::vector<Position>& raw_path) {
    if (raw_path.size() <= 2) return raw_path;

    std::vector<Position> smoothed;
    smoothed.reserve(raw_path.size() * 3);

    // 对每对相邻点使用三次 Bezier 插值
    for (size_t i = 0; i + 1 < raw_path.size(); ++i) {
        const Position& p0 = raw_path[i];
        const Position& p3 = raw_path[i + 1];

        // 计算控制点（使用前后点确定方向）
        Position p1, p2;

        if (i == 0) {
            // 第一段：简单线性控制点
            p1.x = p0.x + (p3.x - p0.x) / 3.0;
            p1.y = p0.y + (p3.y - p0.y) / 3.0;
            p1.z = p0.z + (p3.z - p0.z) / 3.0;
            p2.x = p0.x + 2.0 * (p3.x - p0.x) / 3.0;
            p2.y = p0.y + 2.0 * (p3.y - p0.y) / 3.0;
            p2.z = p0.z + 2.0 * (p3.z - p0.z) / 3.0;
        } else {
            const Position& prev = raw_path[i - 1];
            // 使用前一点确定切线方向
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

        // 沿 Bezier 曲线采样
        const int samples = 5;
        for (int s = 0; s < samples; ++s) {
            double t = static_cast<double>(s) / samples;
            double t2 = t * t;
            double t3 = t2 * t;
            double mt = 1.0 - t;
            double mt2 = mt * mt;
            double mt3 = mt2 * mt;

            Position pt;
            pt.x = mt3 * p0.x + 3.0 * mt2 * t * p1.x + 3.0 * mt * t2 * p2.x + t3 * p3.x;
            pt.y = mt3 * p0.y + 3.0 * mt2 * t * p1.y + 3.0 * mt * t2 * p2.y + t3 * p3.y;
            pt.z = mt3 * p0.z + 3.0 * mt2 * t * p1.z + 3.0 * mt * t2 * p2.z + t3 * p3.z;
            smoothed.push_back(pt);
        }
    }

    // 确保终点被包含
    smoothed.push_back(raw_path.back());

    return smoothed;
}

// ============================================================================
// RRTStarPlanner 实现
// ============================================================================

RRTStarPlanner::RRTStarPlanner(uint32_t max_iterations, double step_size, double goal_bias)
    : max_iterations_(max_iterations)
    , step_size_(step_size)
    , goal_bias_(goal_bias)
    , rewire_radius_(step_size * 3.0)
    , optimization_enabled_(true)
    , last_planning_time_ms_(0.0)
{
}

void RRTStarPlanner::initialize(const std::string& config) {
    (void)config;
}

void RRTStarPlanner::set_obstacles(const std::vector<Obstacle>& obstacles) {
    obstacles_ = obstacles;
}

void RRTStarPlanner::set_no_fly_zones(const std::vector<std::vector<Position>>& no_fly_zones) {
    no_fly_zones_ = no_fly_zones;
}

void RRTStarPlanner::set_rewire_radius(double radius) {
    rewire_radius_ = (radius > 0.0) ? radius : step_size_ * 3.0;
}

void RRTStarPlanner::enable_optimization(bool enable) {
    optimization_enabled_ = enable;
}

std::vector<Waypoint> RRTStarPlanner::plan(
    const Position& start,
    const Position& goal,
    double max_altitude,
    double min_altitude
) {
    auto begin_time = std::chrono::steady_clock::now();

    std::vector<Waypoint> result;

    // 检查起点终点有效性
    if (is_collision(start, obstacles_) || is_collision(goal, obstacles_)) {
        last_planning_time_ms_ = 0.0;
        return result;
    }

    // 随机数生成器
    std::mt19937 rng(static_cast<unsigned>(
        std::chrono::steady_clock::now().time_since_epoch().count()));

    // 计算搜索空间边界
    double x_min = std::min(start.x, goal.x) - 50.0;
    double x_max = std::max(start.x, goal.x) + 50.0;
    double y_min = std::min(start.y, goal.y) - 50.0;
    double y_max = std::max(start.y, goal.y) + 50.0;

    std::uniform_real_distribution<double> x_dist(x_min, x_max);
    std::uniform_real_distribution<double> y_dist(y_min, y_max);
    std::uniform_real_distribution<double> z_dist(min_altitude, max_altitude);
    std::uniform_real_distribution<double> unit_dist(0.0, 1.0);

    // RRT* 树
    std::vector<Position> nodes;
    std::vector<double> costs;         // 每个节点到起点的代价
    std::vector<size_t> parents;       // 父节点索引

    nodes.push_back(start);
    costs.push_back(0.0);
    parents.push_back(0); // 起点指向自身

    // RRT* 主循环
    for (uint32_t iter = 0; iter < max_iterations_; ++iter) {
        // 采样随机点（带目标偏向）
        Position sample;
        if (unit_dist(rng) < goal_bias_) {
            sample = goal;
        } else {
            sample.x = x_dist(rng);
            sample.y = y_dist(rng);
            sample.z = z_dist(rng);
        }

        // 找到最近节点
        size_t nearest_idx = find_nearest(nodes, sample);
        const Position& nearest = nodes[nearest_idx];

        // 向最近节点方向扩展
        double dx = sample.x - nearest.x;
        double dy = sample.y - nearest.y;
        double dz = sample.z - nearest.z;
        double dist = std::sqrt(dx * dx + dy * dy + dz * dz);

        if (dist < 1e-6) continue;

        // 限制步长
        Position new_node;
        if (dist <= step_size_) {
            new_node = sample;
        } else {
            double ratio = step_size_ / dist;
            new_node.x = nearest.x + dx * ratio;
            new_node.y = nearest.y + dy * ratio;
            new_node.z = nearest.z + dz * ratio;
        }

        // 碰撞检查
        if (!is_collision_free(nearest, new_node)) continue;
        if (is_in_no_fly_zone(new_node, no_fly_zones_)) continue;

        // RRT* 重连：找到新节点周围代价更低的父节点
        size_t best_parent = nearest_idx;
        double best_cost = costs[nearest_idx] + nearest.distance_to(new_node);

        if (optimization_enabled_) {
            for (size_t i = 0; i < nodes.size(); ++i) {
                if (i == nearest_idx) continue;
                double d = nodes[i].distance_to(new_node);
                if (d < rewire_radius_ && is_collision_free(nodes[i], new_node)) {
                    double new_cost = costs[i] + d;
                    if (new_cost < best_cost) {
                        best_cost = new_cost;
                        best_parent = i;
                    }
                }
            }
        }

        // 添加新节点
        size_t new_idx = nodes.size();
        nodes.push_back(new_node);
        costs.push_back(best_cost);
        parents.push_back(best_parent);

        // RRT* 重连：检查新节点是否能改善已有节点的代价
        if (optimization_enabled_) {
            for (size_t i = 0; i < nodes.size() - 1; ++i) {
                double d = nodes[i].distance_to(new_node);
                if (d < rewire_radius_ && is_collision_free(nodes[i], new_node)) {
                    double new_cost = best_cost + d;
                    if (new_cost < costs[i]) {
                        costs[i] = new_cost;
                        parents[i] = new_idx;
                    }
                }
            }
        }

        // 检查是否到达目标附近
        if (new_node.distance_to(goal) < step_size_) {
            // 回溯路径
            std::vector<Position> raw_path;
            size_t idx = new_idx;
            while (idx != parents[idx]) {
                raw_path.push_back(nodes[idx]);
                idx = parents[idx];
            }
            raw_path.push_back(start);
            std::reverse(raw_path.begin(), raw_path.end());
            raw_path.push_back(goal);

            // 路径优化
            if (optimization_enabled_) {
                raw_path = optimize_path(raw_path);
            }

            // 转换为航路点
            for (const auto& pos : raw_path) {
                Waypoint wp;
                wp.position = pos;
                wp.position.z = std::clamp(pos.z, min_altitude, max_altitude);
                result.push_back(wp);
            }

            auto end_time = std::chrono::steady_clock::now();
            last_planning_time_ms_ = std::chrono::duration<double, std::milli>(
                end_time - begin_time).count();
            return result;
        }
    }

    // 未找到路径
    last_planning_time_ms_ = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - begin_time).count();
    return result;
}

bool RRTStarPlanner::validate_path(const std::vector<Waypoint>& waypoints) const {
    if (waypoints.empty()) return false;

    for (const auto& wp : waypoints) {
        if (is_collision(wp.position, obstacles_)) return false;
        if (is_in_no_fly_zone(wp.position, no_fly_zones_)) return false;
    }
    return true;
}

double RRTStarPlanner::last_planning_time_ms() const {
    return last_planning_time_ms_;
}

// ============================================================================
// RRT* 辅助方法
// ============================================================================

bool RRTStarPlanner::is_collision_free(const Position& p1, const Position& p2) const {
    // 沿线段采样检查碰撞
    double dist = p1.distance_to(p2);
    double sample_resolution = step_size_ / 2.0; // 采样分辨率为步长的一半
    int steps = std::max(1, static_cast<int>(dist / sample_resolution));

    for (int i = 0; i <= steps; ++i) {
        double t = static_cast<double>(i) / steps;
        Position p;
        p.x = p1.x + t * (p2.x - p1.x);
        p.y = p1.y + t * (p2.y - p1.y);
        p.z = p1.z + t * (p2.z - p1.z);

        if (is_collision(p, obstacles_)) return false;
    }
    return true;
}

Position RRTStarPlanner::sample_random(const Position& goal) const {
    // 在目标附近随机采样
    std::mt19937 rng(static_cast<unsigned>(
        std::chrono::steady_clock::now().time_since_epoch().count()));
    std::uniform_real_distribution<double> dist(-step_size_ * 5, step_size_ * 5);

    Position p;
    p.x = goal.x + dist(rng);
    p.y = goal.y + dist(rng);
    p.z = goal.z + dist(rng) * 0.1; // 高度变化较小
    return p;
}

size_t RRTStarPlanner::find_nearest(
    const std::vector<Position>& nodes,
    const Position& point
) const {
    size_t nearest = 0;
    double min_dist = std::numeric_limits<double>::max();

    for (size_t i = 0; i < nodes.size(); ++i) {
        double d = nodes[i].distance_to(point);
        if (d < min_dist) {
            min_dist = d;
            nearest = i;
        }
    }
    return nearest;
}

std::vector<Position> RRTStarPlanner::optimize_path(const std::vector<Position>& raw_path) {
    if (raw_path.size() <= 2) return raw_path;

    // 贪心路径简化：尝试跳过中间节点
    std::vector<Position> optimized;
    optimized.push_back(raw_path.front());

    size_t i = 0;
    while (i < raw_path.size() - 1) {
        // 尝试找到最远的可直接连接的节点
        size_t farthest = i + 1;
        for (size_t j = raw_path.size() - 1; j > i + 1; --j) {
            if (is_collision_free(raw_path[i], raw_path[j])) {
                farthest = j;
                break;
            }
        }
        optimized.push_back(raw_path[farthest]);
        i = farthest;
    }

    return optimized;
}

// ============================================================================
// 工厂函数
// ============================================================================

std::unique_ptr<IPathPlanner> create_path_planner(const std::string& algorithm) {
    if (algorithm == "astar") {
        return std::make_unique<AStarPlanner>();
    } else if (algorithm == "rrt_star" || algorithm == "rrt*") {
        return std::make_unique<RRTStarPlanner>();
    }
    // 默认使用 A*
    return std::make_unique<AStarPlanner>();
}

} // namespace uav::edge
