#ifndef FLIGHT_CONTROLLER_H
#define FLIGHT_CONTROLLER_H

#include <vector>
#include <string>
#include <chrono>
#include <functional>
#include <mutex>
#include <atomic>
#include <thread>
#include <cstdint>

namespace uav_sdk {

/**
 * @brief 飞行模式 (MAVLink STANDARD_MODE)
 */
enum class FlightMode : uint8_t {
    MANUAL = 0,
    STABILIZE = 1,
    ALT_HOLD = 2,
    POSITION = 3,
    AUTO = 4,
    RTL = 5,
    LAND = 6,
    TAKEOFF = 7,
    GUIDED = 8,
    LOITER = 9,
    FOLLOW = 10,
    CIRCLE = 11
};

/**
 * @brief MAVLink 消息ID
 */
enum MAVLinkMessageID : uint32_t {
    MAVLINK_MSG_ID_HEARTBEAT = 0,
    MAVLINK_MSG_ID_SYS_STATUS = 1,
    MAVLINK_MSG_ID_COMMAND = 76,
    MAVLINK_MSG_ID_COMMAND_ACK = 77,
    MAVLINK_MSG_ID_ATTITUDE = 30,
    MAVLINK_MSG_ID_GLOBAL_POSITION = 33,
    MAVLINK_MSG_ID_MISSION_COUNT = 44,
    MAVLINK_MSG_ID_MISSION_ITEM = 39,
    MAVLINK_MSG_ID_MISSION_ACK = 47,
    MAVLINK_MSG_ID_SET_MODE = 11,
    MAVLINK_MSG_ID_PARAM_SET = 23,
    MAVLINK_MSG_ID_PARAM_VALUE = 22
};

/**
 * @brief MAVLink v2 帧头
 * @details 标准 MAVLink v2 帧结构: 0xFD len incompat compat seq sys comp msgid[3] payload crc[2]
 */
#pragma pack(push, 1)
struct MAVLinkFrame {
    uint8_t magic = 0xFD;          // MAVLink v2 起始字节
    uint8_t payload_len;           // 载荷长度
    uint8_t incompat_flags = 0;    // 不兼容标志
    uint8_t compat_flags = 0;      // 兼容标志
    uint8_t seq;                   // 序列号
    uint8_t sys_id;                // 系统ID
    uint8_t comp_id;               // 组件ID
    uint32_t msg_id : 24;          // 消息ID (3字节)
    // payload follows
    // CRC follows (2 bytes)
};
#pragma pack(pop)

/**
 * @brief 无人机状态
 */
struct UAVState {
    double latitude = 0.0;
    double longitude = 0.0;
    double altitude = 0.0;
    double abs_altitude = 0.0;
    double heading = 0.0;
    double speed = 0.0;
    double battery = 0.0;
    FlightMode mode = FlightMode::MANUAL;
    bool armed = false;
    bool flying = false;
    uint8_t system_status = 0;
    double roll = 0.0, pitch = 0.0, yaw = 0.0;
    int64_t last_heartbeat_ms = 0;
};

/**
 * @brief 航点
 */
struct Waypoint {
    double latitude;
    double longitude;
    double altitude;
    double speed = 10.0;
    bool action = true;          // true=继续, false=悬停
    uint16_t command = 16;       // MAV_CMD_NAV_WAYPOINT
    uint8_t autocontinue = 1;
    float param1 = 0;            // 停留时间(s)
    float param2 = 0;            // 接受半径(m)
    float param3 = 0;            // 过点半径(m)
    float param4 = 0;            // 偏航角(度)
};

/**
 * @brief 串口配置
 */
struct SerialConfig {
    std::string device;
    int baudrate;
    int data_bits = 8;
    int stop_bits = 1;
    char parity = 'N';
    int timeout_ms = 100;
    int heartbeat_interval_ms = 1000;

    SerialConfig() : device("COM3"), baudrate(57600) {}
    SerialConfig(const std::string& dev, int baud)
        : device(dev), baudrate(baud) {}
};

/**
 * @brief PX4/ArduPilot 飞控通信接口
 * 
 * 基于 MAVLink v2 协议的完整飞控通信实现
 * 支持 PX4 和 ArduPilot（两者使用同一 MAVLink 协议）
 */
class FlightController {
public:
    FlightController(const std::string& device = "COM3", int baudrate = 57600);
    ~FlightController();

    // ─── 连接管理 ────────────────────────────────────────────────────
    bool connect();
    void disconnect();
    bool is_connected() const;

    // ─── 状态获取 ────────────────────────────────────────────────────
    UAVState get_state();
    std::string get_mavlink_version();

    // ─── 飞控指令 ────────────────────────────────────────────────────
    bool arm();
    bool disarm();
    bool set_mode(FlightMode mode);
    bool set_mode(const std::string& mode_name);
    bool takeoff(double altitude);
    bool land();
    bool return_to_launch();
    bool goto_position(double lat, double lon, double alt);

    // ─── 任务管理 ────────────────────────────────────────────────────
    bool upload_mission(const std::vector<Waypoint>& waypoints);
    bool execute_mission();
    bool pause_mission();
    bool clear_mission();
    int get_mission_count();

    // ─── 参数管理 ────────────────────────────────────────────────────
    bool set_parameter(const std::string& name, float value);
    float get_parameter(const std::string& name);
    bool set_home_position(double lat, double lon, double alt);

    // ─── 回调 ────────────────────────────────────────────────────────
    using StateCallback = std::function<void(const UAVState&)>;
    void set_state_callback(StateCallback cb) { state_callback_ = cb; }

    // ─── 遥测 ────────────────────────────────────────────────────────
    int64_t get_last_heartbeat_ms() const;
    double get_connection_quality() const;

private:
    // MAVLink 协议
    uint8_t calculate_crc(const uint8_t* data, size_t len);
    bool validate_crc(const uint8_t* frame, size_t len);
    bool send_mavlink(uint32_t msg_id, const uint8_t* payload, uint8_t payload_len);
    bool receive_mavlink(MAVLinkFrame& header, std::vector<uint8_t>& payload);
    void parse_heartbeat(const uint8_t* payload, size_t len);
    void parse_attitude(const uint8_t* payload, size_t len);
    void parse_global_position(const uint8_t* payload, size_t len);
    void parse_sys_status(const uint8_t* payload, size_t len);
    void parse_command_ack(const uint8_t* payload, size_t len);
    void parse_mission_ack(const uint8_t* payload, size_t len);

    // 指令编码
    std::vector<uint8_t> encode_command_long(uint16_t command, float param1, float param2,
                                              float param3, float param4, float param5,
                                              float param6, float param7);
    std::vector<uint8_t> encode_set_mode(uint8_t base_mode, uint32_t custom_mode);
    std::vector<uint8_t> encode_mission_item(const Waypoint& wp, uint16_t seq);
    std::vector<uint8_t> encode_mission_count(uint16_t count);

    // 串口通信
    bool open_serial();
    void close_serial();
    bool read_serial(uint8_t* buffer, size_t size, size_t& bytes_read);
    bool write_serial(const uint8_t* data, size_t size);
    
    // 接收线程
    void receive_loop();
    void send_heartbeat();

    // 硬件句柄
#ifdef _WIN32
    void* serial_handle_;  // HANDLE
#else
    int serial_fd_;
#endif
    bool connected_;
    
    // 飞控状态
    UAVState current_state_;
    mutable std::mutex state_mutex_;
    std::atomic<int64_t> last_heartbeat_ms_{0};
    
    // 配置
    SerialConfig serial_config_;
    uint8_t system_id_;
    uint8_t component_id_;
    uint8_t sequence_{0};
    
    // 接收线程
    std::thread receive_thread_;
    std::atomic<bool> receive_thread_running_{false};
    
    // 回调
    StateCallback state_callback_;
    
    // CRC16-CCITT 表
    static const uint16_t crc_table_[256];
};

}  // namespace uav_sdk

#endif  // FLIGHT_CONTROLLER_H
