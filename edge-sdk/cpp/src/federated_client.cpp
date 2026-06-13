/// @file federated_client.cpp
/// @brief 联邦学习客户端实现
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "uav_edge/federated_client.h"

#include <cmath>
#include <algorithm>
#include <random>
#include <chrono>
#include <sstream>

namespace uav::edge {

// ============================================================================
// FederatedClient 构造/析构
// ============================================================================

FederatedClient::FederatedClient(const std::string& client_id)
    : aggregation_strategy_("fedavg")
{
    // 自动生成客户端 ID
    if (client_id_.empty()) {
        auto now = std::chrono::steady_clock::now().time_since_epoch().count();
        client_id_ = "FL-CLIENT-" + std::to_string(now);
    } else {
        client_id_ = client_id;
    }
}

// ============================================================================
// 初始化与连接
// ============================================================================

void FederatedClient::initialize(const std::string& config) {
    // 简单配置解析
    (void)config;
}

bool FederatedClient::connect(const std::string& server_url) {
    if (connected_) return true;

    server_url_ = server_url;

    // 模拟连接（实际实现需 HTTP/gRPC 通信）
    if (server_url_.empty()) {
        server_url_ = "http://localhost:5000";
    }

    connected_ = true;
    return true;
}

void FederatedClient::disconnect() {
    connected_ = false;
    server_url_.clear();
}

bool FederatedClient::is_connected() const {
    return connected_;
}

// ============================================================================
// 模型管理
// ============================================================================

bool FederatedClient::download_global_model() {
    if (!connected_) return false;

    // 模拟下载全局模型
    // 实际实现需从服务器获取模型权重
    ++model_version_;

    // 模拟模型权重数据（128 字节占位）
    global_model_.resize(128);
    for (size_t i = 0; i < global_model_.size(); ++i) {
        global_model_[i] = static_cast<uint8_t>(i & 0xFF);
    }

    return true;
}

// ============================================================================
// 本地训练
// ============================================================================

FederatedUpdate FederatedClient::local_train(uint32_t num_epochs, double learning_rate) {
    FederatedUpdate update;

    if (aggregation_strategy_ == "fedprox") {
        update = train_fedprox(num_epochs, learning_rate);
    } else {
        update = train_fedavg(num_epochs, learning_rate);
    }

    return update;
}

/// FedAvg 本地训练
FederatedUpdate FederatedClient::train_fedavg(uint32_t num_epochs, double learning_rate) {
    FederatedUpdate update;
    update.client_id = client_id_;
    update.num_epochs = num_epochs;
    update.updated_at = std::chrono::system_clock::now();

    // 模拟本地训练过程
    std::mt19937 rng(static_cast<unsigned>(
        std::chrono::steady_clock::now().time_since_epoch().count()));
    std::uniform_real_distribution<double> loss_dist(0.1, 2.0);
    std::uniform_int_distribution<uint32_t> sample_dist(50, 500);

    double loss = loss_dist(rng);

    for (uint32_t epoch = 0; epoch < num_epochs; ++epoch) {
        // 模拟每轮训练的损失下降
        loss *= (1.0 - learning_rate * 0.5);
        loss = std::max(0.01, loss);

        // 通知进度回调
        if (progress_callback_) {
            progress_callback_(epoch + 1, loss);
        }

        // 记录训练历史
        training_history_.emplace_back(epoch + 1, loss);
    }

    update.loss = loss;
    update.num_samples = sample_dist(rng);
    update.model_weights = serialize_model();

    return update;
}

/// FedProx 本地训练（带近端项约束）
FederatedUpdate FederatedClient::train_fedprox(uint32_t num_epochs, double learning_rate) {
    FederatedUpdate update;
    update.client_id = client_id_;
    update.num_epochs = num_epochs;
    update.updated_at = std::chrono::system_clock::now();

    // FedProx 在 FedAvg 基础上增加了近端项
    // proximal_term = mu/2 * ||w - w_global||^2
    std::mt19937 rng(static_cast<unsigned>(
        std::chrono::steady_clock::now().time_since_epoch().count()));
    std::uniform_real_distribution<double> loss_dist(0.1, 2.0);
    std::uniform_int_distribution<uint32_t> sample_dist(50, 500);

    double loss = loss_dist(rng);

    for (uint32_t epoch = 0; epoch < num_epochs; ++epoch) {
        // FedProx 损失 = 原始损失 + 近端项
        double proximal_term = proximal_mu_ * 0.1; // 模拟近端项
        loss *= (1.0 - learning_rate * 0.4); // FedProx 收敛稍慢
        loss = std::max(0.01, loss + proximal_term * 0.01);

        if (progress_callback_) {
            progress_callback_(epoch + 1, loss);
        }

        training_history_.emplace_back(epoch + 1, loss);
    }

    update.loss = loss;
    update.num_samples = sample_dist(rng);
    update.model_weights = serialize_model();

    return update;
}

// ============================================================================
// 模型序列化
// ============================================================================

std::vector<uint8_t> FederatedClient::serialize_model() const {
    // 模拟模型序列化
    // 实际实现需将模型参数序列化为字节流
    std::vector<uint8_t> data;
    data.reserve(256);

    // 写入魔数和版本
    data.push_back(0xAA);
    data.push_back(0xBB);
    data.push_back(static_cast<uint8_t>(model_version_ & 0xFF));
    data.push_back(static_cast<uint8_t>((model_version_ >> 8) & 0xFF));

    // 填充模拟权重数据
    for (size_t i = 4; i < 256; ++i) {
        data.push_back(static_cast<uint8_t>(i & 0xFF));
    }

    return data;
}

void FederatedClient::deserialize_model(const std::vector<uint8_t>& data) {
    // 模拟模型反序列化
    if (data.size() < 4) return;

    // 验证魔数
    if (data[0] != 0xAA || data[1] != 0xBB) return;

    // 读取版本号
    model_version_ = data[2] | (static_cast<uint32_t>(data[3]) << 8);
    global_model_ = data;
}

// ============================================================================
// 上传与联邦轮次
// ============================================================================

bool FederatedClient::upload_update(const FederatedUpdate& update) {
    if (!connected_) return false;

    // 模拟上传模型更新到服务器
    // 实际实现需 HTTP/gRPC 通信
    (void)update;
    return true;
}

FederatedUpdate FederatedClient::federated_round(uint32_t num_epochs, double learning_rate) {
    FederatedUpdate update;

    // 1. 下载全局模型
    if (!download_global_model()) {
        update.loss = -1.0; // 标记失败
        return update;
    }

    // 2. 本地训练
    update = local_train(num_epochs, learning_rate);

    // 3. 上传更新
    upload_update(update);

    return update;
}

// ============================================================================
// 查询方法
// ============================================================================

uint32_t FederatedClient::global_model_version() const {
    return model_version_;
}

std::string FederatedClient::client_id() const {
    return client_id_;
}

const std::vector<std::pair<uint32_t, double>>&
FederatedClient::training_history() const {
    return training_history_;
}

// ============================================================================
// 配置方法
// ============================================================================

void FederatedClient::set_aggregation_strategy(const std::string& strategy) {
    if (strategy == "fedavg" || strategy == "fedprox") {
        aggregation_strategy_ = strategy;
    }
}

void FederatedClient::set_proximal_mu(double mu) {
    proximal_mu_ = (mu >= 0.0) ? mu : 0.01;
}

void FederatedClient::set_local_dataset_path(const std::string& path) {
    dataset_path_ = path;
}

void FederatedClient::on_training_progress(
    std::function<void(uint32_t epoch, double loss)> callback
) {
    progress_callback_ = std::move(callback);
}

// ============================================================================
// 工厂函数
// ============================================================================

std::unique_ptr<IFederatedClient> create_federated_client(const std::string& client_id) {
    return std::make_unique<FederatedClient>(client_id);
}

} // namespace uav::edge
