"""
自动驾驶集成 - V2X通信 + 协同感知 + 群智协同
"""
import logging
import time
import random
import numpy as np
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class V2XMessageType(Enum):
    BSM = "basic_safety"  # 基本安全消息
    PSM = "personal_safety"  # 个人安全消息
    MAP = "map_data"  # 地图数据
    SPaT = "signal_phase_timing"  # 信号灯相位
    RSM = "roadside_safety"  # 路侧安全
    CAM = "cooperative_awareness"  # 协同感知


@dataclass
class V2XMessage:
    msg_type: V2XMessageType
    sender_id: str
    timestamp: float
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float]
    heading: float
    data: dict
    ttl: int = 10


class V2XCommunicator:
    """V2X通信模块 - 车联网/无人机互联"""

    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.nearby_vehicles: Dict[str, dict] = {}
        self.message_buffer = deque(maxlen=1000)
        self.message_handlers: Dict[V2XMessageType, List[Callable]] = {}
        self.communication_range = 500.0
        self._init_handlers()

    def _init_handlers(self):
        for msg_type in V2XMessageType:
            self.message_handlers[msg_type] = []

    def register_handler(self, msg_type: V2XMessageType, handler: Callable):
        self.message_handlers[msg_type].append(handler)

    def broadcast(self, msg: V2XMessage):
        """广播V2X消息"""
        msg.timestamp = time.time()
        self.message_buffer.append(msg)
        logger.info(f"V2X广播: {msg.msg_type.value} from {msg.sender_id}")

    def receive(self, msg: V2XMessage):
        """接收V2X消息"""
        if msg.sender_id == self.vehicle_id:
            return
        dist = self._calc_distance(msg.position, self._get_self_position())
        if dist > self.communication_range:
            return
        self.nearby_vehicles[msg.sender_id] = {
            "position": msg.position,
            "velocity": msg.velocity,
            "heading": msg.heading,
            "last_seen": time.time(),
            "data": msg.data
        }
        for handler in self.message_handlers.get(msg.msg_type, []):
            handler(msg)

    def _calc_distance(self, pos1: Tuple, pos2: Tuple) -> float:
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2 +
                       (pos1[2] - pos2[2])**2) if len(pos1) > 2 else np.sqrt(
            (pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def _get_self_position(self) -> Tuple:
        return (0, 0, 0)

    def get_nearby_vehicles(self) -> List[dict]:
        return [{"id": vid, **vinfo} for vid, vinfo in self.nearby_vehicles.items()
                if time.time() - vinfo["last_seen"] < 5]


class CooperativePerception:
    """协同感知 - 多无人机融合感知"""

    def __init__(self):
        self.observations: Dict[str, List[dict]] = {}
        self.fused_map = {}

    def share_observation(self, drone_id: str, obstacles: List[dict],
                          weather: dict, position: Tuple[float, float]):
        """共享感知数据"""
        if drone_id not in self.observations:
            self.observations[drone_id] = []
        self.observations[drone_id].append({
            "obstacles": obstacles,
            "weather": weather,
            "position": position,
            "timestamp": time.time()
        })
        self._fuse_observations()

    def _fuse_observations(self):
        """融合多源观测"""
        all_obstacles = {}
        for did, obs_list in self.observations.items():
            for obs in obs_list[-5:
                ]:
                for ob in obs.get("obstacles", []):
                    key = (round(ob.get("lon", 0), 4), round(ob.get("lat", 0), 4))
                    if key in all_obstacles:
                        all_obstacles[key]["confidence"] += 0.2
                    else:
                        all_obstacles[key] = {**ob, "confidence": 0.5, "sources": [did]}
        self.fused_map = {
            "obstacles": [v for v in all_obstacles.values() if v["confidence"] > 0.5],
            "timestamp": time.time(),
            "coverage": len(self.observations)
        }

    def get_fused_view(self) -> dict:
        return self.fused_map


class SwarmIntelligence:
    """群智协同 - 无人机蜂群决策"""

    def __init__(self):
        self.drones: Dict[str, dict] = {}
        self.consensus_threshold = 0.6

    def register_drone(self, drone_id: str, capability: List[str] = None):
        self.drones[drone_id] = {"id": drone_id, "capabilities": capability or [],
                                  "votes": {}, "last_vote": 0}

    def propose_route(self, proposer: str, route: List[Tuple]) -> dict:
        """蜂群路线提议与共识"""
        votes_for = 1
        votes_against = 0
        total = len(self.drones)

        for did, drone in self.drones.items():
            if did == proposer:
                continue
            score = random.uniform(0, 1)
            if score > 0.3:
                votes_for += 1
            else:
                votes_against += 1

        consensus = votes_for / total >= self.consensus_threshold
        logger.info(f"蜂群共识: {proposer} 路线提议 {'通过' if consensus else '拒绝'} "
                    f"({votes_for}/{total})")
        return {
            "proposer": proposer,
            "consensus_reached": consensus,
            "votes_for": votes_for,
            "votes_against": votes_against,
            "total": total,
            "route": route if consensus else None,
            "suggestion": "执行路线" if consensus else "重新提议"
        }
