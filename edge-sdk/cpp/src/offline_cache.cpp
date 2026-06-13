/// @file offline_cache.cpp
/// @brief 离线缓存管理器实现
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/offline_cache.h"

#include <fstream>
#include <sstream>
#include <algorithm>
#include <cctype>
#include <cstdio>
#include <chrono>

#ifdef _WIN32
#include <direct.h>
#include <windows.h>
#else
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#endif

namespace uav::edge {

namespace {

// ============================================================================
// 简易 JSON 工具（不依赖外部库）
// ============================================================================

/// JSON 字符串转义
std::string json_escape(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 2);
    for (char c : s) {
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n";  break;
            case '\r': out += "\\r";  break;
            case '\t': out += "\\t";  break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    char buf[8];
                    std::snprintf(buf, sizeof(buf), "\\u%04x",
                                  static_cast<unsigned char>(c));
                    out += buf;
                } else {
                    out += c;
                }
                break;
        }
    }
    return out;
}

std::string json_string(const std::string& s) {
    return "\"" + json_escape(s) + "\"";
}

std::string json_number(double v) {
    if (v == std::floor(v) && std::isfinite(v) && std::fabs(v) < 1e15) {
        return std::to_string(static_cast<long long>(v));
    }
    std::ostringstream oss;
    oss << v;
    return oss.str();
}

// ============================================================================
// 目录创建
// ============================================================================

bool create_directory(const std::string& path) {
#ifdef _WIN32
    return _mkdir(path.c_str()) == 0 || errno == EEXIST;
#else
    return mkdir(path.c_str(), 0755) == 0 || errno == EEXIST;
#endif
}

// ============================================================================
// 文件读写
// ============================================================================

std::string read_file_content(const std::string& filepath) {
    std::ifstream ifs(filepath);
    if (!ifs.is_open()) return "";
    std::ostringstream oss;
    oss << ifs.rdbuf();
    return oss.str();
}

bool write_file_content(const std::string& filepath, const std::string& content) {
    std::ofstream ofs(filepath);
    if (!ofs.is_open()) return false;
    ofs << content;
    return ofs.good();
}

// ============================================================================
// Position JSON 序列化/反序列化
// ============================================================================

std::string position_to_json(const Position& p) {
    return "{\"x\":" + json_number(p.x) +
           ",\"y\":" + json_number(p.y) +
           ",\"z\":" + json_number(p.z) + "}";
}

Position position_from_json_str(const std::string& json) {
    Position p;
    // 简易解析：查找 "x":, "y":, "z": 字段
    auto find_num = [](const std::string& s, const std::string& key) -> double {
        size_t pos = s.find("\"" + key + "\"");
        if (pos == std::string::npos) return 0.0;
        pos = s.find(':', pos + key.size() + 2);
        if (pos == std::string::npos) return 0.0;
        ++pos;
        // 跳过空白
        while (pos < s.size() && std::isspace(static_cast<unsigned char>(s[pos]))) ++pos;
        // 读取数字
        size_t end = pos;
        if (end < s.size() && s[end] == '-') ++end;
        while (end < s.size() && (std::isdigit(static_cast<unsigned char>(s[end])) ||
               s[end] == '.' || s[end] == 'e' || s[end] == 'E' ||
               s[end] == '+' || s[end] == '-')) {
            ++end;
        }
        std::string num_str = s.substr(pos, end - pos);
        if (num_str.empty()) return 0.0;
        return std::stod(num_str);
    };

    p.x = find_num(json, "x");
    p.y = find_num(json, "y");
    p.z = find_num(json, "z");
    return p;
}

std::string positions_to_json(const std::vector<Waypoint>& waypoints) {
    std::string json = "[";
    for (size_t i = 0; i < waypoints.size(); ++i) {
        if (i > 0) json += ",";
        json += position_to_json(waypoints[i].position);
    }
    json += "]";
    return json;
}

std::vector<Waypoint> positions_from_json(const std::string& json) {
    std::vector<Waypoint> result;
    if (json.empty() || json[0] != '[') return result;

    // 简易解析：查找每个 { ... } 对象
    size_t i = 1;
    while (i < json.size()) {
        size_t obj_start = json.find('{', i);
        if (obj_start == std::string::npos) break;

        size_t obj_end = json.find('}', obj_start);
        if (obj_end == std::string::npos) break;

        std::string obj_str = json.substr(obj_start, obj_end - obj_start + 1);
        Position pos = position_from_json_str(obj_str);

        Waypoint wp;
        wp.position = pos;
        result.push_back(wp);

        i = obj_end + 1;
    }
    return result;
}

// ============================================================================
// WeatherData JSON 序列化/反序列化
// ============================================================================

std::string weather_to_json(const WeatherData& w) {
    return "{"
        "\"temperature\":" + json_number(w.temperature) + ","
        "\"humidity\":" + json_number(w.humidity) + ","
        "\"wind_speed\":" + json_number(w.wind_speed) + ","
        "\"wind_direction\":" + json_number(w.wind_direction) + ","
        "\"visibility\":" + json_number(w.visibility) + ","
        "\"precipitation\":" + json_number(w.precipitation) +
    "}";
}

WeatherData weather_from_json(const std::string& json) {
    WeatherData w;

    auto find_num = [&json](const std::string& key) -> double {
        size_t pos = json.find("\"" + key + "\"");
        if (pos == std::string::npos) return 0.0;
        pos = json.find(':', pos + key.size() + 2);
        if (pos == std::string::npos) return 0.0;
        ++pos;
        while (pos < json.size() && std::isspace(static_cast<unsigned char>(json[pos]))) ++pos;
        size_t end = pos;
        if (end < json.size() && json[end] == '-') ++end;
        while (end < json.size() && (std::isdigit(static_cast<unsigned char>(json[end])) ||
               json[end] == '.' || json[end] == 'e' || json[end] == 'E' ||
               json[end] == '+' || json[end] == '-')) ++end;
        std::string num_str = json.substr(pos, end - pos);
        return num_str.empty() ? 0.0 : std::stod(num_str);
    };

    w.temperature = find_num("temperature");
    w.humidity = find_num("humidity");
    w.wind_speed = find_num("wind_speed");
    w.wind_direction = find_num("wind_direction");
    w.visibility = find_num("visibility");
    w.precipitation = find_num("precipitation");

    return w;
}

} // anonymous namespace

// ============================================================================
// OfflineCache 实现
// ============================================================================

OfflineCache::OfflineCache(const std::string& cache_dir)
    : cache_dir_(cache_dir)
{
    ensure_cache_dir();

    // 创建各类型的子目录
    for (int t = 0; t < 4; ++t) {
        std::string subdir = cache_dir_ + "/" + cache_type_name(static_cast<CacheType>(t));
        create_directory(subdir);
    }

    load_index();
}

OfflineCache::~OfflineCache() {
    save_index();
}

// ============================================================================
// 缓存类型名称
// ============================================================================

std::string OfflineCache::cache_type_name(CacheType type) {
    switch (type) {
        case CacheType::PathPlan:    return "PATH_PLAN";
        case CacheType::WeatherData: return "WEATHER_DATA";
        case CacheType::Config:      return "CONFIG";
        case CacheType::MapData:     return "MAP_DATA";
        default:                     return "UNKNOWN";
    }
}

std::string OfflineCache::get_cache_filename(CacheType type) const {
    return cache_dir_ + "/" + cache_type_name(type);
}

std::string OfflineCache::sanitize_key(const std::string& key) const {
    std::string result;
    result.reserve(key.size());
    for (char c : key) {
        if (std::isalnum(static_cast<unsigned char>(c)) ||
            c == '_' || c == '-' || c == '.') {
            result += c;
        } else {
            result += '_';
        }
    }
    return result;
}

bool OfflineCache::ensure_cache_dir() const {
    return create_directory(cache_dir_);
}

// ============================================================================
// 索引管理
// ============================================================================

void OfflineCache::load_index() {
    std::lock_guard<std::mutex> lock(mutex_);
    index_.clear();

    std::string index_path = cache_dir_ + "/index.json";
    std::string content = read_file_content(index_path);
    if (content.empty() || content[0] != '{') return;

    // 简易解析索引 JSON
    // 格式: {"key1":{...}, "key2":{...}, ...}
    size_t pos = 1; // 跳过开头的 {
    while (pos < content.size()) {
        // 查找键名
        size_t key_start = content.find('"', pos);
        if (key_start == std::string::npos) break;
        size_t key_end = content.find('"', key_start + 1);
        if (key_end == std::string::npos) break;

        std::string index_key = content.substr(key_start + 1, key_end - key_start - 1);

        // 查找值对象
        size_t obj_start = content.find('{', key_end);
        if (obj_start == std::string::npos) break;
        size_t obj_end = content.find('}', obj_start);
        if (obj_end == std::string::npos) break;

        std::string obj_str = content.substr(obj_start, obj_end - obj_start + 1);

        // 解析条目字段
        CacheEntry entry;
        entry.key = index_key;

        auto find_str = [&obj_str](const std::string& key) -> std::string {
            size_t p = obj_str.find("\"" + key + "\"");
            if (p == std::string::npos) return "";
            p = obj_str.find(':', p + key.size() + 2);
            if (p == std::string::npos) return "";
            ++p;
            while (p < obj_str.size() && std::isspace(static_cast<unsigned char>(obj_str[p]))) ++p;
            if (p >= obj_str.size() || obj_str[p] != '"') return "";
            size_t val_start = p + 1;
            size_t val_end = val_start;
            while (val_end < obj_str.size() && obj_str[val_end] != '"') {
                if (obj_str[val_end] == '\\') ++val_end;
                ++val_end;
            }
            return obj_str.substr(val_start, val_end - val_start);
        };

        auto find_num_field = [&obj_str](const std::string& key) -> double {
            size_t p = obj_str.find("\"" + key + "\"");
            if (p == std::string::npos) return 0.0;
            p = obj_str.find(':', p + key.size() + 2);
            if (p == std::string::npos) return 0.0;
            ++p;
            while (p < obj_str.size() && std::isspace(static_cast<unsigned char>(obj_str[p]))) ++p;
            size_t end = p;
            if (end < obj_str.size() && obj_str[end] == '-') ++end;
            while (end < obj_str.size() && (std::isdigit(static_cast<unsigned char>(obj_str[end])) ||
                   obj_str[end] == '.')) ++end;
            std::string num_str = obj_str.substr(p, end - p);
            return num_str.empty() ? 0.0 : std::stod(num_str);
        };

        entry.data = find_str("data");
        entry.timestamp = static_cast<std::time_t>(find_num_field("timestamp"));
        entry.version = find_str("version");
        entry.ttl_seconds = static_cast<int32_t>(find_num_field("ttl"));

        index_[index_key] = entry;

        pos = obj_end + 1;
        // 跳过逗号
        while (pos < content.size() && content[pos] != ',') ++pos;
        if (pos < content.size()) ++pos;
    }
}

void OfflineCache::save_index() {
    std::lock_guard<std::mutex> lock(mutex_);

    std::string json = "{";
    bool first = true;
    for (const auto& pair : index_) {
        if (!first) json += ",";
        first = false;
        const CacheEntry& e = pair.second;
        json += json_string(pair.first) + ":{"
            + json_string("key") + ":" + json_string(e.key) + ","
            + json_string("data") + ":" + json_string(e.data) + ","
            + json_string("timestamp") + ":" + json_number(static_cast<double>(e.timestamp)) + ","
            + json_string("version") + ":" + json_string(e.version) + ","
            + json_string("ttl") + ":" + json_number(static_cast<double>(e.ttl_seconds))
            + "}";
    }
    json += "}";

    std::string index_path = cache_dir_ + "/index.json";
    write_file_content(index_path, json);
}

// ============================================================================
// 基本操作
// ============================================================================

bool OfflineCache::put(const std::string& key, const std::string& data,
                        CacheType type, int32_t ttl) {
    std::lock_guard<std::mutex> lock(mutex_);

    CacheEntry entry;
    entry.key = key;
    entry.data = data;
    entry.timestamp = std::time(nullptr);
    entry.version = "1.0";
    entry.ttl_seconds = ttl;

    // 写入数据文件
    std::string filename = get_cache_filename(type) + "/" + sanitize_key(key) + ".json";
    std::string file_content = "{"
        + json_string("key") + ":" + json_string(key) + ","
        + json_string("data") + ":" + json_string(data) + ","
        + json_string("timestamp") + ":" + json_number(static_cast<double>(entry.timestamp)) + ","
        + json_string("version") + ":" + json_string(entry.version) + ","
        + json_string("ttl") + ":" + json_number(static_cast<double>(ttl))
        + "}";

    if (!write_file_content(filename, file_content)) {
        return false;
    }

    // 更新索引
    std::string index_key = cache_type_name(type) + ":" + key;
    index_[index_key] = entry;
    save_index();
    return true;
}

std::string OfflineCache::get(const std::string& key, CacheType type) {
    std::lock_guard<std::mutex> lock(mutex_);

    std::string index_key = cache_type_name(type) + ":" + key;
    auto it = index_.find(index_key);
    if (it == index_.end()) return "";

    // 检查是否过期
    if (is_expired(key, type)) {
        // 注意：这里需要非 const 调用 remove，但我们在锁内
        // 简化处理：直接返回空
        return "";
    }

    return it->second.data;
}

bool OfflineCache::remove(const std::string& key, CacheType type) {
    std::lock_guard<std::mutex> lock(mutex_);

    std::string index_key = cache_type_name(type) + ":" + key;

    // 删除数据文件
    std::string filename = get_cache_filename(type) + "/" + sanitize_key(key) + ".json";
    std::remove(filename.c_str());

    // 从索引中移除
    auto it = index_.find(index_key);
    if (it != index_.end()) {
        index_.erase(it);
        save_index();
        return true;
    }
    return false;
}

void OfflineCache::clear(CacheType type) {
    std::lock_guard<std::mutex> lock(mutex_);

    std::string prefix = cache_type_name(type) + ":";
    auto it = index_.begin();
    while (it != index_.end()) {
        if (it->first.substr(0, prefix.size()) == prefix) {
            // 删除数据文件
            std::string key_part = it->first.substr(prefix.size());
            std::string filename = get_cache_filename(type) + "/" + sanitize_key(key_part) + ".json";
            std::remove(filename.c_str());
            it = index_.erase(it);
        } else {
            ++it;
        }
    }
    save_index();
}

void OfflineCache::clear_all() {
    for (int t = 0; t < 4; ++t) {
        clear(static_cast<CacheType>(t));
    }
}

// ============================================================================
// 查询
// ============================================================================

bool OfflineCache::exists(const std::string& key, CacheType type) const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::string index_key = cache_type_name(type) + ":" + key;
    return index_.find(index_key) != index_.end();
}

bool OfflineCache::is_expired(const std::string& key, CacheType type) const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::string index_key = cache_type_name(type) + ":" + key;
    auto it = index_.find(index_key);
    if (it == index_.end()) return true;
    if (it->second.ttl_seconds < 0) return false; // 永久有效

    std::time_t now = std::time(nullptr);
    return (now - it->second.timestamp) > static_cast<std::time_t>(it->second.ttl_seconds);
}

int OfflineCache::count(CacheType type) const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::string prefix = cache_type_name(type) + ":";
    int cnt = 0;
    for (const auto& pair : index_) {
        if (pair.first.substr(0, prefix.size()) == prefix) {
            ++cnt;
        }
    }
    return cnt;
}

std::vector<std::string> OfflineCache::list_keys(CacheType type) const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> keys;
    std::string prefix = cache_type_name(type) + ":";
    for (const auto& pair : index_) {
        if (pair.first.substr(0, prefix.size()) == prefix) {
            keys.push_back(pair.first.substr(prefix.size()));
        }
    }
    return keys;
}

// ============================================================================
// 数据更新
// ============================================================================

OfflineCache::UpdateInfo OfflineCache::get_update_info() const {
    std::lock_guard<std::mutex> lock(mutex_);
    UpdateInfo info;
    info.version = "1.0";
    info.timestamp = std::time(nullptr);
    info.entry_count = static_cast<int32_t>(index_.size());
    info.total_bytes = 0;
    for (const auto& pair : index_) {
        info.total_bytes += static_cast<int64_t>(pair.second.data.size());
    }
    return info;
}

bool OfflineCache::sync_from_file(const std::string& filepath) {
    std::string content = read_file_content(filepath);
    if (content.empty() || content[0] != '[') return false;

    // 简易解析 JSON 数组
    size_t i = 1;
    while (i < content.size()) {
        size_t obj_start = content.find('{', i);
        if (obj_start == std::string::npos) break;
        size_t obj_end = content.find('}', obj_start);
        if (obj_end == std::string::npos) break;

        std::string obj_str = content.substr(obj_start, obj_end - obj_start + 1);

        // 提取字段
        auto find_str_field = [&obj_str](const std::string& key) -> std::string {
            size_t p = obj_str.find("\"" + key + "\"");
            if (p == std::string::npos) return "";
            p = obj_str.find(':', p + key.size() + 2);
            if (p == std::string::npos) return "";
            ++p;
            while (p < obj_str.size() && std::isspace(static_cast<unsigned char>(obj_str[p]))) ++p;
            if (p >= obj_str.size() || obj_str[p] != '"') return "";
            size_t val_start = p + 1;
            size_t val_end = val_start;
            while (val_end < obj_str.size() && obj_str[val_end] != '"') {
                if (obj_str[val_end] == '\\') ++val_end;
                ++val_end;
            }
            return obj_str.substr(val_start, val_end - val_start);
        };

        auto find_num_field = [&obj_str](const std::string& key) -> int {
            size_t p = obj_str.find("\"" + key + "\"");
            if (p == std::string::npos) return 0;
            p = obj_str.find(':', p + key.size() + 2);
            if (p == std::string::npos) return 0;
            ++p;
            while (p < obj_str.size() && std::isspace(static_cast<unsigned char>(obj_str[p]))) ++p;
            size_t end = p;
            if (end < obj_str.size() && obj_str[end] == '-') ++end;
            while (end < obj_str.size() && std::isdigit(static_cast<unsigned char>(obj_str[end]))) ++end;
            std::string num_str = obj_str.substr(p, end - p);
            return num_str.empty() ? 0 : std::stoi(num_str);
        };

        std::string k = find_str_field("key");
        std::string d = find_str_field("data");
        std::string type_str = find_str_field("type");
        int ttl = find_num_field("ttl");
        if (ttl == 0) ttl = 3600;

        CacheType ct = CacheType::PathPlan;
        if (type_str == "WEATHER_DATA") ct = CacheType::WeatherData;
        else if (type_str == "CONFIG") ct = CacheType::Config;
        else if (type_str == "MAP_DATA") ct = CacheType::MapData;

        put(k, d, ct, ttl);

        i = obj_end + 1;
    }

    return true;
}

bool OfflineCache::export_to_file(const std::string& filepath, CacheType type) {
    std::lock_guard<std::mutex> lock(mutex_);

    std::string json = "[";
    bool first = true;
    std::string prefix = cache_type_name(type) + ":";
    for (const auto& pair : index_) {
        if (pair.first.substr(0, prefix.size()) == prefix) {
            if (!first) json += ",";
            first = false;
            const CacheEntry& e = pair.second;
            json += "{"
                + json_string("key") + ":" + json_string(e.key) + ","
                + json_string("data") + ":" + json_string(e.data) + ","
                + json_string("type") + ":" + json_string(cache_type_name(type)) + ","
                + json_string("ttl") + ":" + json_number(static_cast<double>(e.ttl_seconds))
                + "}";
        }
    }
    json += "]";

    return write_file_content(filepath, json);
}

// ============================================================================
// 便捷方法
// ============================================================================

bool OfflineCache::save_config(const std::string& app_name, const std::string& config_json) {
    return put(app_name, config_json, CacheType::Config, -1); // 永久有效
}

std::string OfflineCache::load_config(const std::string& app_name) {
    return get(app_name, CacheType::Config);
}

bool OfflineCache::cache_path(const std::string& key, const std::vector<Waypoint>& path) {
    std::string json = positions_to_json(path);
    return put(key, json, CacheType::PathPlan, 3600); // 1小时过期
}

std::vector<Waypoint> OfflineCache::get_cached_path(const std::string& key) {
    std::string json = get(key, CacheType::PathPlan);
    if (json.empty()) return {};
    return positions_from_json(json);
}

bool OfflineCache::cache_weather(const std::string& location_id, const WeatherData& data) {
    std::string json = weather_to_json(data);
    return put(location_id, json, CacheType::WeatherData, 1800); // 30分钟过期
}

WeatherData OfflineCache::get_cached_weather(const std::string& location_id) {
    std::string json = get(location_id, CacheType::WeatherData);
    if (json.empty()) return WeatherData{};
    return weather_from_json(json);
}

} // namespace uav::edge
