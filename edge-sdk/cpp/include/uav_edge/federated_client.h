#pragma once

/// @file federated_client.h
/// @brief 联邦学习客户端接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <memory>
#include <vector>
#include <string>
#include <functional>

namespace uav::edge {

// ============================================================================
// 联邦学习客户端抽象接口
// ============================================================================

/// 联邦学习客户端抽象基类
/// 在边缘设备上执行本地模型训练并上传更新
class IFederatedClient {
public:
    virtual ~IFederatedClient() = default;

    /// 初始化联邦学习客户端
    /// @param config 配置参数（JSON 格式字符串）
    virtual void initialize(const std::string& config) = 0;

    /// 连接到联邦学习服务器
    /// @param server_url 服务器地址
    /// @return 连接是否成功
    virtual bool connect(const std::string& server_url) = 0;

    /// 断开与服务器的连接
    virtual void disconnect() = 0;

    /// 从服务器下载全局模型
    /// @return 下载是否成功
    virtual bool download_global_model() = 0;

    /// 使用本地数据执行训练
    /// @param num_epochs 本地训练轮数
    /// @param learning_rate 学习率
    /// @return 训练更新结果
    virtual FederatedUpdate local_train(
        uint32_t num_epochs = 1,
        double learning_rate = 0.001
    ) = 0;

    /// 上传本地模型更新到服务器
    /// @param update 训练更新结果
    /// @return 上传是否成功
    virtual bool upload_update(const FederatedUpdate& update) = 0;

    /// 执行一轮完整的联邦学习流程（下载 -> 训练 -> 上传）
    /// @param num_epochs 本地训练轮数
    /// @param learning_rate 学习率
    /// @return 本轮更新结果
    virtual FederatedUpdate federated_round(
        uint32_t num_epochs = 1,
        double learning_rate = 0.001
    ) = 0;

    /// 获取当前全局模型版本
    [[nodiscard]] virtual uint32_t global_model_version() const = 0;

    /// 获取客户端 ID
    [[nodiscard]] virtual std::string client_id() const = 0;

    /// 检查是否已连接
    [[nodiscard]] virtual bool is_connected() const = 0;

    /// 注册训练进度回调
    /// @param callback 进度回调函数 (epoch, loss)
    virtual void on_training_progress(
        std::function<void(uint32_t epoch, double loss)> callback
    ) = 0;
};

// ============================================================================
// 联邦学习客户端实现
// ============================================================================

/// 联邦学习客户端
/// 支持 FedAvg 和 FedProx 聚合策略的边缘端实现
class FederatedClient : public IFederatedClient {
public:
    /// 构造函数
    /// @param client_id 客户端唯一标识
    explicit FederatedClient(const std::string& client_id = "");

    void initialize(const std::string& config) override;
    bool connect(const std::string& server_url) override;
    void disconnect() override;
    bool download_global_model() override;
    FederatedUpdate local_train(uint32_t num_epochs = 1, double learning_rate = 0.001) override;
    bool upload_update(const FederatedUpdate& update) override;
    FederatedUpdate federated_round(uint32_t num_epochs = 1, double learning_rate = 0.001) override;

    [[nodiscard]] uint32_t global_model_version() const override;
    [[nodiscard]] std::string client_id() const override;
    [[nodiscard]] bool is_connected() const override;

    void on_training_progress(
        std::function<void(uint32_t epoch, double loss)> callback
    ) override;

    /// 设置聚合策略 ("fedavg" 或 "fedprox")
    void set_aggregation_strategy(const std::string& strategy);

    /// 设置 FedProx 近端项系数
    void set_proximal_mu(double mu);

    /// 设置本地数据集路径
    void set_local_dataset_path(const std::string& path);

    /// 获取训练历史记录
    [[nodiscard]] const std::vector<std::pair<uint32_t, double>>& training_history() const;

private:
    std::string client_id_;              ///< 客户端 ID
    std::string server_url_;             ///< 服务器地址
    std::string aggregation_strategy_;    ///< 聚合策略
    double proximal_mu_{0.01};           ///< FedProx 近端项系数
    std::string dataset_path_;           ///< 本地数据集路径
    bool connected_{false};               ///< 连接状态
    uint32_t model_version_{0};          ///< 全局模型版本号
    std::vector<uint8_t> global_model_;  ///< 全局模型权重
    std::vector<std::pair<uint32_t, double>> training_history_; ///< 训练历史
    std::function<void(uint32_t, double)> progress_callback_; ///< 进度回调

    /// 执行 FedAvg 本地训练
    FederatedUpdate train_fedavg(uint32_t num_epochs, double learning_rate);

    /// 执行 FedProx 本地训练
    FederatedUpdate train_fedprox(uint32_t num_epochs, double learning_rate);

    /// 模型序列化
    std::vector<uint8_t> serialize_model() const;

    /// 模型反序列化
    void deserialize_model(const std::vector<uint8_t>& data);
};

// ============================================================================
// 工厂函数
// ============================================================================

/// 创建联邦学习客户端实例
/// @param client_id 客户端 ID
/// @return 联邦学习客户端智能指针
std::unique_ptr<IFederatedClient> create_federated_client(const std::string& client_id = "");

} // namespace uav::edge
