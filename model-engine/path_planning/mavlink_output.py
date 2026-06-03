"""
MAVLink 输出 — PX4/ArduPilot 原生支持

将 GPR 风险规划路径转为:
  1. .plan 任务文件 (QGroundControl 可导入)
  2. 实时 MAVLink 指令 (串口/UDP)

不需要 pymavlink 库，无额外依赖。
"""
import json
import struct
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import IntEnum
from pathlib import Path
from datetime import datetime


# ── 坐标系统 ────────────────────────────────────

@dataclass
class GeoConfig:
    """地理坐标配置 (成都平原)"""
    ref_lat: float = 30.67         # 成都市中心纬度
    ref_lon: float = 104.07        # 经度
    ref_alt: float = 500.0         # 基准海拔 m

    # 成都平原投影参数 (近似)
    lat_per_km: float = 0.0090     # 1° ≈ 111km → 1km ≈ 0.009°
    lon_per_km: float = 0.0097     # cos(30.67°) ≈ 0.86 → 1km ≈ 0.0097°


class MAV_FRAME(IntEnum):
    """MAVLink 坐标帧"""
    GLOBAL = 0
    LOCAL_NED = 1
    GLOBAL_RELATIVE_ALT = 3
    GLOBAL_INT = 4
    MISSION = 6


class MAV_CMD(IntEnum):
    """MAVLink 命令"""
    NAV_WAYPOINT = 16
    NAV_LOITER_UNLIM = 17
    NAV_LOITER_TIME = 18
    NAV_RETURN_TO_LAUNCH = 20
    NAV_LAND = 21
    NAV_SPLINE_WAYPOINT = 82
    DO_CHANGE_SPEED = 178
    DO_SET_SERVO = 183
    DO_SET_RELAY = 181
    CONDITION_DELAY = 112


class MAV_MISSION_TYPE(IntEnum):
    MISSION = 0
    FENCE = 1
    RALLY = 2
    PATH_PLANNING = 3


@dataclass
class GeoPoint:
    """地理坐标点"""
    lat: float              # 度
    lon: float
    alt: float              # m (相对起飞点)
    frame: MAV_FRAME = MAV_FRAME.GLOBAL_RELATIVE_ALT


class GeoConverter:
    """
    本地坐标 (km) ↔ 地理坐标 (WGS84)

    model-engine 输出: xy km (成都中心为原点)
    PX4/ArduPilot 输入: lat/lon/alt
    """

    def __init__(self, ref_lat: float = 30.67, ref_lon: float = 104.07,
                 ref_alt: float = 500.0):
        self.cfg = GeoConfig(ref_lat=ref_lat, ref_lon=ref_lon, ref_alt=ref_alt)

    def local_to_geo(self, x_km: float, y_km: float,
                     alt_m: float = 100.0) -> GeoPoint:
        """
        本地坐标 → 经纬度

        Args:
            x_km: 东西向 (正=东, km)
            y_km: 南北向 (正=北, km)
            alt_m: 海拔高度 (m)

        Returns:
            GeoPoint(lat, lon, alt)
        """
        lat = self.cfg.ref_lat + y_km * self.cfg.lat_per_km
        lon = self.cfg.ref_lon + x_km * self.cfg.lon_per_km
        alt = self.cfg.ref_alt + alt_m
        return GeoPoint(lat=lat, lon=lon, alt=alt)

    def geo_to_local(self, lat: float, lon: float,
                     alt: float) -> Tuple[float, float, float]:
        """经纬度 → 本地坐标"""
        y_km = (lat - self.cfg.ref_lat) / self.cfg.lat_per_km
        x_km = (lon - self.cfg.ref_lon) / self.cfg.lon_per_km
        alt_m = alt - self.cfg.ref_alt
        return (x_km, y_km, alt_m)

    def waypoint_to_geo(self, wp) -> GeoPoint:
        """Waypoint → GeoPoint"""
        return self.local_to_geo(wp.x, wp.y, wp.z)


# ── .plan 任务文件生成 ──────────────────────────

class MissionPlanGenerator:
    """
    生成 QGroundControl 可导入的 .plan 文件

    QGC 的 .plan 是 JSON 格式:
    {
      "version": 1,
      "mission": {
        "cruiseSpeed": 15,
        "firmwareType": 12,          // PX4
        "items": [
          {"type": "missionItem",
           "command": 16,             // MAV_CMD_NAV_WAYPOINT
           "params": [0, 0, 0, 0, lat, lon, alt],
           "autoContinue": true},
          ...
        ]
      }
    }
    """

    def __init__(self, geoconv: Optional[GeoConverter] = None,
                 ref_lat: float = 30.67, ref_lon: float = 104.07):
        self.geo = geoconv or GeoConverter(ref_lat=ref_lat, ref_lon=ref_lon)

    def generate_plan(self, waypoints: list,
                      cruise_speed: float = 15.0,
                      firmware: str = "px4",
                      home: Optional[Tuple[float, float, float]] = None
                      ) -> str:
        home_pos = home
        """
        生成 .plan 任务文件

        Args:
            waypoints: 来自 path_planning.planner 的 Waypoint 列表
            cruise_speed: 巡航速度 m/s
            firmware: "px4" | "ardupilot"
            home_pos: (lat, lon, alt) 起飞点

        Returns:
            JSON 字符串 (保存为 .plan 文件即可导入 QGC)
        """
        firmware_type = 12 if firmware == "px4" else 3  # QGC firmware enums
        items = []

        # 0. 起飞点 (HOME)
        if home_pos:
            items.append(self._make_item(
                command=MAV_CMD.NAV_WAYPOINT,
                frame=MAV_FRAME.GLOBAL,
                params=[0, 0, 0, 0, home_pos[0], home_pos[1], home_pos[2]],
                comment="HOME"
            ))

        # 1. 起飞
        if waypoints:
            first = self.geo.waypoint_to_geo(waypoints[0])
            items.append(self._make_item(
                command=MAV_CMD.NAV_WAYPOINT,
                frame=MAV_FRAME.GLOBAL_RELATIVE_ALT,
                params=[0, 0, 0, 0, first.lat, first.lon, 50.0],
                comment="TAKEOFF"
            ))

        # 2. 途径点
        for i, wp in enumerate(waypoints[1:-1], 1):
            gp = self.geo.waypoint_to_geo(wp)
            items.append(self._make_item(
                command=MAV_CMD.NAV_WAYPOINT,
                frame=MAV_FRAME.GLOBAL_RELATIVE_ALT,
                params=[0, 0, 0, 0, gp.lat, gp.lon, max(gp.alt, 50)],
                comment=f"WAYPOINT_{i}"
            ))

        # 3. 最后的目标点
        if len(waypoints) >= 2:
            last = self.geo.waypoint_to_geo(waypoints[-1])
            items.append(self._make_item(
                command=MAV_CMD.NAV_WAYPOINT,
                frame=MAV_FRAME.GLOBAL_RELATIVE_ALT,
                params=[0, 0, 0, 0, last.lat, last.lon, max(last.alt, 50)],
                comment="TARGET"
            ))

        # 4. 返航 (RTL)
        items.append(self._make_item(
            command=MAV_CMD.NAV_RETURN_TO_LAUNCH,
            frame=MAV_FRAME.GLOBAL,
            params=[0, 0, 0, 0, 0, 0, 0],
            comment="RTL"
        ))

        mission = {
            "version": 1,
            "mission": {
                "cruiseSpeed": cruise_speed,
                "firmwareType": firmware_type,
                "items": items,
            }
        }

        return json.dumps(mission, indent=2)

    def save_plan(self, waypoints: list, filepath: str = "mission.plan",
                  **kwargs):
        """生成并保存 .plan 文件"""
        plan_str = self.generate_plan(waypoints, **kwargs)
        Path(filepath).write_text(plan_str)
        return filepath

    @staticmethod
    def _make_item(command: int, frame: int, params: list,
                   comment: str = "") -> dict:
        """构造单个 mission item"""
        p = [0.0] * 7
        for i, v in enumerate(params):
            p[i] = float(v)
        return {
            "type": "missionItem",
            "command": int(command),
            "frame": int(frame),
            "params": p,
            "autoContinue": True,
            "comment": comment,
        }


# ── 实时 MAVLink 指令 (轻量实现) ───────────────

class MAVLinkEncoder:
    """
    轻量 MAVLink 消息编码器

    不依赖 pymavlink，直接构造 MAVLink v2 二进制协议。
    支持: HEARTBEAT, COMMAND_LONG, MISSION_ITEM_INT
    """

    def __init__(self, sys_id: int = 1, comp_id: int = 1,
                 target_sys: int = 1, target_comp: int = 1):
        self.sys_id = sys_id
        self.comp_id = comp_id
        self.target_sys = target_sys
        self.target_comp = target_comp

    # ── MAVLink v2 帧编码 ──

    def _encode_frame(self, msg_id: int, payload: bytes) -> bytes:
        """MAVLink v2 帧封装"""
        header = bytearray([
            0xFD,               # 起始字节 (MAVLink 2)
            len(payload),       # 负载长度
            0, 0,               # 不兼容/兼容标志
            0, 0,               # 序列号 (简化)
            self.sys_id,        # 系统 ID
            self.comp_id,       # 组件 ID
            msg_id & 0xFF,      # 消息 ID (低8位)
            (msg_id >> 8) & 0xFF,
            (msg_id >> 16) & 0xFF,
        ])
        # CRC (简化: 用 XOR, 实际应用需用 MAVLink CRC)
        crc = self._crc(header + payload)
        return bytes(header) + payload + crc.to_bytes(2, 'little')

    @staticmethod
    def _crc(data: bytes) -> int:
        """简化的 CRC (用于演示，实际需用 MAVLink CRC-16-MCRF4XX)"""
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc >>= 1
        return crc

    # ── 消息构造 ──

    def heartbeat(self, armed: bool = False) -> bytes:
        """HEARTBEAT (#0) — 告诉飞控地面站在线"""
        payload = struct.pack('<IBBBBB',
            0,                          # custom_mode
            4 if armed else 0,          # type (4=地面站)
            0,                          # autopilot
            3,                          # base_mode (3=guided)
            0,                          # custom_state
            0,                          # system_status
        )
        return self._encode_frame(0, payload)

    def goto_waypoint(self, lat: float, lon: float,
                      alt: float, speed: float = 10.0) -> bytes:
        """
        COMMAND_LONG (#76) — 发送 MAV_CMD_NAV_WAYPOINT
        """
        payload = struct.pack('<BBfffffffH',
            self.target_sys,
            self.target_comp,
            0, 0, 0, speed,
            float(lat), float(lon), float(alt),
            MAV_CMD.NAV_WAYPOINT,
        )
        return self._encode_frame(76, payload)

    def set_speed(self, speed_mps: float) -> bytes:
        """DO_CHANGE_SPEED — 调整巡航速度"""
        payload = struct.pack('<BBffffffHH',
            self.target_sys, self.target_comp,
            0, speed_mps, -1, 0, 0, 0, 0,
            MAV_CMD.DO_CHANGE_SPEED, 0,
        )
        return self._encode_frame(76, payload)

    def rtl(self) -> bytes:
        """NAV_RETURN_TO_LAUNCH — 立即返航"""
        payload = struct.pack('<BBfffffffH',
            self.target_sys,
            self.target_comp,
            0, 0, 0, 0, 0, 0, 0,
            MAV_CMD.NAV_RETURN_TO_LAUNCH,
        )
        return self._encode_frame(76, payload)

    def upload_mission_item(self, seq: int, command: int,
                            lat: float, lon: float, alt: float,
                            current: bool = False) -> bytes:
        """
        MISSION_ITEM_INT (#73) — 上传单个任务航点

        批量上传流程:
          1. MISSION_COUNT (#44) 告知飞控总航点数
          2. 飞控回复 MISSION_REQUEST_INT (#51)
          3. 逐个发送 MISSION_ITEM_INT (#73)
          4. 飞控回复 MISSION_ACK (#47)
        """
        payload = struct.pack('<BBBBHfffHHhh',
            self.target_sys, self.target_comp,
            0,                          # seq
            MAV_FRAME.GLOBAL_RELATIVE_ALT,  # frame
            command,                     # command
            0, 0, 0,  # current, autocontinue, param1
            0, 0,      # param2, param3
            int(lat * 1e7),              # x (纬度 × 1e7)
            int(lon * 1e7),              # y (经度 × 1e7)
            int(alt * 1000),             # z (高度 mm)
            0, 0, 0, 0,  # param4-7
        )
        return self._encode_frame(73, payload)


# ── 一键输出 ────────────────────────────────────

def export_to_mavlink(waypoints: list,
                      output_type: str = "plan",
                      speed: float = 15.0,
                      home: Optional[Tuple[float, float, float]] = None,
                      **kwargs
                      ) -> str:
    """
    路径规划结果 → PX4/ArduPilot 原生格式

    Args:
        waypoints: GPRPathPlanner 的 Waypoint 列表
        output_type: "plan" → .plan 任务文件 | "mavlink" → 实时指令
        speed: 巡航速度 m/s
        home: 起飞点 (lat, lon, alt)，不指定则自动计算
        save_path: .plan 文件保存路径

    Returns:
        "plan" 模式 → JSON字符串
        "mavlink" 模式 → 二进制 MAVLink 帧串
    """
    geo = GeoConverter()
    gen = MissionPlanGenerator(geo)

    # 自动计算起飞点 (第一个航点的反向偏移)
    if home is None and waypoints:
        home_gp = geo.waypoint_to_geo(waypoints[0])
        home = (home_gp.lat - 0.001, home_gp.lon - 0.001, 500.0)

    if output_type == "plan":
        return gen.generate_plan(waypoints, speed, home=home)
    else:
        # 实时 MAVLink 指令流
        encoder = MAVLinkEncoder()
        frames = [encoder.heartbeat(armed=False)]

        for wp in waypoints:
            gp = geo.waypoint_to_geo(wp)
            frames.append(encoder.goto_waypoint(gp.lat, gp.lon, gp.alt, speed))

        frames.append(encoder.rtl())
        # 帧间用 0xFE 分隔
        return b'\xFE'.join(frames).hex()
