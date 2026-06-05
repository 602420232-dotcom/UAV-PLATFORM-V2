#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAV Edge SDK - Flight Controller Python Fallback
"""
import time
from typing import Dict, Any, List


class FlightControllerFallback:
    """飞控 Python 降级实现 - 模拟MAVLink通信"""

    def __init__(self, device: str = "COM3", baudrate: int = 57600):
        self.device = device
        self.baudrate = baudrate
        self.connected = False
        self.state = {
            'latitude': 31.2304,
            'longitude': 121.4737,
            'altitude': 0.0,
            'abs_altitude': 50.0,
            'heading': 0.0,
            'speed': 0.0,
            'battery': 100.0,
            'armed': False,
            'flying': False,
            'mode': 'STABILIZE',
            'system_status': 3,
            'roll': 0.0,
            'pitch': 0.0,
            'yaw': 0.0
        }
        self._connected_time = 0

    def connect(self) -> bool:
        self.connected = True
        self._connected_time = time.time()
        return True

    def disconnect(self):
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def get_state(self) -> Dict[str, Any]:
        self.state['last_heartbeat_ms'] = int(time.time() * 1000)
        return self.state

    def arm(self) -> bool:
        if not self.connected:
            return False
        self.state['armed'] = True
        return True

    def disarm(self) -> bool:
        if not self.connected:
            return False
        self.state['armed'] = False
        return True

    def set_mode(self, mode: str) -> bool:
        if not self.connected:
            return False
        valid_modes = ['MANUAL', 'STABILIZE', 'ALT_HOLD', 'POSITION',
                       'AUTO', 'RTL', 'LAND', 'TAKEOFF', 'GUIDED',
                       'LOITER', 'FOLLOW', 'CIRCLE']
        if mode not in valid_modes:
            return False
        self.state['mode'] = mode
        return True

    def takeoff(self, altitude: float) -> bool:
        if not self.connected:
            return False
        self.state['altitude'] = altitude
        self.state['flying'] = True
        self.state['mode'] = 'TAKEOFF'
        time.sleep(0.01)
        return True

    def land(self) -> bool:
        if not self.connected:
            return False
        self.state['altitude'] = 0.0
        self.state['flying'] = False
        self.state['mode'] = 'LAND'
        time.sleep(0.01)
        return True

    def return_to_launch(self) -> bool:
        if not self.connected:
            return False
        self.state['mode'] = 'RTL'
        return True

    def goto_position(self, lat: float, lon: float, alt: float) -> bool:
        if not self.connected:
            return False
        self.state['latitude'] = lat
        self.state['longitude'] = lon
        self.state['altitude'] = alt
        return True

    def upload_mission(self, waypoints: List[Any]) -> bool:
        return self.connected

    def execute_mission(self) -> bool:
        if not self.connected:
            return False
        self.state['mode'] = 'AUTO'
        return True

    def pause_mission(self) -> bool:
        if not self.connected:
            return False
        self.state['mode'] = 'POSITION'
        return True

    def clear_mission(self) -> bool:
        return self.connected

    def set_parameter(self, name: str, value: float) -> bool:
        return self.connected

    def get_parameter(self, name: str) -> float:
        return 0.0

    def get_mavlink_version(self) -> str:
        return "MAVLink v2.0 (Python fallback)"

    def get_last_heartbeat_ms(self) -> int:
        return int(time.time() * 1000)

    def get_connection_quality(self) -> float:
        if not self.connected:
            return 0.0
        elapsed = time.time() - self._connected_time
        if elapsed > 10:
            return 0.0
        return 100.0
