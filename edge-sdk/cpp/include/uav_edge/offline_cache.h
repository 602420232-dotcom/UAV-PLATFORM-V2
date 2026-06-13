#pragma once

/// @file offline_cache.h
/// @brief 离线缓存接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <ctime>
#include <cstdint>

namespace uav::edge {

// ============================================================================
// 缓存条目
// ============================================================================

/// 缓存条目
struct CacheEntry {
    std::string key;              ///< 缓存键
    std::string data;             ///< 缓存数据（JSON 字符串）
    std::time_t timestamp{0};     ///< 写入时间戳
    std::string version;          ///< 数据版本
    int32_t ttl_seconds{3600};    ///< 有效期 (秒)，-1 表示永久
};

// ============================================================================
// 缓存类型
// ============================================================================

/// 缓存数据类型
enum class CacheType : uint8_t {
    PathPlan = 0,    ///< 路径规划缓存
    WeatherData = 1, ///< 气象数据缓存
    Config = 2,      ///< 配置数据
    MapData = 3      ///< 地图/地形数据
};

// ============================================================================
// 离线缓存管理器
// ============================================================================

/// 离线缓存管理器
/// 管理本地数据持久化和离线更新机制
/// 支持路径规划缓存、气象数据缓存、配置文件存储
class OfflineCache {
public:
    /// 构造函数
    /// @param cache_dir 缓存目录路径
    explicit OfflineCache(const std::string& cache_dir = "./offline_cache");

    /// 析构函数，自动保存索引
    ~OfflineCache();

    // ========================================================================
    // 基本操作
    // ========================================================================

    /// 写入缓存
    bool put(const std::string& key, const std::string& data,
             CacheType type = CacheType::PathPlan, int32_t ttl = 3600);

    /// 读取缓存
    [[nodiscard]] std::string get(const std::string& key,
                                    CacheType type = CacheType::PathPlan);

    /// 删除缓存条目
    bool remove(const std::string& key, CacheType type = CacheType::PathPlan);

    /// 清空指定类型的缓存
    void clear(CacheType type = CacheType::PathPlan);

    /// 清空所有缓存
    void clear_all();

    // ========================================================================
    // 查询
    // ========================================================================

    /// 检查缓存是否存在
    [[nodiscard]] bool exists(const std::string& key,
                               CacheType type = CacheType::PathPlan) const;

    /// 检查缓存是否过期
    [[nodiscard]] bool is_expired(const std::string& key,
                                   CacheType type = CacheType::PathPlan) const;

    /// 获取指定类型的缓存条目数
    [[nodiscard]] int count(CacheType type = CacheType::PathPlan) const;

    /// 列出指定类型的所有缓存键
    [[nodiscard]] std::vector<std::string> list_keys(
        CacheType type = CacheType::PathPlan
    ) const;

    // ========================================================================
    // 数据更新
    // ========================================================================

    /// 更新信息
    struct UpdateInfo {
        std::string version;       ///< 缓存版本
        std::time_t timestamp;    ///< 更新时间戳
        int32_t entry_count{0};   ///< 条目总数
        int64_t total_bytes{0};   ///< 数据总字节数
    };

    /// 获取更新信息
    [[nodiscard]] UpdateInfo get_update_info() const;

    /// 从文件同步缓存
    bool sync_from_file(const std::string& filepath);

    /// 导出缓存到文件
    bool export_to_file(const std::string& filepath,
                        CacheType type = CacheType::PathPlan);

    // ========================================================================
    // 便捷方法
    // ========================================================================

    /// 保存配置
    bool save_config(const std::string& app_name, const std::string& config_json);

    /// 加载配置
    [[nodiscard]] std::string load_config(const std::string& app_name);

    /// 缓存路径规划结果
    bool cache_path(const std::string& key, const std::vector<Waypoint>& path);

    /// 获取缓存的路径规划结果
    [[nodiscard]] std::vector<Waypoint> get_cached_path(const std::string& key);

    /// 缓存天气数据
    bool cache_weather(const std::string& location_id, const WeatherData& data);

    /// 获取缓存的天气数据
    [[nodiscard]] WeatherData get_cached_weather(const std::string& location_id);

private:
    std::string cache_dir_;  ///< 缓存目录
    std::unordered_map<std::string, CacheEntry> index_; ///< 缓存索引
    mutable std::mutex mutex_; ///< 互斥锁

    /// 获取缓存类型子目录名
    [[nodiscard]] static std::string cache_type_name(CacheType type);

    /// 获取缓存文件路径
    [[nodiscard]] std::string get_cache_filename(CacheType type) const;

    /// 清理键名中的特殊字符
    [[nodiscard]] std::string sanitize_key(const std::string& key) const;

    /// 确保缓存目录存在
    bool ensure_cache_dir() const;

    /// 加载缓存索引
    void load_index();

    /// 保存缓存索引
    void save_index();
};

} // namespace uav::edge
