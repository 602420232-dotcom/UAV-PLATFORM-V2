#pragma once

/// @file types.h
/// @brief UAV 边缘计算 SDK 基础类型定义
/// @author UAV Platform Team
/// @version 1.0.0
/// @date 2026-06-14

#include <cstdint>
#include <cmath>
#include <string>
#include <vector>
#include <optional>
#include <variant>
#include <chrono>

namespace uav::edge {

// ============================================================================
// 枚举类型
// ============================================================================

/// 风险等级枚举
enum class RiskLevel : uint8_t {
    Low = 0,      ///< 低风险 - 可正常飞行
    Medium = 1,   ///< 中风险 - 需要关注
    High = 2,     ///< 高风险 - 需要调整航线
    Critical = 3, ///< 极高风险 - 建议返航
};

/// 飞行状态枚举
enum class FlightState : uint8_t {
    Idle = 0,        ///< 空闲
    Takeoff = 1,     ///< 起飞中
    Cruising = 2,    ///< 巡航中
    Hovering = 3,    ///< 悬停
    Landing = 4,     ///< 降落中
    Emergency = 5,  ///< 紧急状态
    Returning = 6,  ///< 返航中
};

/// V2X 通信模式枚举
enum class V2XMode : uint8_t {
    Broadcast = 0,       ///< 广播模式
    Unicast = 1,         ///< 单播模式
    Geobroadcast = 2,    ///< 地理广播
    Topology = 3,        ///< 拓扑发现
};

/// V2X 通信技术枚举
enum class V2XTechnology : uint8_t {
    DSRC = 0,   ///< DSRC (IEEE 802.11p)
    CV2X = 1,   ///< C-V2X (3GPP LTE-V2X / NR-V2X)
};

/// 模型推理精度枚举
enum class InferencePrecision : uint8_t {
    FP32 = 0,  ///< 32位浮点
    FP16 = 1,  ///< 16位浮点
    INT8 = 2,  ///< 8位整数
};

// ============================================================================
// 基础数据结构
// ============================================================================

/// 三维位置坐标（WGS84 或局部坐标系）
struct Position {
    double x{0.0}; ///< 经度 / 东向坐标 (m)
    double y{0.0}; ///< 纬度 / 北向坐标 (m)
    double z{0.0}; ///< 高度 (m, WGS84 椭球高)

    /// 计算到目标点的欧氏距离
    [[nodiscard]] double distance_to(const Position& other) const noexcept {
        double dx = x - other.x;
        double dy = y - other.y;
        double dz = z - other.z;
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }
};

/// 速度向量
struct Velocity {
    double vx{0.0}; ///< 东向速度 (m/s)
    double vy{0.0}; ///< 北向速度 (m/s)
    double vz{0.0}; ///< 垂直速度 (m/s)

    /// 计算速率标量
    [[nodiscard]] double speed() const noexcept {
        return std::sqrt(vx * vx + vy * vy + vz * vz);
    }
};

/// 四元数姿态表示
struct Quaternion {
    double w{1.0}; ///< 实部
    double x{0.0}; ///< i 分量
    double y{0.0}; ///< j 分量
    double z{0.0}; ///< k 分量
};

/// 障碍物信息
struct Obstacle {
    Position position;             ///< 障碍物中心位置
    double radius{0.0};           ///< 障碍物等效半径 (m)
    double height{0.0};           ///< 障碍物高度 (m)
    std::string type;              ///< 障碍物类型（建筑、树木、线缆等）
    std::optional<double> dynamic_speed; ///< 动态障碍物移动速度 (m/s)，静态障碍物为 nullopt
    std::chrono::system_clock::time_point detected_at; ///< 检测时间戳
};

/// 航路点
struct Waypoint {
    Position position;             ///< 航路点位置
    std::optional<double> speed_limit; ///< 速度限制 (m/s)
    std::optional<double> heading;     ///< 期望航向角 (rad)
    std::optional<double> hold_time;   ///< 悬停时间 (s)
};

/// 飞行计划
struct FlightPlan {
    std::vector<Waypoint> waypoints;    ///< 航路点序列
    double max_altitude{120.0};        ///< 最大飞行高度 (m)
    double min_altitude{10.0};         ///< 最小飞行高度 (m)
    std::chrono::system_clock::time_point depart_time; ///< 起飞时间
    std::optional<std::chrono::system_clock::time_point> deadline; ///< 截止到达时间
    std::string uav_id;                ///< 无人机 ID
};

/// 天气数据
struct WeatherData {
    double temperature{25.0};         ///< 温度 (°C)
    double humidity{50.0};             ///< 相对湿度 (%)
    double wind_speed{0.0};            ///< 风速 (m/s)
    double wind_direction{0.0};        ///< 风向 (rad, 正北为 0)
    double visibility{10000.0};        ///< 能见度 (m)
    double precipitation{0.0};         ///< 降水量 (mm/h)
    std::optional<double> turbulence;  ///< 湍流强度指数 (0-1)
    std::chrono::system_clock::time_point observed_at; ///< 观测时间戳

    /// 判断当前天气是否适合飞行
    [[nodiscard]] bool is_flyable() const noexcept {
        return wind_speed < 15.0 && visibility > 2000.0 && precipitation < 5.0;
    }
};

/// V2X 消息结构
struct V2XMessage {
    std::string sender_id;            ///< 发送方 ID
    Position sender_position;         ///< 发送方位置
    std::vector<uint8_t> payload;     ///< 消息载荷
    uint32_t sequence{0};             ///< 序列号
    std::chrono::system_clock::time_point timestamp; ///< 发送时间戳
    V2XMode mode{V2XMode::Broadcast}; ///< 通信模式
};

/// V2X 信道质量信息
struct ChannelQuality {
    double snr{0.0};                  ///< 信噪比 (dB)
    double packet_loss_rate{0.0};     ///< 丢包率 (0-1)
    double latency_ms{0.0};          ///< 往返延迟 (ms)
    double bandwidth_mbps{0.0};      ///< 可用带宽 (Mbps)
    double ber{0.0};                 ///< 误比特率 (Bit Error Rate)
};

/// 模型推理输入张量
struct Tensor {
    std::vector<int64_t> shape;       ///< 张量形状
    std::vector<uint8_t> data;        ///< 原始数据
    std::string dtype;                ///< 数据类型 ("float32", "int8" 等)
};

/// 模型推理结果
struct InferenceResult {
    std::vector<Tensor> outputs;      ///< 输出张量列表
    double inference_time_ms{0.0};    ///< 推理耗时 (ms)
    std::optional<std::string> error; ///< 错误信息（推理失败时）
};

/// 联邦学习客户端更新
struct FederatedUpdate {
    std::string client_id;            ///< 客户端 ID
    std::vector<uint8_t> model_weights; ///< 模型权重更新
    uint32_t num_samples{0};         ///< 训练样本数
    uint32_t num_epochs{1};           ///< 训练轮数
    double loss{0.0};                ///< 最终损失值
    std::chrono::system_clock::time_point updated_at; ///< 更新时间戳
};

/// 风险评估结果
struct RiskAssessment {
    RiskLevel level{RiskLevel::Low};  ///< 综合风险等级
    double score{0.0};                ///< 风险评分 (0-1)
    std::vector<std::string> factors; ///< 风险因素列表
    std::string description;          ///< 风险描述
    std::optional<FlightPlan> suggested_plan; ///< 建议的替代飞行计划
};

} // namespace uav::edge
