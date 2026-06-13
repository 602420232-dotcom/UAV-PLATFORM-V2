/// @file risk_assessor.cpp
/// @brief 风险评估器实现
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/risk_assessor.h"

#include <cmath>
#include <algorithm>
#include <sstream>

namespace uav::edge {

// ============================================================================
// WeatherRiskAssessor 初始化
// ============================================================================

void WeatherRiskAssessor::initialize(const std::string& config) {
    // 简单配置解析，使用默认值
    // 可扩展为 JSON 解析
    (void)config;
}

void WeatherRiskAssessor::set_wind_speed_threshold(double threshold) {
    wind_speed_threshold_ = (threshold > 0.0) ? threshold : 15.0;
}

void WeatherRiskAssessor::set_visibility_threshold(double threshold) {
    visibility_threshold_ = (threshold > 0.0) ? threshold : 2000.0;
}

void WeatherRiskAssessor::set_precipitation_threshold(double threshold) {
    precipitation_threshold_ = (threshold >= 0.0) ? threshold : 5.0;
}

// ============================================================================
// 风险因子评估
// ============================================================================

/// 计算风速风险因子 (0-1)
/// 风速越大风险越高，超过阈值后急剧增加
double WeatherRiskAssessor::evaluate_wind_risk(double wind_speed) const {
    if (wind_speed < wind_speed_threshold_ * 0.3) {
        return 0.0; // 微风，无风险
    }
    if (wind_speed < wind_speed_threshold_ * 0.6) {
        // 轻风到中风：线性增长
        return (wind_speed - wind_speed_threshold_ * 0.3) /
               (wind_speed_threshold_ * 0.3);
    }
    if (wind_speed < wind_speed_threshold_) {
        // 中风到强风：加速增长
        return 0.5 + 0.3 * (wind_speed - wind_speed_threshold_ * 0.6) /
               (wind_speed_threshold_ * 0.4);
    }
    if (wind_speed < wind_speed_threshold_ * 1.5) {
        // 超过安全阈值：高风险
        return 0.8 + 0.2 * (wind_speed - wind_speed_threshold_) /
               (wind_speed_threshold_ * 0.5);
    }
    return 1.0; // 极端风速
}

/// 计算能见度风险因子 (0-1)
/// 能见度越低风险越高
double WeatherRiskAssessor::evaluate_visibility_risk(double visibility) const {
    if (visibility > visibility_threshold_ * 2.0) {
        return 0.0; // 能见度极好
    }
    if (visibility > visibility_threshold_) {
        // 良好到一般
        return 0.2 * (1.0 - (visibility - visibility_threshold_) / visibility_threshold_);
    }
    if (visibility > visibility_threshold_ * 0.5) {
        // 一般到较差
        return 0.2 + 0.4 * (1.0 - (visibility - visibility_threshold_ * 0.5) /
               (visibility_threshold_ * 0.5));
    }
    if (visibility > visibility_threshold_ * 0.2) {
        // 较差到极差
        return 0.6 + 0.3 * (1.0 - (visibility - visibility_threshold_ * 0.2) /
               (visibility_threshold_ * 0.3));
    }
    return 1.0; // 能见度极低
}

/// 计算降水风险因子 (0-1)
double WeatherRiskAssessor::evaluate_precipitation_risk(double precipitation) const {
    if (precipitation < precipitation_threshold_ * 0.1) {
        return 0.0; // 无降水或微量
    }
    if (precipitation < precipitation_threshold_) {
        // 小雨
        return 0.3 * precipitation / precipitation_threshold_;
    }
    if (precipitation < precipitation_threshold_ * 2.0) {
        // 中雨
        return 0.3 + 0.4 * (precipitation - precipitation_threshold_) / precipitation_threshold_;
    }
    if (precipitation < precipitation_threshold_ * 4.0) {
        // 大雨
        return 0.7 + 0.2 * (precipitation - precipitation_threshold_ * 2.0) /
               (precipitation_threshold_ * 2.0);
    }
    return 1.0; // 暴雨
}

/// 计算湍流风险因子 (0-1)
double WeatherRiskAssessor::evaluate_turbulence_risk(double turbulence) const {
    // turbulence 为 0-1 的强度指数
    return std::clamp(turbulence, 0.0, 1.0);
}

/// 综合各因子得到总风险评分 (0-1)
/// 使用加权平均，权重分配：风速 30%，能见度 25%，降水 20%，湍流 25%
double WeatherRiskAssessor::combine_factors(
    double wind, double visibility, double precip, double turb
) const {
    return std::clamp(
        wind * 0.30 + visibility * 0.25 + precip * 0.20 + turb * 0.25,
        0.0, 1.0
    );
}

/// 风险评分映射到风险等级
RiskLevel WeatherRiskAssessor::score_to_level(double score) {
    if (score < 0.25) return RiskLevel::Low;
    if (score < 0.50) return RiskLevel::Medium;
    if (score < 0.75) return RiskLevel::High;
    return RiskLevel::Critical;
}

// ============================================================================
// 风险评估接口实现
// ============================================================================

RiskAssessment WeatherRiskAssessor::assess_weather_risk(
    const WeatherData& weather,
    const FlightPlan& flight_plan
) {
    RiskAssessment result;

    // 计算各天气风险因子
    double wind_risk = evaluate_wind_risk(weather.wind_speed);
    double vis_risk = evaluate_visibility_risk(weather.visibility);
    double precip_risk = evaluate_precipitation_risk(weather.precipitation);
    double turb_risk = weather.turbulence.has_value()
        ? evaluate_turbulence_risk(weather.turbulence.value())
        : 0.0;

    // 综合评分
    result.score = combine_factors(wind_risk, vis_risk, precip_risk, turb_risk);
    result.level = score_to_level(result.score);

    // 生成风险因素描述
    if (wind_risk > 0.5) {
        result.factors.push_back("风速过高 (" +
            std::to_string(static_cast<int>(weather.wind_speed)) + " m/s)");
    }
    if (vis_risk > 0.5) {
        result.factors.push_back("能见度不足 (" +
            std::to_string(static_cast<int>(weather.visibility)) + " m)");
    }
    if (precip_risk > 0.5) {
        result.factors.push_back("降水量过大 (" +
            std::to_string(static_cast<int>(weather.precipitation)) + " mm/h)");
    }
    if (turb_risk > 0.5) {
        result.factors.push_back("湍流强度高");
    }

    // 生成描述
    std::ostringstream oss;
    switch (result.level) {
        case RiskLevel::Low:
            oss << "天气条件良好，适合飞行";
            break;
        case RiskLevel::Medium:
            oss << "天气条件一般，需关注变化";
            break;
        case RiskLevel::High:
            oss << "天气条件较差，建议调整飞行计划";
            break;
        case RiskLevel::Critical:
            oss << "天气条件恶劣，强烈建议推迟或取消飞行";
            break;
    }
    result.description = oss.str();

    (void)flight_plan; // 预留扩展
    return result;
}

RiskAssessment WeatherRiskAssessor::assess_obstacle_risk(
    const std::vector<Obstacle>& obstacles,
    const FlightPlan& flight_plan
) {
    RiskAssessment result;
    result.score = 0.0;
    result.level = RiskLevel::Low;

    if (obstacles.empty() || flight_plan.waypoints.empty()) {
        result.description = "无障碍物或无飞行计划";
        return result;
    }

    // 计算每个航段与障碍物的最小距离
    double min_clearance = std::numeric_limits<double>::max();
    int close_obstacles = 0;

    for (const auto& wp : flight_plan.waypoints) {
        for (const auto& obs : obstacles) {
            double dist = wp.position.distance_to(obs.position);
            double clearance = dist - obs.radius;

            if (clearance < min_clearance) {
                min_clearance = clearance;
            }

            // 安全距离阈值：20m
            if (clearance < 20.0) {
                close_obstacles++;
            }
        }
    }

    // 根据最小间隙计算风险
    if (min_clearance < 5.0) {
        result.score = 0.9;
        result.factors.push_back("存在极近距离障碍物 (< 5m)");
    } else if (min_clearance < 10.0) {
        result.score = 0.6;
        result.factors.push_back("存在近距离障碍物 (< 10m)");
    } else if (min_clearance < 20.0) {
        result.score = 0.3;
        result.factors.push_back("存在中等距离障碍物 (< 20m)");
    } else {
        result.score = 0.05;
    }

    if (close_obstacles > 5) {
        result.score = std::min(1.0, result.score + 0.1);
        result.factors.push_back("密集障碍物区域 (" +
            std::to_string(close_obstacles) + " 个近距离障碍物)");
    }

    result.level = score_to_level(result.score);

    std::ostringstream oss;
    oss << "障碍物风险评估: 最小安全间隙 " << static_cast<int>(min_clearance) << "m";
    result.description = oss.str();

    return result;
}

RiskAssessment WeatherRiskAssessor::assess(
    const WeatherData& weather,
    const std::vector<Obstacle>& obstacles,
    const FlightPlan& flight_plan
) {
    // 分别评估天气和障碍物风险
    RiskAssessment weather_risk = assess_weather_risk(weather, flight_plan);
    RiskAssessment obstacle_risk = assess_obstacle_risk(obstacles, flight_plan);

    // 综合评估：取较高风险，并适当加权
    RiskAssessment combined;

    // 综合评分：天气 60%，障碍物 40%
    combined.score = std::clamp(
        weather_risk.score * 0.6 + obstacle_risk.score * 0.4,
        0.0, 1.0
    );
    combined.level = score_to_level(combined.score);

    // 合并风险因素
    combined.factors = weather_risk.factors;
    combined.factors.insert(
        combined.factors.end(),
        obstacle_risk.factors.begin(),
        obstacle_risk.factors.end()
    );

    // 生成综合描述
    std::ostringstream oss;
    oss << "综合风险评估: 天气风险 " << static_cast<int>(weather_risk.score * 100)
        << "%, 障碍物风险 " << static_cast<int>(obstacle_risk.score * 100)
        << "%, 综合风险 " << static_cast<int>(combined.score * 100) << "%";

    switch (combined.level) {
        case RiskLevel::Low:
            oss << " - 可以正常飞行";
            break;
        case RiskLevel::Medium:
            oss << " - 需要关注";
            break;
        case RiskLevel::High:
            oss << " - 建议调整航线";
            break;
        case RiskLevel::Critical:
            oss << " - 建议返航";
            break;
    }
    combined.description = oss.str();

    return combined;
}

// ============================================================================
// 工厂函数
// ============================================================================

std::unique_ptr<IRiskAssessor> create_risk_assessor(const std::string& algorithm) {
    if (algorithm == "weather") {
        return std::make_unique<WeatherRiskAssessor>();
    }
    // 默认使用天气风险评估器
    return std::make_unique<WeatherRiskAssessor>();
}

} // namespace uav::edge
