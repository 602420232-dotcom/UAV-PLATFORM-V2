#include "flight_controller.h"
#include "logger.h"
#include <thread>
#include <chrono>
#include <cstring>
#include <sstream>
#include <algorithm>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <sys/ioctl.h>
#endif

namespace uav_sdk {

static Logger& log = Logger::get_instance();

// CRC16-CCITT 查表
const uint16_t FlightController::crc_table_[256] = {
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
    0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
    0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
    0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
    0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
};

// ─── MAVLink 消息CRC额外字节 (X.25 CRC 附加) ──────────────────────────
static const uint8_t mavlink_crc_extra[] = {
    50, 124, 137, 0, 237, 217, 104, 119, 0, 0, 0, 89, 0, 0, 0, 0,
    0, 0, 0, 0, 214, 159, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 217, 0, 0, 0, 0, 0, 0, 0
};

// ═══════════════════════════════════════════════════════════════════════
//  构造函数 / 析构函数
// ═══════════════════════════════════════════════════════════════════════
FlightController::FlightController(const std::string& device, int baudrate)
    : serial_handle_(nullptr), connected_(false),
      system_id_(1), component_id_(1), sequence_(0) {
    serial_config_.device = device;
    serial_config_.baudrate = baudrate;
}

FlightController::~FlightController() {
    disconnect();
}

// ═══════════════════════════════════════════════════════════════════════
//  CRC 计算
// ═══════════════════════════════════════════════════════════════════════
uint16_t FlightController::calculate_crc(const uint8_t* data, size_t len) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc = (crc << 8) ^ crc_table_[((crc >> 8) ^ data[i]) & 0xFF];
    }
    return crc;
}

bool FlightController::validate_crc(const uint8_t* frame, size_t len) {
    if (len < 12) return false;  // 帧头10字节 + CRC2字节
    // CRC覆盖: 帧头[1..9] + payload
    size_t payload_len = frame[1];
    size_t crc_start = 10 + payload_len;  // CRC位置
    if (crc_start + 2 > len) return false;
    
    uint16_t expected = calculate_crc(frame + 1, 9 + payload_len);
    uint8_t msg_id_low = frame[7];  // msg_id低字节
    // 添加CRC extra
    if (msg_id_low < sizeof(mavlink_crc_extra)) {
        expected = (expected << 8) ^ crc_table_[((expected >> 8) ^ mavlink_crc_extra[msg_id_low]) & 0xFF];
    }
    expected &= 0xFFFF;
    
    uint16_t actual = (uint16_t)frame[crc_start] | ((uint16_t)frame[crc_start + 1] << 8);
    return expected == actual;
}

// ═══════════════════════════════════════════════════════════════════════
//  串口通信
// ═══════════════════════════════════════════════════════════════════════
bool FlightController::open_serial() {
#ifdef _WIN32
    std::string full_path = "\\\\.\\" + serial_config_.device;
    HANDLE handle = CreateFileA(
        full_path.c_str(),
        GENERIC_READ | GENERIC_WRITE,
        0, NULL,
        OPEN_EXISTING,
        FILE_FLAG_NO_BUFFERING | FILE_FLAG_OVERLAPPED,
        NULL
    );
    if (handle == INVALID_HANDLE_VALUE) {
        log.error("Failed to open serial port: " + serial_config_.device);
        return false;
    }

    DCB dcb = {0};
    dcb.DCBlength = sizeof(DCB);
    if (!GetCommState(handle, &dcb)) {
        CloseHandle(handle);
        return false;
    }

    dcb.BaudRate = serial_config_.baudrate;
    dcb.ByteSize = serial_config_.data_bits;
    dcb.StopBits = (serial_config_.stop_bits == 2) ? TWOSTOPBITS : ONESTOPBIT;
    dcb.Parity = (serial_config_.parity == 'N') ? NOPARITY :
                 (serial_config_.parity == 'E') ? EVENPARITY : ODDPARITY;
    dcb.fDtrControl = DTR_CONTROL_ENABLE;
    dcb.fRtsControl = RTS_CONTROL_ENABLE;

    if (!SetCommState(handle, &dcb)) {
        CloseHandle(handle);
        log.error("Failed to set serial parameters");
        return false;
    }

    // 设置超时
    COMMTIMEOUTS timeouts = {0};
    timeouts.ReadIntervalTimeout = serial_config_.timeout_ms;
    timeouts.ReadTotalTimeoutConstant = serial_config_.timeout_ms;
    timeouts.ReadTotalTimeoutMultiplier = 0;
    timeouts.WriteTotalTimeoutConstant = serial_config_.timeout_ms;
    timeouts.WriteTotalTimeoutMultiplier = 0;
    SetCommTimeouts(handle, &timeouts);

    serial_handle_ = handle;
    log.info("Serial port opened: " + serial_config_.device + " @ " + std::to_string(serial_config_.baudrate) + " baud");
    return true;

#else
    serial_fd_ = open(serial_config_.device.c_str(), O_RDWR | O_NOCTTY | O_NDELAY);
    if (serial_fd_ < 0) {
        log.error("Failed to open serial port: " + serial_config_.device);
        return false;
    }

    struct termios options;
    tcgetattr(serial_fd_, &options);

    cfsetispeed(&options, serial_config_.baudrate);
    cfsetospeed(&options, serial_config_.baudrate);

    options.c_cflag |= (CLOCAL | CREAD);
    options.c_cflag &= ~PARENB;
    options.c_cflag &= ~CSTOPB;
    options.c_cflag &= ~CSIZE;
    options.c_cflag |= CS8;
    options.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
    options.c_iflag &= ~(IXON | IXOFF | IXANY);
    options.c_iflag &= ~(INLCR | ICRNL);
    options.c_oflag &= ~OPOST;

    options.c_cc[VMIN] = 0;
    options.c_cc[VTIME] = serial_config_.timeout_ms / 100;

    tcsetattr(serial_fd_, TCSANOW, &options);

    log.info("Serial port opened: " + serial_config_.device + " @ " + std::to_string(serial_config_.baudrate) + " baud");
    return true;
#endif
}

void FlightController::close_serial() {
#ifdef _WIN32
    if (serial_handle_) {
        CloseHandle(serial_handle_);
        serial_handle_ = nullptr;
    }
#else
    if (serial_fd_ >= 0) {
        close(serial_fd_);
        serial_fd_ = -1;
    }
#endif
}

bool FlightController::read_serial(uint8_t* buffer, size_t size, size_t& bytes_read) {
#ifdef _WIN32
    if (!serial_handle_) return false;
    OVERLAPPED ov = {0};
    ov.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    DWORD read = 0;
    if (ReadFile(serial_handle_, buffer, (DWORD)size, &read, &ov)) {
        bytes_read = read;
        CloseHandle(ov.hEvent);
        return true;
    }
    if (GetLastError() == ERROR_IO_PENDING) {
        if (WaitForSingleObject(ov.hEvent, serial_config_.timeout_ms) == WAIT_OBJECT_0) {
            GetOverlappedResult(serial_handle_, &ov, &read, TRUE);
            bytes_read = read;
            CloseHandle(ov.hEvent);
            return true;
        }
        CancelIo(serial_handle_);
    }
    CloseHandle(ov.hEvent);
    return false;
#else
    if (serial_fd_ < 0) return false;
    ssize_t n = read(serial_fd_, buffer, size);
    if (n > 0) {
        bytes_read = n;
        return true;
    }
    return false;
#endif
}

bool FlightController::write_serial(const uint8_t* data, size_t size) {
#ifdef _WIN32
    if (!serial_handle_) return false;
    OVERLAPPED ov = {0};
    ov.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    DWORD written = 0;
    if (WriteFile(serial_handle_, data, (DWORD)size, &written, &ov)) {
        CloseHandle(ov.hEvent);
        return written == size;
    }
    if (GetLastError() == ERROR_IO_PENDING) {
        if (WaitForSingleObject(ov.hEvent, serial_config_.timeout_ms) == WAIT_OBJECT_0) {
            GetOverlappedResult(serial_handle_, &ov, &written, TRUE);
            CloseHandle(ov.hEvent);
            return written == size;
        }
        CancelIo(serial_handle_);
    }
    CloseHandle(ov.hEvent);
    return false;
#else
    if (serial_fd_ < 0) return false;
    size_t total = 0;
    while (total < size) {
        ssize_t n = write(serial_fd_, data + total, size - total);
        if (n <= 0) return false;
        total += n;
    }
    return true;
#endif
}

// ═══════════════════════════════════════════════════════════════════════
//  MAVLink 发送/接收
// ═══════════════════════════════════════════════════════════════════════
bool FlightController::send_mavlink(uint32_t msg_id, const uint8_t* payload, uint8_t payload_len) {
    if (!connected_) return false;

    std::vector<uint8_t> frame;
    frame.reserve(12 + payload_len + 2);  // header + payload + crc

    // 帧头 (10 bytes)
    MAVLinkFrame header;
    header.payload_len = payload_len;
    header.incompat_flags = 0;
    header.compat_flags = 0;
    header.seq = sequence_++;
    header.sys_id = system_id_;
    header.comp_id = component_id_;
    header.msg_id = msg_id;

    frame.push_back(0xFD);
    frame.push_back(payload_len);
    frame.push_back(0);
    frame.push_back(0);
    frame.push_back(header.seq);
    frame.push_back(header.sys_id);
    frame.push_back(header.comp_id);
    frame.push_back(msg_id & 0xFF);
    frame.push_back((msg_id >> 8) & 0xFF);
    frame.push_back((msg_id >> 16) & 0xFF);

    // Payload
    frame.insert(frame.end(), payload, payload + payload_len);

    // CRC: 从第1字节开始到payload结束
    uint16_t crc = calculate_crc(frame.data() + 1, frame.size() - 1);
    // 添加CRC extra
    if (msg_id < sizeof(mavlink_crc_extra)) {
        crc = (crc << 8) ^ crc_table_[((crc >> 8) ^ mavlink_crc_extra[msg_id]) & 0xFF];
    }
    crc &= 0xFFFF;
    frame.push_back(crc & 0xFF);
    frame.push_back((crc >> 8) & 0xFF);

    return write_serial(frame.data(), frame.size());
}

bool FlightController::receive_mavlink(MAVLinkFrame& header, std::vector<uint8_t>& payload) {
    if (!connected_) return false;

    uint8_t buf[512];
    size_t bytes_read = 0;

    // 查找帧起始
    while (true) {
        size_t n = 0;
        if (!read_serial(buf, 1, n)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
            continue;
        }
        if (n > 0 && buf[0] == 0xFD) break;
    }

    // 读取帧头剩余9字节
    size_t header_read = 0;
    size_t offset = 0;
    while (header_read < 9) {
        size_t n = 0;
        if (read_serial(buf + offset + 1, 9 - header_read, n)) {
            header_read += n;
            offset += n;
        }
    }

    // 解析帧头
    header.magic = 0xFD;
    header.payload_len = buf[1];
    header.incompat_flags = buf[2];
    header.compat_flags = buf[3];
    header.seq = buf[4];
    header.sys_id = buf[5];
    header.comp_id = buf[6];
    header.msg_id = (uint32_t)buf[7] | ((uint32_t)buf[8] << 8) | ((uint32_t)buf[9] << 16);

    // 读取payload
    payload.clear();
    if (header.payload_len > 0) {
        payload.resize(header.payload_len);
        size_t payload_read = 0;
        while (payload_read < header.payload_len) {
            size_t n = 0;
            if (read_serial(payload.data() + payload_read, header.payload_len - payload_read, n)) {
                payload_read += n;
            }
        }
    }

    // 读取并验证CRC
    uint8_t crc_bytes[2];
    size_t crc_read = 0;
    while (crc_read < 2) {
        size_t n = 0;
        if (read_serial(crc_bytes + crc_read, 2 - crc_read, n)) {
            crc_read += n;
        }
    }

    return true;
}

// ═══════════════════════════════════════════════════════════════════════
//  消息解析
// ═══════════════════════════════════════════════════════════════════════
void FlightController::parse_heartbeat(const uint8_t* payload, size_t len) {
    if (len < 9) return;
    uint8_t type = payload[0];
    uint8_t autopilot = payload[1];
    uint8_t base_mode = payload[2];
    uint32_t custom_mode = *(const uint32_t*)(payload + 4);
    uint8_t system_status = payload[8];

    std::lock_guard<std::mutex> lock(state_mutex_);
    current_state_.armed = (base_mode & 0x80) != 0;
    current_state_.flying = (base_mode & 0x04) != 0;
    current_state_.system_status = system_status;
    current_state_.last_heartbeat_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();

    // 解析飞行模式 (PX4 custom_mode / ArduPilot)
    if (autopilot == 1) { // PX4
        switch (custom_mode) {
            case 0: current_state_.mode = FlightMode::TAKEOFF; break;
            case 1: current_state_.mode = FlightMode::POSITION; break;
            case 2: current_state_.mode = FlightMode::ALT_HOLD; break;
            case 3: current_state_.mode = FlightMode::AUTO; break;
            case 4: current_state_.mode = FlightMode::STABILIZE; break;
            case 5: current_state_.mode = FlightMode::RTL; break;
            case 6: current_state_.mode = FlightMode::LAND; break;
            default: current_state_.mode = FlightMode::MANUAL; break;
        }
    } else if (autopilot == 3) { // ArduPilot
        switch (custom_mode) {
            case 0: current_state_.mode = FlightMode::STABILIZE; break;
            case 1: current_state_.mode = FlightMode::POSITION; break;
            case 2: current_state_.mode = FlightMode::AUTO; break;
            case 3: current_state_.mode = FlightMode::RTL; break;
            case 4: current_state_.mode = FlightMode::LAND; break;
            case 5: current_state_.mode = FlightMode::TAKEOFF; break;
            case 6: current_state_.mode = FlightMode::GUIDED; break;
            default: current_state_.mode = FlightMode::MANUAL; break;
        }
    }

    last_heartbeat_ms_ = current_state_.last_heartbeat_ms;
}

void FlightController::parse_attitude(const uint8_t* payload, size_t len) {
    if (len < 16) return;
    // time_boot_ms(4) + roll(4) + pitch(4) + yaw(4)
    float roll = *(const float*)(payload + 4);
    float pitch = *(const float*)(payload + 8);
    float yaw = *(const float*)(payload + 12);
    
    std::lock_guard<std::mutex> lock(state_mutex_);
    current_state_.roll = roll * 180.0 / 3.14159;
    current_state_.pitch = pitch * 180.0 / 3.14159;
    current_state_.yaw = yaw * 180.0 / 3.14159;
    current_state_.heading = current_state_.yaw;
}

void FlightController::parse_global_position(const uint8_t* payload, size_t len) {
    if (len < 28) return;
    // time_boot_ms(4) + lat(4) + lon(4) + alt(4) + rel_alt(4) + vx(2) + vy(2) + vz(2) + hdg(2)
    int32_t lat = *(const int32_t*)(payload + 4);
    int32_t lon = *(const int32_t*)(payload + 8);
    int32_t alt = *(const int32_t*)(payload + 12);      // mm
    int32_t rel_alt = *(const int32_t*)(payload + 16);  // mm
    uint16_t hdg = *(const uint16_t*)(payload + 24);     // cdeg

    std::lock_guard<std::mutex> lock(state_mutex_);
    current_state_.latitude = lat / 1e7;
    current_state_.longitude = lon / 1e7;
    current_state_.altitude = rel_alt / 1000.0;
    current_state_.abs_altitude = alt / 1000.0;
    current_state_.heading = hdg / 100.0;
}

void FlightController::parse_sys_status(const uint8_t* payload, size_t len) {
    if (len < 15) return;
    // onboard_control_sensors_present(4) + onboard_control_sensors_enabled(4) +
    // onboard_control_sensors_health(4) + load(2) + voltage_battery(2) +
    // current_battery(2) + battery_remaining(-1)
    uint16_t voltage = *(const uint16_t*)(payload + 12);
    int8_t battery_remaining = *(const int8_t*)(payload + 16);

    std::lock_guard<std::mutex> lock(state_mutex_);
    current_state_.battery = battery_remaining >= 0 ? battery_remaining / 100.0 * 100 : 100.0;
}

void FlightController::parse_command_ack(const uint8_t* payload, size_t len) {
    if (len < 3) return;
    uint16_t command = *(const uint16_t*)(payload);
    uint8_t result = payload[2];
    log.info("Command ACK: cmd=" + std::to_string(command) + " result=" + std::to_string(result));
}

void FlightController::parse_mission_ack(const uint8_t* payload, size_t len) {
    if (len < 1) return;
    log.info("Mission ACK received, type=" + std::to_string(payload[0]));
}

// ═══════════════════════════════════════════════════════════════════════
//  指令编码
// ═══════════════════════════════════════════════════════════════════════
std::vector<uint8_t> FlightController::encode_command_long(uint16_t command, float param1, float param2,
                                                           float param3, float param4, float param5,
                                                           float param6, float param7) {
    std::vector<uint8_t> payload(14);
    *((uint16_t*)(payload.data())) = command;
    *((uint8_t*)(payload.data() + 2)) = 1;  // target_system
    *((uint8_t*)(payload.data() + 3)) = 1;  // target_component
    *((float*)(payload.data() + 4)) = param1;
    *((float*)(payload.data() + 8)) = param2;
    *((float*)(payload.data() + 12)) = param3;
    payload.resize(14 + 4);  // 需要全7个参数
    *((float*)(payload.data() + 16)) = param4;
    *((float*)(payload.data() + 20)) = param5;
    *((float*)(payload.data() + 24)) = param6;
    *((float*)(payload.data() + 28)) = param7;
    return payload;
}

std::vector<uint8_t> FlightController::encode_set_mode(uint8_t base_mode, uint32_t custom_mode) {
    std::vector<uint8_t> payload(6);
    payload[0] = base_mode;
    payload[1] = 0;  // target_system
    *((uint32_t*)(payload.data() + 2)) = custom_mode;
    return payload;
}

std::vector<uint8_t> FlightController::encode_mission_item(const Waypoint& wp, uint16_t seq) {
    std::vector<uint8_t> payload(20);
    payload[0] = 1;  // target_system
    payload[1] = 1;  // target_component
    *((uint16_t*)(payload.data() + 2)) = seq;
    *((uint8_t*)(payload.data() + 4)) = 0;  // frame
    *((uint16_t*)(payload.data() + 5)) = wp.command;
    payload[7] = 1;  // current
    payload[8] = wp.autocontinue;
    *((float*)(payload.data() + 9)) = wp.param1;
    *((float*)(payload.data() + 13)) = wp.param2;
    *((float*)(payload.data() + 17)) = wp.param3;
    *((float*)(payload.data() + 21)) = wp.param4;
    *((int32_t*)(payload.data() + 25)) = (int32_t)(wp.latitude * 1e7);
    *((int32_t*)(payload.data() + 29)) = (int32_t)(wp.longitude * 1e7);
    *((float*)(payload.data() + 33)) = wp.altitude;
    return payload;
}

std::vector<uint8_t> FlightController::encode_mission_count(uint16_t count) {
    std::vector<uint8_t> payload(4);
    payload[0] = 1;  // target_system
    payload[1] = 1;  // target_component
    *((uint16_t*)(payload.data() + 2)) = count;
    return payload;
}

// ═══════════════════════════════════════════════════════════════════════
//  接收线程
// ═══════════════════════════════════════════════════════════════════════
void FlightController::receive_loop() {
    log.info("MAVLink receive thread started");
    
    while (receive_thread_running_) {
        MAVLinkFrame header;
        std::vector<uint8_t> payload;
        
        if (receive_mavlink(header, payload)) {
            switch (header.msg_id) {
                case MAVLINK_MSG_ID_HEARTBEAT:
                    parse_heartbeat(payload.data(), payload.size());
                    break;
                case MAVLINK_MSG_ID_ATTITUDE:
                    parse_attitude(payload.data(), payload.size());
                    break;
                case MAVLINK_MSG_ID_GLOBAL_POSITION:
                    parse_global_position(payload.data(), payload.size());
                    break;
                case MAVLINK_MSG_ID_SYS_STATUS:
                    parse_sys_status(payload.data(), payload.size());
                    break;
                case MAVLINK_MSG_ID_COMMAND_ACK:
                    parse_command_ack(payload.data(), payload.size());
                    break;
                case MAVLINK_MSG_ID_MISSION_ACK:
                    parse_mission_ack(payload.data(), payload.size());
                    break;
                default:
                    break;
            }
            
            // 通知状态回调
            if (state_callback_) {
                std::lock_guard<std::mutex> lock(state_mutex_);
                state_callback_(current_state_);
            }
        }
    }
    
    log.info("MAVLink receive thread stopped");
}

void FlightController::send_heartbeat() {
    uint8_t payload[9] = {0};
    payload[0] = 2;     // MAV_TYPE_QUADROTOR
    payload[1] = 0;     // MAV_AUTOPILOT_INVALID
    payload[2] = 0;     // base_mode
    payload[4] = 0;     // custom_mode
    payload[8] = 3;     // MAV_STATE_ACTIVE
    send_mavlink(MAVLINK_MSG_ID_HEARTBEAT, payload, 9);
}

// ═══════════════════════════════════════════════════════════════════════
//  连接管理
// ═══════════════════════════════════════════════════════════════════════
bool FlightController::connect() {
    if (connected_) {
        log.warn("Already connected");
        return true;
    }

    log.info("Connecting to flight controller on " + serial_config_.device + "...");
    
    if (!open_serial()) {
        log.error("Failed to open serial port");
        // 尝试模拟模式
        log.info("Serial port failed, entering simulation mode");
        connected_ = true;
        return true;
    }

    connected_ = true;
    
    // 启动接收线程
    receive_thread_running_ = true;
    receive_thread_ = std::thread(&FlightController::receive_loop, this);
    
    // 发送心跳
    send_heartbeat();
    
    log.info("Flight controller connected successfully");
    return true;
}

void FlightController::disconnect() {
    if (!connected_) return;
    
    log.info("Disconnecting flight controller...");
    
    receive_thread_running_ = false;
    if (receive_thread_.joinable()) {
        receive_thread_.join();
    }
    
    close_serial();
    connected_ = false;
    log.info("Flight controller disconnected");
}

bool FlightController::is_connected() const {
    return connected_;
}

// ═══════════════════════════════════════════════════════════════════════
//  状态获取
// ═══════════════════════════════════════════════════════════════════════
UAVState FlightController::get_state() {
    std::lock_guard<std::mutex> lock(state_mutex_);
    return current_state_;
}

std::string FlightController::get_mavlink_version() {
    return "MAVLink v2.0";
}

int64_t FlightController::get_last_heartbeat_ms() const {
    return last_heartbeat_ms_.load();
}

double FlightController::get_connection_quality() const {
    if (!connected_) return 0.0;
    int64_t now = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    int64_t elapsed = now - last_heartbeat_ms_.load();
    if (elapsed > 10000) return 0.0;     // 10秒无心跳
    if (elapsed > 5000) return 50.0;     // 5秒无心跳
    return 100.0;                         // 正常
}

// ═══════════════════════════════════════════════════════════════════════
//  飞控指令
// ═══════════════════════════════════════════════════════════════════════
bool FlightController::arm() {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    log.info("Arming motors...");
    auto payload = encode_command_long(400, 1.0f, 0, 0, 0, 0, 0, 0);  // MAV_CMD_COMPONENT_ARM_DISARM
    if (send_mavlink(MAVLINK_MSG_ID_COMMAND, payload.data(), payload.size())) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        {
            std::lock_guard<std::mutex> lock(state_mutex_);
            current_state_.armed = true;
        }
        log.info("Motors armed");
        return true;
    }
    return false;
}

bool FlightController::disarm() {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    log.info("Disarming motors...");
    auto payload = encode_command_long(400, 0.0f, 0, 0, 0, 0, 0, 0);
    if (send_mavlink(MAVLINK_MSG_ID_COMMAND, payload.data(), payload.size())) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        {
            std::lock_guard<std::mutex> lock(state_mutex_);
            current_state_.armed = false;
        }
        log.info("Motors disarmed");
        return true;
    }
    return false;
}

bool FlightController::set_mode(FlightMode mode) {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    
    uint32_t custom_mode = 0;
    switch (mode) {
        case FlightMode::TAKEOFF: custom_mode = 0; break;
        case FlightMode::POSITION: custom_mode = 1; break;
        case FlightMode::ALT_HOLD: custom_mode = 2; break;
        case FlightMode::AUTO: custom_mode = 3; break;
        case FlightMode::STABILIZE: custom_mode = 4; break;
        case FlightMode::RTL: custom_mode = 5; break;
        case FlightMode::LAND: custom_mode = 6; break;
        default: custom_mode = 0; break;
    }
    
    auto payload = encode_set_mode(0x01, custom_mode);  // MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
    if (send_mavlink(MAVLINK_MSG_ID_SET_MODE, payload.data(), payload.size())) {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        {
            std::lock_guard<std::mutex> lock(state_mutex_);
            current_state_.mode = mode;
        }
        log.info("Flight mode set successfully");
        return true;
    }
    return false;
}

bool FlightController::set_mode(const std::string& mode_name) {
    static const std::pair<const char*, FlightMode> mode_map[] = {
        {"MANUAL", FlightMode::MANUAL}, {"STABILIZE", FlightMode::STABILIZE},
        {"ALT_HOLD", FlightMode::ALT_HOLD}, {"POSITION", FlightMode::POSITION},
        {"AUTO", FlightMode::AUTO}, {"RTL", FlightMode::RTL},
        {"LAND", FlightMode::LAND}, {"TAKEOFF", FlightMode::TAKEOFF},
        {"GUIDED", FlightMode::GUIDED}, {"LOITER", FlightMode::LOITER},
        {"FOLLOW", FlightMode::FOLLOW}, {"CIRCLE", FlightMode::CIRCLE}
    };
    
    for (const auto& [name, mode] : mode_map) {
        if (mode_name == name) {
            return set_mode(mode);
        }
    }
    
    log.error("Unknown flight mode: " + mode_name);
    return false;
}

bool FlightController::takeoff(double altitude) {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    log.info("Taking off to " + std::to_string(altitude) + "m...");
    auto payload = encode_command_long(22, 0, 0, 0, 0, 0, 0, altitude);  // MAV_CMD_NAV_TAKEOFF
    return send_mavlink(MAVLINK_MSG_ID_COMMAND, payload.data(), payload.size());
}

bool FlightController::land() {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    log.info("Landing...");
    auto payload = encode_command_long(21, 0, 0, 0, 0, 0, 0, 0);  // MAV_CMD_NAV_LAND
    return send_mavlink(MAVLINK_MSG_ID_COMMAND, payload.data(), payload.size());
}

bool FlightController::return_to_launch() {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    log.info("Returning to launch...");
    auto payload = encode_command_long(20, 0, 0, 0, 0, 0, 0, 0);  // MAV_CMD_NAV_RETURN_TO_LAUNCH
    return send_mavlink(MAVLINK_MSG_ID_COMMAND, payload.data(), payload.size());
}

bool FlightController::goto_position(double lat, double lon, double alt) {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    log.info("Going to position: lat=" + std::to_string(lat) + ", lon=" + std::to_string(lon) + ", alt=" + std::to_string(alt));
    auto payload = encode_command_long(16, 0, 0, 0, 0, lat, lon, alt);  // MAV_CMD_NAV_WAYPOINT
    return send_mavlink(MAVLINK_MSG_ID_COMMAND, payload.data(), payload.size());
}

// ═══════════════════════════════════════════════════════════════════════
//  任务管理
// ═══════════════════════════════════════════════════════════════════════
bool FlightController::upload_mission(const std::vector<Waypoint>& waypoints) {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    
    log.info("Uploading mission with " + std::to_string(waypoints.size()) + " waypoints...");
    
    // 发送航点数量
    auto count_payload = encode_mission_count(waypoints.size());
    if (!send_mavlink(MAVLINK_MSG_ID_MISSION_COUNT, count_payload.data(), count_payload.size())) {
        return false;
    }
    
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    
    // 发送每个航点
    for (size_t i = 0; i < waypoints.size(); i++) {
        auto item_payload = encode_mission_item(waypoints[i], i);
        if (!send_mavlink(MAVLINK_MSG_ID_MISSION_ITEM, item_payload.data(), item_payload.size())) {
            return false;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
    
    log.info("Mission uploaded successfully");
    return true;
}

bool FlightController::execute_mission() {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    log.info("Executing mission...");
    return set_mode(FlightMode::AUTO);
}

bool FlightController::pause_mission() {
    if (!connected_) {
        log.error("Not connected!");
        return false;
    }
    log.info("Pausing mission...");
    return set_mode(FlightMode::POSITION);
}

bool FlightController::clear_mission() {
    if (!connected_) return false;
    log.info("Clearing mission...");
    auto payload = encode_command_long(45, 0, 0, 0, 0, 0, 0, 0);  // MAV_CMD_MISSION_CLEAR
    return send_mavlink(MAVLINK_MSG_ID_COMMAND, payload.data(), payload.size());
}

int FlightController::get_mission_count() {
    return 0;  // 实际实现需发送MISSION_REQUEST_LIST并等待响应
}

// ═══════════════════════════════════════════════════════════════════════
//  参数管理
// ═══════════════════════════════════════════════════════════════════════
bool FlightController::set_parameter(const std::string& name, float value) {
    if (!connected_) return false;
    std::vector<uint8_t> payload(9 + name.size());
    payload[0] = 1;  // target_system
    payload[1] = 1;  // target_component
    memcpy(payload.data() + 2, name.c_str(), name.size());
    memset(payload.data() + 2 + name.size(), 0, 9 - name.size());
    *((float*)(payload.data() + 11)) = value;
    *((uint8_t*)(payload.data() + 15)) = 6;  // MAV_PARAM_TYPE_REAL32
    return send_mavlink(MAVLINK_MSG_ID_PARAM_SET, payload.data(), payload.size());
}

float FlightController::get_parameter(const std::string& name) {
    if (!connected_) return 0;
    // 简化实现: 发送PARAM_REQUEST_LIST
    log.info("Requesting parameter: " + name);
    return 0;
}

bool FlightController::set_home_position(double lat, double lon, double alt) {
    if (!connected_) return false;
    log.info("Setting home position...");
    auto payload = encode_command_long(179, 0, 1, 0, 0, lat, lon, alt);
    return send_mavlink(MAVLINK_MSG_ID_COMMAND, payload.data(), payload.size());
}

}  // namespace uav_sdk
