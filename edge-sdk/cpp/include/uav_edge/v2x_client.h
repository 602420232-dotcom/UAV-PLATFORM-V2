#pragma once

/// @file v2x_client.h
/// @brief V2X 车联网通信客户端接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <memory>
#include <vector>
#include <functional>
#include <string>

namespace uav::edge {

// ============================================================================
// V2X 通信客户端抽象接口
// ============================================================================

/// V2X 通信客户端抽象基类
/// 支持 DSRC 和 C-V2X 两种通信技术
class IV2XClient {
public:
    virtual ~IV2XClient() = default;

    /// 初始化 V2X 通信客户端
    /// @param config 配置参数（JSON 格式字符串）
    virtual void initialize(const std::string& config) = 0;

    /// 启动通信服务
    virtual void start() = 0;

    /// 停止通信服务
    virtual void stop() = 0;

    /// 广播消息
    /// @param message 待广播的消息
    /// @return 成功接收的接收方数量
    virtual size_t broadcast(const V2XMessage& message) = 0;

    /// 单播消息
    /// @param message 待发送的消息
    /// @param receiver_id 接收方 ID
    /// @return 发送是否成功
    virtual bool unicast(const V2XMessage& message, const std::string& receiver_id) = 0;

    /// 地理广播（向指定区域内的设备广播）
    /// @param message 待广播的消息
    /// @param center 区域中心
    /// @param radius_m 广播半径 (m)
    /// @return 成功接收的接收方数量
    virtual size_t geobroadcast(
        const V2XMessage& message,
        const Position& center,
        double radius_m
    ) = 0;

    /// 评估信道质量
    /// @param target_position 目标位置
    /// @return 信道质量信息
    virtual ChannelQuality evaluate_channel(const Position& target_position) = 0;

    /// 获取网络拓扑信息
    /// @return 当前可见节点 ID 列表
    virtual std::vector<std::string> discover_topology() = 0;

    /// 注册消息接收回调
    /// @param callback 消息回调函数
    virtual void on_message_received(std::function<void(const V2XMessage&)> callback) = 0;

    /// 获取客户端标识
    [[nodiscard]] virtual std::string client_id() const = 0;

    /// 获取通信技术类型
    [[nodiscard]] virtual V2XTechnology technology() const = 0;

    /// 检查服务是否正在运行
    [[nodiscard]] virtual bool is_running() const = 0;
};

// ============================================================================
// DSRC 通信客户端
// ============================================================================

/// DSRC (Dedicated Short-Range Communications) 通信客户端
/// 基于 IEEE 802.11p 标准的 V2X 通信实现
class DSRCClient : public IV2XClient {
public:
    /// 构造函数
    /// @param device_id 设备标识
    explicit DSRCClient(const std::string& device_id = "");

    void initialize(const std::string& config) override;
    void start() override;
    void stop() override;

    size_t broadcast(const V2XMessage& message) override;
    bool unicast(const V2XMessage& message, const std::string& receiver_id) override;
    size_t geobroadcast(const V2XMessage& message, const Position& center, double radius_m) override;

    ChannelQuality evaluate_channel(const Position& target_position) override;
    std::vector<std::string> discover_topology() override;

    void on_message_received(std::function<void(const V2XMessage&)> callback) override;

    [[nodiscard]] std::string client_id() const override;
    [[nodiscard]] V2XTechnology technology() const override { return V2XTechnology::DSRC; }
    [[nodiscard]] bool is_running() const override;

    /// 设置通信频道 (IEEE 802.11p CH172/CH174/CH176/CH180/CH182)
    void set_channel(uint8_t channel);

    /// 设置发射功率 (dBm)
    void set_tx_power(double power_dbm);

    /// 获取当前信道质量统计
    [[nodiscard]] const ChannelQuality& channel_stats() const;

private:
    std::string device_id_;         ///< 设备标识
    uint8_t channel_{178};           ///< 通信频道，默认 CH178 (5.890 GHz)
    double tx_power_{20.0};         ///< 发射功率 (dBm)
    bool running_{false};           ///< 运行状态
    ChannelQuality channel_stats_;  ///< 信道质量统计
    std::function<void(const V2XMessage&)> message_callback_; ///< 消息回调

    /// 自由空间路径损耗模型 (dB)
    [[nodiscard]] double calculate_path_loss(
        const Position& sender,
        const Position& receiver,
        double frequency_hz
    ) const;

    /// 计算 SNR
    [[nodiscard]] double calculate_snr(double path_loss_db) const;

    /// 仿真丢包率
    [[nodiscard]] double estimate_packet_loss(double snr_db, double distance_m) const;
};

// ============================================================================
// 工厂函数
// ============================================================================

/// 创建 V2X 通信客户端实例
/// @param technology 通信技术类型
/// @param device_id 设备标识
/// @return V2X 客户端智能指针
std::unique_ptr<IV2XClient> create_v2x_client(
    V2XTechnology technology,
    const std::string& device_id = ""
);

} // namespace uav::edge
