#pragma once

/// @file model_runtime.h
/// @brief 模型推理运行时接口定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include "types.h"

#include <memory>
#include <vector>
#include <string>
#include <unordered_map>

namespace uav::edge {

// ============================================================================
// 模型推理运行时抽象接口
// ============================================================================

/// 模型推理运行时抽象基类
/// 提供统一的模型加载与推理接口，支持多种推理后端
class IModelRuntime {
public:
    virtual ~IModelRuntime() = default;

    /// 加载模型文件
    /// @param model_path 模型文件路径
    /// @param config 额外配置参数（可选）
    /// @return 加载是否成功
    virtual bool load_model(const std::string& model_path, const std::string& config = "") = 0;

    /// 卸载当前模型，释放资源
    virtual void unload_model() = 0;

    /// 执行模型推理
    /// @param inputs 输入张量列表
    /// @return 推理结果
    virtual InferenceResult infer(const std::vector<Tensor>& inputs) = 0;

    /// 批量推理
    /// @param batch_inputs 批量输入（外层为 batch 维度）
    /// @return 批量推理结果
    virtual std::vector<InferenceResult> infer_batch(
        const std::vector<std::vector<Tensor>>& batch_inputs
    ) = 0;

    /// 获取模型输入信息
    /// @return 输入层名称到形状的映射
    [[nodiscard]] virtual std::unordered_map<std::string, std::vector<int64_t>>
    input_info() const = 0;

    /// 获取模型输出信息
    /// @return 输出层名称到形状的映射
    [[nodiscard]] virtual std::unordered_map<std::string, std::vector<int64_t>>
    output_info() const = 0;

    /// 设置推理精度
    virtual void set_precision(InferencePrecision precision) = 0;

    /// 获取当前推理精度
    [[nodiscard]] virtual InferencePrecision precision() const = 0;

    /// 检查模型是否已加载
    [[nodiscard]] virtual bool is_model_loaded() const = 0;

    /// 获取运行时名称
    [[nodiscard]] virtual std::string runtime_name() const = 0;

    /// 获取运行时版本
    [[nodiscard]] virtual std::string runtime_version() const = 0;
};

// ============================================================================
// ONNX Runtime 推理后端
// ============================================================================

/// ONNX Runtime 推理后端
/// 使用 ONNX Runtime 进行高性能模型推理
class ONNXRuntime : public IModelRuntime {
public:
    /// 构造函数
    ONNXRuntime() = default;

    /// 析构函数
    ~ONNXRuntime() override;

    // 禁止拷贝
    ONNXRuntime(const ONNXRuntime&) = delete;
    ONNXRuntime& operator=(const ONNXRuntime&) = delete;

    // 允许移动
    ONNXRuntime(ONNXRuntime&&) noexcept;
    ONNXRuntime& operator=(ONNXRuntime&&) noexcept;

    bool load_model(const std::string& model_path, const std::string& config = "") override;
    void unload_model() override;
    InferenceResult infer(const std::vector<Tensor>& inputs) override;
    std::vector<InferenceResult> infer_batch(
        const std::vector<std::vector<Tensor>>& batch_inputs
    ) override;

    [[nodiscard]] std::unordered_map<std::string, std::vector<int64_t>>
    input_info() const override;

    [[nodiscard]] std::unordered_map<std::string, std::vector<int64_t>>
    output_info() const override;

    void set_precision(InferencePrecision precision) override;
    [[nodiscard]] InferencePrecision precision() const override;
    [[nodiscard]] bool is_model_loaded() const override;
    [[nodiscard]] std::string runtime_name() const override { return "ONNXRuntime"; }
    [[nodiscard]] std::string runtime_version() const override;

    /// 设置推理设备 ("CPU" / "CUDA" / "TensorRT")
    void set_device(const std::string& device);

    /// 设置线程数
    void set_num_threads(int num_threads);

    /// 启用/禁用图优化
    void set_graph_optimization(bool enable, int level = 99);

private:
    InferencePrecision precision_{InferencePrecision::FP32}; ///< 推理精度
    std::string device_{"CPU"};   ///< 推理设备
    int num_threads_{1};          ///< 线程数
    bool graph_optimization_{true}; ///< 图优化开关
    int optimization_level_{99};   ///< 优化等级
    bool model_loaded_{false};    ///< 模型加载状态

    // PImpl 模式隐藏 ONNX Runtime 头文件依赖
    struct Impl;
    std::unique_ptr<Impl> impl_;

    /// Tensor 数据类型字符串转 ONNX 数据类型
    [[nodiscard]] int map_dtype(const std::string& dtype) const;
};

// ============================================================================
// 工厂函数
// ============================================================================

/// 创建模型推理运行时实例
/// @param backend 后端名称 ("onnxruntime")
/// @return 推理运行时智能指针
std::unique_ptr<IModelRuntime> create_model_runtime(const std::string& backend = "onnxruntime");

} // namespace uav::edge
