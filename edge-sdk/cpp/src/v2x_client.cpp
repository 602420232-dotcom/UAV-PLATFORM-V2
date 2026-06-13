/// @file v2x_client.cpp
/// @brief V2X 通信客户端实现（DSRC）
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/v2x_client.h"

#include <cmath>
#include <algorithm>
#include <chrono>
#include <random>
#include <sstream>

namespace uav::edge {

// ============================================================================
// DSRCClient 构造/析构
// ============================================================================

DSRCClient::DSRCClient(const std::string& device_id)
    : device_id_(device_id)
{
    // 自动生成设备 ID（如果未提供）
    if (device_id_.empty()) {
        auto now = std::chrono::steady_clock::now().time_since_epoch().count();
        device_id_ = "UAV-" + std::to_string(now);
    }

    // 初始化信道质量统计
    channel_stats_ = ChannelQuality{};
}

// ============================================================================
// 初始化与生命周期
// ============================================================================

void DSRCClient::initialize(const std::string& config) {
    // 简单配置解析
    // 格式: "channel:178,tx_power:20.0"
    (void)config;
}

void DSRCClient::start() {
    running_ = true;

    // 初始化信道统计
    channel_stats_ = ChannelQuality{
        30.0,   // SNR (dB)
        0.05,   // 丢包率
        50.0,   // 延迟 (ms)
        6.0,    // 带宽 (Mbps)
        1e-6    // 误比特率
    };
}

void DSRCClient::stop() {
    running_ = false;
}

bool DSRCClient::is_running() const {
    return running_;
}

// ============================================================================
// 消息收发
// ============================================================================

size_t DSRCClient::broadcast(const V2XMessage& message) {
    if (!running_) return 0;

    // 模拟广播：根据信道质量计算接收方数量
    // DSRC 通信范围通常 300-1000m
    double range = 500.0; // 默认通信范围 (m)

    // 根据发射功率调整通信范围
    double power_factor = std::pow(10.0, (tx_power_ - 20.0) / 10.0);
    range *= std::sqrt(power_factor);

    // 模拟接收方数量（基于通信范围和信道质量）
    size_t receivers = static_cast<size_t>(
        range / 50.0 * (1.0 - channel_stats_.packet_loss_rate)
    );

    // 触发回调（模拟接收自己发送的消息不回调）
    (void)message;

    return receivers;
}

bool DSRCClient::unicast(const V2XMessage& message, const std::string& receiver_id) {
    if (!running_) return false;
    if (receiver_id.empty()) return false;

    // 模拟单播发送
    // 根据丢包率决定是否成功
    std::mt19937 rng(static_cast<unsigned>(
        std::chrono::steady_clock::now().time_since_epoch().count()));
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    bool success = dist(rng) > channel_stats_.packet_loss_rate;
    (void)message;

    return success;
}

size_t DSRCClient::geobroadcast(
    const V2XMessage& message,
    const Position& center,
    double radius_m
) {
    if (!running_) return 0;

    // 地理广播：只向指定区域内的设备广播
    // 模拟计算区域内的设备数量
    double area = M_PI * radius_m * radius_m; // 区域面积 (m^2)
    double device_density = 0.0001; // 设备密度 (设备/m^2)
    size_t devices_in_area = static_cast<size_t>(area * device_density);

    // 根据信道质量过滤
    size_t successful = static_cast<size_t>(
        devices_in_area * (1.0 - channel_stats_.packet_loss_rate)
    );

    (void)message;
    (void)center;

    return successful;
}

// ============================================================================
// 信道评估
// ============================================================================

ChannelQuality DSRCClient::evaluate_channel(const Position& target_position) {
    ChannelQuality quality;

    // 计算到目标的距离（使用设备自身位置，简化为固定位置）
    double distance = std::sqrt(
        target_position.x * target_position.x +
        target_position.y * target_position.y +
        target_position.z * target_position.z
    );

    // 自由空间路径损耗模型
    double path_loss = calculate_path_loss(
        Position{}, target_position, 5.89e9 // DSRC CH178 频率
    );

    // 计算 SNR
    double snr = calculate_snr(path_loss);
    quality.snr = snr;

    // 估算丢包率
    quality.packet_loss_rate = estimate_packet_loss(snr, distance);

    // 估算延迟
    quality.latency_ms = 10.0 + distance * 0.001 + channel_stats_.packet_loss_rate * 50.0;

    // 估算带宽
    quality.bandwidth_mbps = std::max(0.1, 6.0 * (1.0 - quality.packet_loss_rate));

    // 估算误比特率
    quality.ber = std::max(1e-9, std::pow(10.0, -snr / 10.0) * 0.01);

    return quality;
}

std::vector<std::string> DSRCClient::discover_topology() {
    // 模拟拓扑发现：返回模拟的可见节点列表
    std::vector<std::string> nodes;

    if (!running_) return nodes;

    // 模拟发现 3-8 个节点
    std::mt19937 rng(static_cast<unsigned>(
        std::chrono::steady_clock::now().time_since_epoch().count()));
    std::uniform_int_distribution<int> count_dist(3, 8);
    int count = count_dist(rng);

    for (int i = 0; i < count; ++i) {
        std::ostringstream oss;
        oss << "NODE-" << (1000 + i);
        nodes.push_back(oss.str());
    }

    return nodes;
}

void DSRCClient::on_message_received(
    std::function<void(const V2XMessage&)> callback
) {
    message_callback_ = std::move(callback);
}

// ============================================================================
// 配置方法
// ============================================================================

void DSRCClient::set_channel(uint8_t channel) {
    // IEEE 802.11p 合法频道
    static const uint8_t valid_channels[] = {172, 174, 176, 178, 180, 182};
    for (auto ch : valid_channels) {
        if (channel == ch) {
            channel_ = channel;
            return;
        }
    }
    // 无效频道，保持默认
}

void DSRCClient::set_tx_power(double power_dbm) {
    // DSRC 发射功率范围: 0-33 dBm
    tx_power_ = std::clamp(power_dbm, 0.0, 33.0);
}

const ChannelQuality& DSRCClient::channel_stats() const {
    return channel_stats_;
}

std::string DSRCClient::client_id() const {
    return device_id_;
}

// ============================================================================
// 物理层模型
// ============================================================================

/// 自由空间路径损耗模型 (dB)
/// FSPL = 20*log10(d) + 20*log10(f) + 20*log10(4*pi/c)
double DSRCClient::calculate_path_loss(
    const Position& sender,
    const Position& receiver,
    double frequency_hz
) const {
    double distance = sender.distance_to(receiver);
    if (distance < 1.0) distance = 1.0; // 最小距离 1m

    // 光速
    constexpr double speed_of_light = 3.0e8;

    // 自由空间路径损耗
    double fspl = 20.0 * std::log10(distance) +
                  20.0 * std::log10(frequency_hz) -
                  20.0 * std::log10(speed_of_light / (4.0 * M_PI));

    return fspl;
}

/// 计算 SNR (dB)
/// SNR = Tx_power - Path_loss - Noise_floor
double DSRCClient::calculate_snr(double path_loss_db) const {
    constexpr double noise_floor = -95.0; // 热噪声基底 (dBm)
    double rx_power = tx_power_ - path_loss_db; // 接收功率
    return rx_power - noise_floor;
}

/// 仿真丢包率
/// 基于 SNR 和距离的简化模型
double DSRCClient::estimate_packet_loss(double snr_db, double distance_m) const {
    if (snr_db > 25.0) return 0.01;  // 优秀信道
    if (snr_db > 15.0) return 0.05;  // 良好信道
    if (snr_db > 10.0) return 0.15;  // 一般信道
    if (snr_db > 5.0) return 0.40;   // 较差信道

    // 距离衰减因子
    double distance_factor = 1.0;
    if (distance_m > 300.0) {
        distance_factor = 1.0 + (distance_m - 300.0) / 700.0;
    }

    return std::min(0.95, 0.7 * distance_factor); // 极差信道
}

// ============================================================================
// 工厂函数
// ============================================================================

std::unique_ptr<IV2XClient> create_v2x_client(
    V2XTechnology technology,
    const std::string& device_id
) {
    switch (technology) {
        case V2XTechnology::DSRC:
            return std::make_unique<DSRCClient>(device_id);
        case V2XTechnology::CV2X:
            // C-V2X 暂未实现，回退到 DSRC
            return std::make_unique<DSRCClient>(device_id);
        default:
            return std::make_unique<DSRCClient>(device_id);
    }
}

} // namespace uav::edge
