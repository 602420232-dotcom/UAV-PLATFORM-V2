#include "offline_cache.h"
#include <algorithm>
#include <cctype>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <sys/stat.h>
#include <sys/types.h>

#ifdef _WIN32
#include <direct.h>
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace uav_sdk {

namespace {

// ─── 简单 JSON 序列化/反序列化工具 ────────────────────────────────────────────

std::string json_escape(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 2);
    for (char c : s) {
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\b': out += "\\b";  break;
            case '\f': out += "\\f";  break;
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
    std::ostringstream oss;
    oss.precision(15);
    // 如果是整数，不输出小数点
    if (v == std::floor(v) && std::isfinite(v) && std::fabs(v) < 1e15) {
        oss << static_cast<long long>(v);
    } else {
        oss << v;
    }
    return oss.str();
}

std::string json_bool(bool b) {
    return b ? "true" : "false";
}

// 简单的 JSON 令牌解析器
class JsonParser {
public:
    explicit JsonParser(const std::string& input) : input_(input), pos_(0) {}

    bool ok() const { return !error_; }

    // 解析根值
    bool parse() {
        skip_ws();
        if (pos_ >= input_.size()) {
            error_ = true;
            return false;
        }
        value_ = parse_value();
        return !error_;
    }

    // 获取解析后的值（原始字符串表示）
    const std::string& value_str() const { return value_; }

    // 便利方法：提取字符串值（去掉引号）
    std::string parse_string() {
        skip_ws();
        if (pos_ >= input_.size() || input_[pos_] != '"') {
            error_ = true;
            return "";
        }
        ++pos_; // 跳过开头引号
        std::string result;
        while (pos_ < input_.size() && input_[pos_] != '"') {
            if (input_[pos_] == '\\') {
                ++pos_;
                if (pos_ >= input_.size()) break;
                switch (input_[pos_]) {
                    case '"': result += '"'; break;
                    case '\\': result += '\\'; break;
                    case '/': result += '/'; break;
                    case 'b': result += '\b'; break;
                    case 'f': result += '\f'; break;
                    case 'n': result += '\n'; break;
                    case 'r': result += '\r'; break;
                    case 't': result += '\t'; break;
                    case 'u': {
                        // 简单的 unicode 转义处理（仅支持 BMP）
                        char hex[5] = {0};
                        for (int i = 0; i < 4; ++i) {
                            if (pos_ + 1 + i >= input_.size()) break;
                            hex[i] = input_[pos_ + 1 + i];
                        }
                        unsigned int code = 0;
                        std::sscanf(hex, "%x", &code);
                        if (code <= 0x7F) {
                            result += static_cast<char>(code);
                        } else if (code <= 0x7FF) {
                            result += static_cast<char>(0xC0 | (code >> 6));
                            result += static_cast<char>(0x80 | (code & 0x3F));
                        } else {
                            result += static_cast<char>(0xE0 | (code >> 12));
                            result += static_cast<char>(0x80 | ((code >> 6) & 0x3F));
                            result += static_cast<char>(0x80 | (code & 0x3F));
                        }
                        pos_ += 4;
                        break;
                    }
                    default: result += input_[pos_]; break;
                }
                ++pos_;
            } else {
                result += input_[pos_];
                ++pos_;
            }
        }
        if (pos_ < input_.size()) ++pos_; // 跳过结尾引号
        return result;
    }

    // 从当前 JSON 对象中获取指定键的值
    std::string get_string_value(const std::string& key, const std::string& json_obj) {
        size_t pos = 0;
        return extract_key(key, json_obj, pos);
    }

    // 从 JSON 对象中提取数值
    double get_number_value(const std::string& key, const std::string& json_obj, double default_val = 0.0) {
        size_t pos = 0;
        std::string val = extract_key(key, json_obj, pos);
        if (val.empty()) return default_val;
        char* end = nullptr;
        double result = std::strtod(val.c_str(), &end);
        return (end != val.c_str()) ? result : default_val;
    }

    // 从 JSON 对象中提取布尔值
    bool get_bool_value(const std::string& key, const std::string& json_obj, bool default_val = false) {
        size_t pos = 0;
        std::string val = extract_key(key, json_obj, pos);
        if (val == "true") return true;
        if (val == "false") return false;
        return default_val;
    }

    // 从 JSON 对象中提取整数值
    int get_int_value(const std::string& key, const std::string& json_obj, int default_val = 0) {
        return static_cast<int>(get_number_value(key, json_obj, static_cast<double>(default_val)));
    }

    // 从 JSON 对象中提取字符串（已去引号）
    std::string get_unescaped_string(const std::string& key, const std::string& json_obj,
                                      const std::string& default_val = "") {
        size_t pos = 0;
        std::string raw = extract_key(key, json_obj, pos);
        if (raw.empty()) return default_val;
        // 手动解析字符串
        JsonParser p(raw);
        return p.parse_string();
    }

private:
    std::string input_;
    size_t pos_;
    bool error_ = false;
    std::string value_;

    void skip_ws() {
        while (pos_ < input_.size() &&
               (input_[pos_] == ' ' || input_[pos_] == '\t' ||
                input_[pos_] == '\n' || input_[pos_] == '\r')) {
            ++pos_;
        }
    }

    std::string parse_value() {
        skip_ws();
        if (pos_ >= input_.size()) {
            error_ = true;
            return "";
        }
        char c = input_[pos_];
        if (c == '{') return parse_object();
        if (c == '[') return parse_array();
        if (c == '"') return parse_string_token();
        if (c == 't' || c == 'f') return parse_bool();
        if (c == 'n') return parse_null();
        return parse_number();
    }

    std::string parse_string_token() {
        skip_ws();
        if (pos_ >= input_.size() || input_[pos_] != '"') {
            error_ = true;
            return "";
        }
        size_t start = pos_;
        ++pos_;
        while (pos_ < input_.size()) {
            if (input_[pos_] == '\\') {
                pos_ += 2;
                continue;
            }
            if (input_[pos_] == '"') {
                ++pos_;
                return input_.substr(start, pos_ - start);
            }
            ++pos_;
        }
        error_ = true;
        return "";
    }

    std::string parse_number() {
        skip_ws();
        size_t start = pos_;
        if (pos_ < input_.size() && (input_[pos_] == '-' || input_[pos_] == '+')) {
            ++pos_;
        }
        while (pos_ < input_.size() && std::isdigit(static_cast<unsigned char>(input_[pos_]))) {
            ++pos_;
        }
        if (pos_ < input_.size() && input_[pos_] == '.') {
            ++pos_;
            while (pos_ < input_.size() && std::isdigit(static_cast<unsigned char>(input_[pos_]))) {
                ++pos_;
            }
        }
        if (pos_ < input_.size() && (input_[pos_] == 'e' || input_[pos_] == 'E')) {
            ++pos_;
            if (pos_ < input_.size() && (input_[pos_] == '-' || input_[pos_] == '+')) ++pos_;
            while (pos_ < input_.size() && std::isdigit(static_cast<unsigned char>(input_[pos_]))) {
                ++pos_;
            }
        }
        return input_.substr(start, pos_ - start);
    }

    std::string parse_object() {
        skip_ws();
        if (pos_ >= input_.size() || input_[pos_] != '{') {
            error_ = true;
            return "";
        }
        size_t start = pos_;
        int depth = 0;
        ++pos_;
        bool in_string = false;
        while (pos_ < input_.size()) {
            char c = input_[pos_];
            if (in_string) {
                if (c == '\\') {
                    pos_ += 2;
                    continue;
                }
                if (c == '"') in_string = false;
            } else {
                if (c == '"') in_string = true;
                else if (c == '{') ++depth;
                else if (c == '}') {
                    if (depth == 0) {
                        ++pos_;
                        return input_.substr(start, pos_ - start);
                    }
                    --depth;
                }
            }
            ++pos_;
        }
        error_ = true;
        return "";
    }

    std::string parse_array() {
        skip_ws();
        if (pos_ >= input_.size() || input_[pos_] != '[') {
            error_ = true;
            return "";
        }
        size_t start = pos_;
        int depth = 0;
        ++pos_;
        bool in_string = false;
        while (pos_ < input_.size()) {
            char c = input_[pos_];
            if (in_string) {
                if (c == '\\') { pos_ += 2; continue; }
                if (c == '"') in_string = false;
            } else {
                if (c == '"') in_string = true;
                else if (c == '[') ++depth;
                else if (c == ']') {
                    if (depth == 0) {
                        ++pos_;
                        return input_.substr(start, pos_ - start);
                    }
                    --depth;
                }
            }
            ++pos_;
        }
        error_ = true;
        return "";
    }

    std::string parse_bool() {
        skip_ws();
        if (input_.substr(pos_, 4) == "true") {
            pos_ += 4;
            return "true";
        }
        if (input_.substr(pos_, 5) == "false") {
            pos_ += 5;
            return "false";
        }
        error_ = true;
        return "";
    }

    std::string parse_null() {
        skip_ws();
        if (input_.substr(pos_, 4) == "null") {
            pos_ += 4;
            return "null";
        }
        error_ = true;
        return "";
    }

    // 从 JSON 对象字符串中提取键的值（低层级实现）
    std::string extract_key(const std::string& key, const std::string& json_obj, size_t& pos) {
        // 跳过开头的 {
        pos = 0;
        size_t len = json_obj.size();
        // 找到第一个非空白字符
        while (pos < len && (json_obj[pos] == ' ' || json_obj[pos] == '\t' ||
                             json_obj[pos] == '\n' || json_obj[pos] == '\r')) {
            ++pos;
        }
        if (pos >= len || json_obj[pos] != '{') return "";

        bool in_str = false;
        bool found_key = false;
        std::string current_key;
        size_t i = pos + 1;

        while (i < len) {
            // 跳过空白
            while (i < len && (json_obj[i] == ' ' || json_obj[i] == '\t' ||
                               json_obj[i] == '\n' || json_obj[i] == '\r')) {
                ++i;
            }
            if (i >= len) break;

            if (json_obj[i] == '}') break;

            if (!found_key) {
                // 解析键名（字符串）
                if (json_obj[i] != '"') { ++i; continue; }
                size_t key_start = i;
                ++i;
                while (i < len && json_obj[i] != '"') {
                    if (json_obj[i] == '\\') ++i;
                    ++i;
                }
                if (i >= len) break;
                ++i;
                current_key = json_obj.substr(key_start, i - key_start);
                // 解析引号内的实际内容
                JsonParser p(current_key);
                std::string actual_key = p.parse_string();
                found_key = (actual_key == key);

                // 跳过冒号
                while (i < len && json_obj[i] != ':') ++i;
                if (i < len) ++i;
            } else {
                // 解析值
                while (i < len && (json_obj[i] == ' ' || json_obj[i] == '\t' ||
                                   json_obj[i] == '\n' || json_obj[i] == '\r')) {
                    ++i;
                }
                if (i >= len) break;

                size_t val_start = i;
                if (json_obj[i] == '"') {
                    // 字符串值
                    ++i;
                    while (i < len && json_obj[i] != '"') {
                        if (json_obj[i] == '\\') ++i;
                        ++i;
                    }
                    if (i < len) ++i;
                } else if (json_obj[i] == '{' || json_obj[i] == '[') {
                    char close = (json_obj[i] == '{') ? '}' : ']';
                    int depth = 0;
                    ++i;
                    bool in_substr = false;
                    while (i < len) {
                        if (in_substr) {
                            if (json_obj[i] == '\\') { ++i; }
                            else if (json_obj[i] == '"') in_substr = false;
                        } else {
                            if (json_obj[i] == '"') in_substr = true;
                            else if (json_obj[i] == close && depth == 0) { ++i; break; }
                            else if (json_obj[i] == '{' || json_obj[i] == '[') ++depth;
                            else if (json_obj[i] == '}' || json_obj[i] == ']') --depth;
                        }
                        ++i;
                    }
                } else {
                    // 数字、布尔值、null
                    while (i < len && json_obj[i] != ',' && json_obj[i] != '}' &&
                           json_obj[i] != ' ' && json_obj[i] != '\t' &&
                           json_obj[i] != '\n' && json_obj[i] != '\r') {
                        ++i;
                    }
                }

                if (found_key) {
                    return json_obj.substr(val_start, i - val_start);
                }
                found_key = false;
                // 跳过逗号
                if (i < len && json_obj[i] == ',') ++i;
            }
        }
        return "";
    }
};

// ─── 目录创建辅助函数 ────────────────────────────────────────────────────────

bool create_directory(const std::string& path) {
#ifdef _WIN32
    return _mkdir(path.c_str()) == 0 || errno == EEXIST;
#else
    return mkdir(path.c_str(), 0755) == 0 || errno == EEXIST;
#endif
}

// ─── 缓存类型名称 ────────────────────────────────────────────────────────────

std::string cache_type_name(OfflineCache::CacheType type) {
    switch (type) {
        case OfflineCache::PATH_PLAN:    return "PATH_PLAN";
        case OfflineCache::WEATHER_DATA: return "WEATHER_DATA";
        case OfflineCache::CONFIG:       return "CONFIG";
        case OfflineCache::MAP_DATA:     return "MAP_DATA";
        default:                         return "UNKNOWN";
    }
}

// ─── 读取/写入文件 ───────────────────────────────────────────────────────────

std::string read_file(const std::string& filepath) {
    std::ifstream ifs(filepath);
    if (!ifs.is_open()) return "";
    std::ostringstream oss;
    oss << ifs.rdbuf();
    return oss.str();
}

bool write_file(const std::string& filepath, const std::string& content) {
    std::ofstream ofs(filepath);
    if (!ofs.is_open()) return false;
    ofs << content;
    return ofs.good();
}

// ─── Point JSON 序列化 ───────────────────────────────────────────────────────

std::string point_to_json(const Point& p) {
    return "{\"x\":" + json_number(static_cast<double>(p.x)) +
           ",\"y\":" + json_number(static_cast<double>(p.y)) + "}";
}

std::string points_to_json(const std::vector<Point>& points) {
    std::string json = "[";
    for (size_t i = 0; i < points.size(); ++i) {
        if (i > 0) json += ",";
        json += point_to_json(points[i]);
    }
    json += "]";
    return json;
}

std::vector<Point> points_from_json(const std::string& json) {
    std::vector<Point> result;
    if (json.empty() || json[0] != '[') return result;

    // 手动遍历数组
    bool in_string = false;
    int depth = 0;
    std::string current_obj;
    for (size_t i = 0; i < json.size(); ++i) {
        if (in_string) {
            current_obj += json[i];
            if (json[i] == '\\' && i + 1 < json.size()) {
                ++i;
                current_obj += json[i];
            } else if (json[i] == '"') {
                in_string = false;
            }
        } else {
            if (json[i] == '"') {
                in_string = true;
                current_obj += json[i];
            } else if (json[i] == '{') {
                if (depth > 0) current_obj += json[i];
                ++depth;
            } else if (json[i] == '}') {
                --depth;
                if (depth > 0) {
                    current_obj += json[i];
                } else if (depth == 0) {
                    current_obj += json[i];
                    // 解析这个对象
                    JsonParser parser(current_obj);
                    if (parser.parse()) {
                        int x = static_cast<int>(parser.get_number_value("x", current_obj));
                        int y = static_cast<int>(parser.get_number_value("y", current_obj));
                        result.push_back(Point(x, y));
                    }
                    current_obj.clear();
                }
            } else if (depth > 0) {
                current_obj += json[i];
            }
        }
    }
    return result;
}

// ─── WeatherData JSON 序列化 ─────────────────────────────────────────────────

std::string weather_to_json(const WeatherData& w) {
    return "{"
        + json_string("wind_speed") + ":" + json_number(w.wind_speed) + ","
        + json_string("wind_direction") + ":" + json_number(w.wind_direction) + ","
        + json_string("temperature") + ":" + json_number(w.temperature) + ","
        + json_string("humidity") + ":" + json_number(w.humidity) + ","
        + json_string("visibility") + ":" + json_number(w.visibility) + ","
        + json_string("precipitation") + ":" + json_number(w.precipitation) + ","
        + json_string("has_thunderstorm") + ":" + json_bool(w.has_thunderstorm)
        + "}";
}

WeatherData weather_from_json(const std::string& json) {
    WeatherData w = {0, 0, 0, 0, 0, 0, false};
    if (json.empty()) return w;
    JsonParser parser(json);
    if (!parser.parse()) return w;

    w.wind_speed = parser.get_number_value("wind_speed", json);
    w.wind_direction = parser.get_number_value("wind_direction", json);
    w.temperature = parser.get_number_value("temperature", json);
    w.humidity = parser.get_number_value("humidity", json);
    w.visibility = parser.get_number_value("visibility", json);
    w.precipitation = parser.get_number_value("precipitation", json);
    w.has_thunderstorm = parser.get_bool_value("has_thunderstorm", json);
    return w;
}

}  // anonymous namespace

// ─── OfflineCache 实现 ───────────────────────────────────────────────────────

OfflineCache::OfflineCache(const std::string& cache_dir)
    : cache_dir_(cache_dir) {
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

std::string OfflineCache::sanitize_key(const std::string& key) const {
    std::string result;
    result.reserve(key.size());
    for (char c : key) {
        if (std::isalnum(static_cast<unsigned char>(c)) || c == '_' || c == '-' || c == '.') {
            result += c;
        } else {
            // 将非安全字符替换为下划线
            result += '_';
        }
    }
    return result;
}

std::string OfflineCache::get_cache_filename(CacheType type) const {
    return cache_dir_ + "/" + cache_type_name(type);
}

bool OfflineCache::ensure_cache_dir() const {
    return create_directory(cache_dir_);
}

void OfflineCache::load_index() {
    std::lock_guard<std::mutex> lock(mutex_);
    index_.clear();

    std::string index_path = cache_dir_ + "/index.json";
    std::string content = read_file(index_path);
    if (content.empty()) return;

    // 解析索引 JSON
    // 格式: {"key1":{"key":"k1","data":"...","timestamp":...,"version":"...","ttl":...}, ...}
    size_t pos = 0;
    // 跳过外层 {
    while (pos < content.size() && content[pos] != '{') ++pos;
    if (pos >= content.size()) return;
    ++pos;

    bool in_string = false;
    bool reading_key = true;
    std::string current_key;

    for (size_t i = pos; i < content.size(); ++i) {
        if (in_string) {
            if (content[i] == '\\') { ++i; continue; }
            if (content[i] == '"') in_string = false;
            continue;
        }
        if (content[i] == '"') {
            in_string = true;
            continue;
        }
        if (content[i] == '{') {
            // 找到一个条目对象
            size_t start = i;
            int depth = 0;
            bool obj_in_str = false;
            while (i < content.size()) {
                if (obj_in_str) {
                    if (content[i] == '\\') { ++i; }
                    else if (content[i] == '"') obj_in_str = false;
                } else {
                    if (content[i] == '"') obj_in_str = true;
                    else if (content[i] == '{') ++depth;
                    else if (content[i] == '}') {
                        if (depth == 0) break;
                        --depth;
                    }
                }
                ++i;
            }
            std::string entry_json = content.substr(start, i - start + 1);

            JsonParser parser(entry_json);
            if (parser.parse()) {
                CacheEntry entry;
                entry.key = parser.get_unescaped_string("key", entry_json);
                entry.data = parser.get_unescaped_string("data", entry_json);
                entry.timestamp = static_cast<std::time_t>(parser.get_int_value("timestamp", entry_json));
                entry.version = parser.get_unescaped_string("version", entry_json);
                entry.ttl_seconds = parser.get_int_value("ttl", entry_json, -1);
                index_[entry.key] = entry;
            }
        }
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
        json += json_string(e.key) + ":{"
            + json_string("key") + ":" + json_string(e.key) + ","
            + json_string("data") + ":" + json_string(e.data) + ","
            + json_string("timestamp") + ":" + json_number(static_cast<double>(e.timestamp)) + ","
            + json_string("version") + ":" + json_string(e.version) + ","
            + json_string("ttl") + ":" + json_number(static_cast<double>(e.ttl_seconds))
            + "}";
    }
    json += "}";

    std::string index_path = cache_dir_ + "/index.json";
    write_file(index_path, json);
}

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

    if (!write_file(filename, file_content)) {
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
        remove(key, type);
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
    return (now - it->second.timestamp) > it->second.ttl_seconds;
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
    std::string content = read_file(filepath);
    if (content.empty()) return false;

    // 期望 JSON 数组格式
    // [{"key":"...","data":"...","type":"...","ttl":...}, ...]
    if (content.empty() || content[0] != '[') return false;

    bool in_str = false;
    int depth = 0;
    std::string current_entry;
    for (size_t i = 1; i < content.size(); ++i) {
        if (in_str) {
            current_entry += content[i];
            if (content[i] == '\\' && i + 1 < content.size()) {
                ++i;
                current_entry += content[i];
            } else if (content[i] == '"') {
                in_str = false;
            }
        } else {
            if (content[i] == '"') {
                in_str = true;
                current_entry += content[i];
            } else if (content[i] == '{') {
                ++depth;
                if (depth == 1) current_entry = "{";
                else current_entry += content[i];
            } else if (content[i] == '}') {
                --depth;
                if (depth == 0) {
                    current_entry += "}";
                    // 解析并插入条目
                    JsonParser parser(current_entry);
                    if (parser.parse()) {
                        std::string k = parser.get_unescaped_string("key", current_entry);
                        std::string d = parser.get_unescaped_string("data", current_entry);
                        std::string type_str = parser.get_unescaped_string("type", current_entry, "PATH_PLAN");
                        int ttl = parser.get_int_value("ttl", current_entry, 3600);

                        CacheType ct = PATH_PLAN;
                        if (type_str == "WEATHER_DATA") ct = WEATHER_DATA;
                        else if (type_str == "CONFIG") ct = CONFIG;
                        else if (type_str == "MAP_DATA") ct = MAP_DATA;

                        put(k, d, ct, ttl);
                    }
                    current_entry.clear();
                } else {
                    current_entry += content[i];
                }
            } else if (depth > 0) {
                current_entry += content[i];
            }
        }
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

    return write_file(filepath, json);
}

bool OfflineCache::save_config(const std::string& app_name, const std::string& config_json) {
    return put(app_name, config_json, CONFIG, -1);
}

std::string OfflineCache::load_config(const std::string& app_name) {
    return get(app_name, CONFIG);
}

bool OfflineCache::cache_path(const std::string& key, const std::vector<Point>& path) {
    std::string json = points_to_json(path);
    return put(key, json, PATH_PLAN, 3600);
}

std::vector<Point> OfflineCache::get_cached_path(const std::string& key) {
    std::string json = get(key, PATH_PLAN);
    if (json.empty()) return {};
    return points_from_json(json);
}

bool OfflineCache::cache_weather(const std::string& location_id, const WeatherData& data) {
    std::string json = weather_to_json(data);
    return put(location_id, json, WEATHER_DATA, 1800); // 气象数据 30 分钟过期
}

WeatherData OfflineCache::get_cached_weather(const std::string& location_id) {
    std::string json = get(location_id, WEATHER_DATA);
    if (json.empty()) return WeatherData{0, 0, 0, 0, 0, 0, false};
    return weather_from_json(json);
}

}  // namespace uav_sdk
