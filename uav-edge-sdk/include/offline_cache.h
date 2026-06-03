#ifndef OFFLINE_CACHE_H
#define OFFLINE_CACHE_H

#include <string>
#include <vector>
#include <map>
#include <functional>
#include <mutex>
#include <ctime>
#include "path_planner.h"
#include "risk_assessor.h"

namespace uav_sdk {

/**
 * @brief 缓存条目
 */
struct CacheEntry {
    std::string key;
    std::string data;              // JSON序列化数据
    std::time_t timestamp;
    std::string version;
    int32_t ttl_seconds;           // 有效期(秒), -1表示永久
};

/**
 * @brief 离线缓存管理器
 * 
 * 管理本地数据持久化和离线更新机制
 * 支持路径规划缓存、气象数据缓存、配置文件存储
 */
class OfflineCache {
public:
    /**
     * @brief 缓存类型
     */
    enum CacheType {
        PATH_PLAN,       // 路径规划缓存
        WEATHER_DATA,    // 气象数据缓存
        CONFIG,          // 配置数据
        MAP_DATA         // 地图/地形数据
    };

    OfflineCache(const std::string& cache_dir = "./offline_cache");
    ~OfflineCache();

    // ─── 基本操作 ────────────────────────────────────────────────────
    bool put(const std::string& key, const std::string& data, 
             CacheType type = PATH_PLAN, int32_t ttl = 3600);
    std::string get(const std::string& key, CacheType type = PATH_PLAN);
    bool remove(const std::string& key, CacheType type = PATH_PLAN);
    void clear(CacheType type = PATH_PLAN);
    void clear_all();

    // ─── 查询 ────────────────────────────────────────────────────────
    bool exists(const std::string& key, CacheType type = PATH_PLAN) const;
    bool is_expired(const std::string& key, CacheType type = PATH_PLAN) const;
    int count(CacheType type = PATH_PLAN) const;
    std::vector<std::string> list_keys(CacheType type = PATH_PLAN) const;

    // ─── 数据更新 ────────────────────────────────────────────────────
    struct UpdateInfo {
        std::string version;
        std::time_t timestamp;
        int32_t entry_count;
        int64_t total_bytes;
    };

    UpdateInfo get_update_info() const;
    bool sync_from_file(const std::string& filepath);
    bool export_to_file(const std::string& filepath, CacheType type = PATH_PLAN);

    // ─── 配置持久化 ───────────────────────────────────────────────────
    bool save_config(const std::string& app_name, const std::string& config_json);
    std::string load_config(const std::string& app_name);

    // ─── 路径规划缓存 ─────────────────────────────────────────────────
    bool cache_path(const std::string& key, const std::vector<Point>& path);
    std::vector<Point> get_cached_path(const std::string& key);

    // ─── 气象数据缓存 ─────────────────────────────────────────────────
    bool cache_weather(const std::string& location_id, const WeatherData& data);
    WeatherData get_cached_weather(const std::string& location_id);

private:
    std::string get_cache_filename(CacheType type) const;
    std::string sanitize_key(const std::string& key) const;
    bool ensure_cache_dir() const;
    void load_index();
    void save_index();

    std::string cache_dir_;
    std::map<std::string, CacheEntry> index_;
    mutable std::mutex mutex_;
};

}  // namespace uav_sdk

#endif  // OFFLINE_CACHE_H
