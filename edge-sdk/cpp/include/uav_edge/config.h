#pragma once

/// @file config.h
/// @brief 边缘计算 SDK 配置管理
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <string>
#include <unordered_map>
#include <optional>
#include <filesystem>

namespace uav::edge {

// ============================================================================
// 边缘配置管理
// ============================================================================

/// 边缘计算 SDK 配置类
/// 统一管理各模块的配置参数，支持从 JSON 文件加载
class EdgeConfig {
public:
    /// 构造函数
    EdgeConfig() = default;

    /// 从 JSON 文件加载配置
    /// @param config_path 配置文件路径
    /// @return 加载是否成功
    bool load_from_file(const std::filesystem::path& config_path);

    /// 从 JSON 字符串加载配置
    /// @param json_str JSON 格式字符串
    /// @return 加载是否成功
    bool load_from_string(const std::string& json_str);

    /// 保存配置到文件
    /// @param config_path 目标文件路径
    /// @return 保存是否成功
    bool save_to_file(const std::filesystem::path& config_path) const;

    /// 导出为 JSON 字符串
    /// @return JSON 格式字符串
    [[nodiscard]] std::string to_json_string() const;

    // ========================================================================
    // 通用配置访问
    // ========================================================================

    /// 获取字符串配置项
    [[nodiscard]] std::optional<std::string> get_string(const std::string& key) const;

    /// 获取整数配置项
    [[nodiscard]] std::optional<int64_t> get_int(const std::string& key) const;

    /// 获取浮点数配置项
    [[nodiscard]] std::optional<double> get_double(const std::string& key) const;

    /// 获取布尔配置项
    [[nodiscard]] std::optional<bool> get_bool(const std::string& key) const;

    /// 设置配置项
    void set(const std::string& key, const std::string& value);
    void set(const std::string& key, int64_t value);
    void set(const std::string& key, double value);
    void set(const std::string& key, bool value);

    /// 检查配置项是否存在
    [[nodiscard]] bool has(const std::string& key) const;

    /// 移除配置项
    void remove(const std::string& key);

    // ========================================================================
    // 路径规划配置
    // ========================================================================

    /// 获取路径规划算法名称
    [[nodiscard]] std::string path_planner_algorithm() const;

    /// 获取栅格分辨率
    [[nodiscard]] double path_planner_resolution() const;

    /// 获取 RRT* 最大迭代次数
    [[nodiscard]] uint32_t rrt_max_iterations() const;

    // ========================================================================
    // 风险评估配置
    // ========================================================================

    /// 获取风速安全阈值
    [[nodiscard]] double risk_wind_speed_threshold() const;

    /// 获取能见度安全阈值
    [[nodiscard]] double risk_visibility_threshold() const;

    // ========================================================================
    // V2X 通信配置
    // ========================================================================

    /// 获取 V2X 通信技术类型
    [[nodiscard]] V2XTechnology v2x_technology() const;

    /// 获取 DSRC 频道
    [[nodiscard]] uint8_t v2x_dsrc_channel() const;

    /// 获取发射功率
    [[nodiscard]] double v2x_tx_power() const;

    // ========================================================================
    // 联邦学习配置
    // ========================================================================

    /// 获取联邦学习服务器地址
    [[nodiscard]] std::string federated_server_url() const;

    /// 获取聚合策略
    [[nodiscard]] std::string federated_aggregation_strategy() const;

    // ========================================================================
    // 模型推理配置
    // ========================================================================

    /// 获取推理后端
    [[nodiscard]] std::string model_runtime_backend() const;

    /// 获取推理设备
    [[nodiscard]] std::string model_runtime_device() const;

    /// 获取推理精度
    [[nodiscard]] InferencePrecision model_runtime_precision() const;

    /// 获取线程数
    [[nodiscard]] int model_runtime_num_threads() const;

private:
    /// 配置存储（扁平化 key-value）
    std::unordered_map<std::string, std::string> config_map_;

    /// 带命名空间的配置访问
    [[nodiscard]] std::optional<std::string> get_namespaced(
        const std::string& ns,
        const std::string& key
    ) const;

    /// 带默认值的配置访问
    [[nodiscard]] std::string get_with_default(
        const std::string& key,
        const std::string& default_value
    ) const;
};

} // namespace uav::edge
