/// @file config.cpp
/// @brief 边缘计算 SDK 配置管理实现
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/config.h"

#include <fstream>
#include <sstream>
#include <algorithm>
#include <cctype>

namespace uav::edge {

// ============================================================================
// EdgeConfig 实现
// ============================================================================

bool EdgeConfig::load_from_file(const std::filesystem::path& config_path) {
    std::ifstream ifs(config_path);
    if (!ifs.is_open()) {
        return false;
    }

    std::ostringstream oss;
    oss << ifs.rdbuf();
    return load_from_string(oss.str());
}

bool EdgeConfig::load_from_string(const std::string& json_str) {
    if (json_str.empty()) return false;

    // 简易 JSON 解析：只支持扁平化 key-value 对象
    // 格式: {"key1": "value1", "key2": 123, "key3": true, ...}

    // 查找对象边界
    size_t start = json_str.find('{');
    size_t end = json_str.rfind('}');
    if (start == std::string::npos || end == std::string::npos || end <= start) {
        return false;
    }

    std::string content = json_str.substr(start + 1, end - start - 1);

    // 逐个解析键值对
    size_t pos = 0;
    while (pos < content.size()) {
        // 跳过空白和逗号
        while (pos < content.size() &&
               (content[pos] == ' ' || content[pos] == '\t' ||
                content[pos] == '\n' || content[pos] == '\r' || content[pos] == ',')) {
            ++pos;
        }
        if (pos >= content.size()) break;

        // 解析键名（字符串）
        if (content[pos] != '"') break;
        size_t key_start = pos + 1;
        size_t key_end = content.find('"', key_start);
        if (key_end == std::string::npos) break;
        std::string key = content.substr(key_start, key_end - key_start);
        pos = key_end + 1;

        // 跳过冒号
        while (pos < content.size() && content[pos] != ':') ++pos;
        if (pos >= content.size()) break;
        ++pos;

        // 跳过空白
        while (pos < content.size() &&
               (content[pos] == ' ' || content[pos] == '\t' ||
                content[pos] == '\n' || content[pos] == '\r')) {
            ++pos;
        }
        if (pos >= content.size()) break;

        // 解析值
        std::string value;
        if (content[pos] == '"') {
            // 字符串值
            size_t val_start = pos + 1;
            size_t val_end = val_start;
            while (val_end < content.size()) {
                if (content[val_end] == '\\') {
                    val_end += 2;
                    continue;
                }
                if (content[val_end] == '"') break;
                ++val_end;
            }
            value = content.substr(val_start, val_end - val_start);
            pos = val_end + 1;
        } else {
            // 数字、布尔值或 null
            size_t val_start = pos;
            while (pos < content.size() && content[pos] != ',' &&
                   content[pos] != '}' && content[pos] != '\n' &&
                   content[pos] != '\r' && content[pos] != ' ') {
                ++pos;
            }
            value = content.substr(val_start, pos - val_start);
        }

        // 去除首尾空白
        auto trim = [](std::string& s) {
            while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front())))
                s.erase(s.begin());
            while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back())))
                s.pop_back();
        };
        trim(key);
        trim(value);

        if (!key.empty() && !value.empty()) {
            config_map_[key] = value;
        }
    }

    return true;
}

bool EdgeConfig::save_to_file(const std::filesystem::path& config_path) const {
    std::string json = to_json_string();
    std::ofstream ofs(config_path);
    if (!ofs.is_open()) return false;
    ofs << json;
    return ofs.good();
}

std::string EdgeConfig::to_json_string() const {
    std::string json = "{\n";
    bool first = true;
    for (const auto& [key, value] : config_map_) {
        if (!first) json += ",\n";
        first = false;

        // 判断值类型
        bool is_string = !value.empty() &&
            (value.front() == '"' || value == "true" || value == "false" ||
             value.find(' ') != std::string::npos);

        if (is_string) {
            json += "  \"" + key + "\": \"" + value + "\"";
        } else {
            json += "  \"" + key + "\": " + value;
        }
    }
    json += "\n}";
    return json;
}

// ============================================================================
// 通用配置访问
// ============================================================================

std::optional<std::string> EdgeConfig::get_string(const std::string& key) const {
    auto it = config_map_.find(key);
    if (it == config_map_.end()) return std::nullopt;
    // 去除引号
    std::string value = it->second;
    if (value.size() >= 2 && value.front() == '"' && value.back() == '"') {
        value = value.substr(1, value.size() - 2);
    }
    return value;
}

std::optional<int64_t> EdgeConfig::get_int(const std::string& key) const {
    auto it = config_map_.find(key);
    if (it == config_map_.end()) return std::nullopt;
    try {
        return std::stoll(it->second);
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<double> EdgeConfig::get_double(const std::string& key) const {
    auto it = config_map_.find(key);
    if (it == config_map_.end()) return std::nullopt;
    try {
        return std::stod(it->second);
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<bool> EdgeConfig::get_bool(const std::string& key) const {
    auto it = config_map_.find(key);
    if (it == config_map_.end()) return std::nullopt;
    const auto& val = it->second;
    if (val == "true" || val == "1") return true;
    if (val == "false" || val == "0") return false;
    return std::nullopt;
}

void EdgeConfig::set(const std::string& key, const std::string& value) {
    config_map_[key] = "\"" + value + "\"";
}

void EdgeConfig::set(const std::string& key, int64_t value) {
    config_map_[key] = std::to_string(value);
}

void EdgeConfig::set(const std::string& key, double value) {
    config_map_[key] = std::to_string(value);
}

void EdgeConfig::set(const std::string& key, bool value) {
    config_map_[key] = value ? "true" : "false";
}

bool EdgeConfig::has(const std::string& key) const {
    return config_map_.find(key) != config_map_.end();
}

void EdgeConfig::remove(const std::string& key) {
    config_map_.erase(key);
}

// ============================================================================
// 带命名空间的配置访问
// ============================================================================

std::optional<std::string> EdgeConfig::get_namespaced(
    const std::string& ns,
    const std::string& key
) const {
    return get_string(ns + "." + key);
}

std::string EdgeConfig::get_with_default(
    const std::string& key,
    const std::string& default_value
) const {
    auto val = get_string(key);
    return val.has_value() ? val.value() : default_value;
}

// ============================================================================
// 路径规划配置
// ============================================================================

std::string EdgeConfig::path_planner_algorithm() const {
    return get_with_default("path_planner.algorithm", "astar");
}

double EdgeConfig::path_planner_resolution() const {
    auto val = get_double("path_planner.resolution");
    return val.has_value() ? val.value() : 1.0;
}

uint32_t EdgeConfig::rrt_max_iterations() const {
    auto val = get_int("path_planner.rrt_max_iterations");
    return val.has_value() ? static_cast<uint32_t>(val.value()) : 5000;
}

// ============================================================================
// 风险评估配置
// ============================================================================

double EdgeConfig::risk_wind_speed_threshold() const {
    auto val = get_double("risk.wind_speed_threshold");
    return val.has_value() ? val.value() : 15.0;
}

double EdgeConfig::risk_visibility_threshold() const {
    auto val = get_double("risk.visibility_threshold");
    return val.has_value() ? val.value() : 2000.0;
}

// ============================================================================
// V2X 通信配置
// ============================================================================

V2XTechnology EdgeConfig::v2x_technology() const {
    std::string tech = get_with_default("v2x.technology", "dsrc");
    // 转小写比较
    std::string lower = tech;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
    if (lower == "cv2x" || lower == "c-v2x") {
        return V2XTechnology::CV2X;
    }
    return V2XTechnology::DSRC;
}

uint8_t EdgeConfig::v2x_dsrc_channel() const {
    auto val = get_int("v2x.dsrc_channel");
    return val.has_value() ? static_cast<uint8_t>(val.value()) : 178;
}

double EdgeConfig::v2x_tx_power() const {
    auto val = get_double("v2x.tx_power");
    return val.has_value() ? val.value() : 20.0;
}

// ============================================================================
// 联邦学习配置
// ============================================================================

std::string EdgeConfig::federated_server_url() const {
    return get_with_default("federated.server_url", "http://localhost:5000");
}

std::string EdgeConfig::federated_aggregation_strategy() const {
    return get_with_default("federated.aggregation_strategy", "fedavg");
}

// ============================================================================
// 模型推理配置
// ============================================================================

std::string EdgeConfig::model_runtime_backend() const {
    return get_with_default("model_runtime.backend", "onnxruntime");
}

std::string EdgeConfig::model_runtime_device() const {
    return get_with_default("model_runtime.device", "CPU");
}

InferencePrecision EdgeConfig::model_runtime_precision() const {
    std::string prec = get_with_default("model_runtime.precision", "fp32");
    std::string lower = prec;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
    if (lower == "fp16") return InferencePrecision::FP16;
    if (lower == "int8") return InferencePrecision::INT8;
    return InferencePrecision::FP32;
}

int EdgeConfig::model_runtime_num_threads() const {
    auto val = get_int("model_runtime.num_threads");
    return val.has_value() ? static_cast<int>(val.value()) : 1;
}

} // namespace uav::edge
