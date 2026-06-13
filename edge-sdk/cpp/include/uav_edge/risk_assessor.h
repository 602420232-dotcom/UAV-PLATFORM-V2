#pragma once

/// @file risk_assessor.h
/// @brief 风险评估接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <memory>
#include <vector>
#include <functional>

namespace uav::edge {

// ============================================================================
// 风险评估抽象接口
// ============================================================================

/// 风险评估器抽象基类
/// 所有风险评估算法需实现此接口
class IRiskAssessor {
public:
    virtual ~IRiskAssessor() = default;

    /// 初始化评估器
    /// @param config 配置参数（JSON 格式字符串）
    virtual void initialize(const std::string& config) = 0;

    /// 评估天气风险
    /// @param weather 天气数据
    /// @param flight_plan 飞行计划
    /// @return 风险评估结果
    virtual RiskAssessment assess_weather_risk(
        const WeatherData& weather,
        const FlightPlan& flight_plan
    ) = 0;

    /// 评估障碍物碰撞风险
    /// @param obstacles 障碍物列表
    /// @param flight_plan 飞行计划
    /// @return 风险评估结果
    virtual RiskAssessment assess_obstacle_risk(
        const std::vector<Obstacle>& obstacles,
        const FlightPlan& flight_plan
    ) = 0;

    /// 综合风险评估
    /// @param weather 天气数据
    /// @param obstacles 障碍物列表
    /// @param flight_plan 飞行计划
    /// @return 综合风险评估结果
    virtual RiskAssessment assess(
        const WeatherData& weather,
        const std::vector<Obstacle>& obstacles,
        const FlightPlan& flight_plan
    ) = 0;

    /// 获取评估器名称
    [[nodiscard]] virtual std::string name() const = 0;
};

// ============================================================================
// 天气风险评估器
// ============================================================================

/// 天气风险评估器
/// 基于气象参数对飞行安全进行定量评估
class WeatherRiskAssessor : public IRiskAssessor {
public:
    /// 构造函数
    WeatherRiskAssessor() = default;

    void initialize(const std::string& config) override;

    RiskAssessment assess_weather_risk(
        const WeatherData& weather,
        const FlightPlan& flight_plan
    ) override;

    RiskAssessment assess_obstacle_risk(
        const std::vector<Obstacle>& obstacles,
        const FlightPlan& flight_plan
    ) override;

    RiskAssessment assess(
        const WeatherData& weather,
        const std::vector<Obstacle>& obstacles,
        const FlightPlan& flight_plan
    ) override;

    [[nodiscard]] std::string name() const override { return "WeatherRiskAssessor"; }

    /// 设置风速安全阈值 (m/s)
    void set_wind_speed_threshold(double threshold);

    /// 设置能见度安全阈值 (m)
    void set_visibility_threshold(double threshold);

    /// 设置降水量安全阈值 (mm/h)
    void set_precipitation_threshold(double threshold);

private:
    double wind_speed_threshold_{15.0};     ///< 风速安全阈值
    double visibility_threshold_{2000.0};   ///< 能见度安全阈值
    double precipitation_threshold_{5.0};    ///< 降水量安全阈值

    /// 计算风速风险因子 (0-1)
    [[nodiscard]] double evaluate_wind_risk(double wind_speed) const;

    /// 计算能见度风险因子 (0-1)
    [[nodiscard]] double evaluate_visibility_risk(double visibility) const;

    /// 计算降水风险因子 (0-1)
    [[nodiscard]] double evaluate_precipitation_risk(double precipitation) const;

    /// 计算湍流风险因子 (0-1)
    [[nodiscard]] double evaluate_turbulence_risk(double turbulence) const;

    /// 综合各因子得到总风险评分
    [[nodiscard]] double combine_factors(
        double wind, double visibility, double precip, double turb
    ) const;

    /// 风险评分映射到风险等级
    [[nodiscard]] static RiskLevel score_to_level(double score);
};

// ============================================================================
// 工厂函数
// ============================================================================

/// 创建风险评估器实例
/// @param algorithm 算法名称 ("weather" 等)
/// @return 风险评估器智能指针
std::unique_ptr<IRiskAssessor> create_risk_assessor(const std::string& algorithm);

} // namespace uav::edge
