#pragma once

/// @file uav_edge.h
/// @brief UAV 边缘计算 SDK 主头文件
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14
///
/// 本头文件聚合所有子模块，用户只需 #include <uav_edge/uav_edge.h>
/// 即可使用 SDK 的全部功能。

// 基础类型定义
#include "types.h"

// 路径规划接口
#include "path_planner.h"

// 风险评估接口
#include "risk_assessor.h"

// V2X 通信客户端接口
#include "v2x_client.h"

// 联邦学习客户端接口
#include "federated_client.h"

// 模型推理运行时接口
#include "model_runtime.h"

// 配置管理
#include "config.h"

namespace uav::edge {

// ============================================================================
// SDK 版本信息
// ============================================================================

/// 获取 SDK 版本字符串
[[nodiscard]] constexpr const char* version() noexcept {
    return "1.0.0";
}

/// 获取 SDK 版本主号
[[nodiscard]] constexpr int version_major() noexcept {
    return 1;
}

/// 获取 SDK 版本次号
[[nodiscard]] constexpr int version_minor() noexcept {
    return 0;
}

/// 获取 SDK 版本补丁号
[[nodiscard]] constexpr int version_patch() noexcept {
    return 0;
}

// ============================================================================
// SDK 初始化与清理
// ============================================================================

/// 全局 SDK 初始化
/// 加载默认配置并初始化各子系统
/// @param config_path 配置文件路径（可选，空字符串使用默认配置）
/// @return 初始化是否成功
bool initialize(const std::string& config_path = "");

/// 全局 SDK 清理
/// 释放所有资源
void shutdown();

/// 检查 SDK 是否已初始化
[[nodiscard]] bool is_initialized();

} // namespace uav::edge
