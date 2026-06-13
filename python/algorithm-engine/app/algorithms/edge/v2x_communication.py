"""V2X (Vehicle-to-Everything) 通信模块。

支持 UAV 与地面站、其他 UAV、UTM 系统之间的通信模拟。
包含 DSRC/C-V2X 消息格式、信道模型、广播/单播通信。
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class V2XCommunication:
    """V2X 通信模拟器。

    模拟 UAV 与地面站、其他 UAV、UTM 系统之间的 V2X 通信，
    支持自由空间路径损耗模型，提供广播、单播、信道质量评估
    和网络拓扑生成功能。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """初始化 V2X 通信模块。

        Args:
            config: 配置字典，支持以下参数：
                - channel_model: 信道模型，默认 "free_space"
                - frequency_ghz: 载波频率 (GHz)，默认 5.9（DSRC 频段）
                - tx_power_dbm: 发射功率 (dBm)，默认 20
                - bandwidth_mhz: 信道带宽 (MHz)，默认 10
        """
        self.config = config or {}
        self.channel_model = self.config.get("channel_model", "free_space")
        self.frequency_ghz = self.config.get("frequency_ghz", 5.9)
        self.tx_power_dbm = self.config.get("tx_power_dbm", 20)
        self.bandwidth_mhz = self.config.get("bandwidth_mhz", 10)

        # 物理常数
        self.speed_of_light = 3e8  # 光速 (m/s)
        self.boltzmann_constant = 1.38e-23  # 玻尔兹曼常数 (J/K)
        self.noise_temperature = 290  # 热噪声温度 (K)
        self.noise_figure_db = 6  # 接收机噪声系数 (dB)

        # 接收机灵敏度阈值
        self.rx_sensitivity_dbm = -90
        # SNR 解调门限 (dB)，对应 QPSK 1/2 编码
        self.snr_threshold_db = 5.0

        logger.info(
            "V2X 通信模块初始化完成: channel_model=%s, freq=%.1f GHz, "
            "tx_power=%.1f dBm, bandwidth=%.1f MHz",
            self.channel_model,
            self.frequency_ghz,
            self.tx_power_dbm,
            self.bandwidth_mhz,
        )

    def _path_loss(self, distance_km: float) -> float:
        """计算自由空间路径损耗。

        使用自由空间路径损耗模型：
        PL(dB) = 20*log10(d) + 20*log10(f) + 32.44
        其中 d 为距离 (km)，f 为频率 (MHz)。

        Args:
            distance_km: 传播距离 (km)。

        Returns:
            路径损耗值 (dB)。
        """
        frequency_mhz = self.frequency_ghz * 1000
        if distance_km <= 0:
            return 0.0
        pl = 20 * math.log10(distance_km) + 20 * math.log10(frequency_mhz) + 32.44
        return pl

    def _compute_snr(self, distance_km: float) -> float:
        """根据距离计算信噪比 (SNR)。

        Args:
            distance_km: 传播距离 (km)。

        Returns:
            SNR 值 (dB)。
        """
        path_loss = self._path_loss(distance_km)
        rx_power = self.tx_power_dbm - path_loss

        # 计算热噪声功率
        noise_figure_linear = 10 ** (self.noise_figure_db / 10)
        bandwidth_hz = self.bandwidth_mhz * 1e6
        noise_power_w = (
            self.boltzmann_constant * self.noise_temperature * bandwidth_hz * noise_figure_linear
        )
        noise_power_dbm = 10 * math.log10(noise_power_w * 1000)

        snr = rx_power - noise_power_dbm
        return snr

    def _snr_to_packet_loss(self, snr_db: float) -> float:
        """将 SNR 映射为丢包率。

        使用简化的 S 型曲线模型，SNR 越高丢包率越低。

        Args:
            snr_db: 信噪比 (dB)。

        Returns:
            丢包率，范围 [0, 1]。
        """
        if snr_db <= 0:
            return 1.0
        # S 型曲线参数
        midpoint = self.snr_threshold_db
        steepness = 0.5
        packet_loss = 1.0 / (1.0 + math.exp(steepness * (snr_db - midpoint)))
        return max(0.0, min(1.0, packet_loss))

    def _compute_latency(self, distance_km: float, message_size_bytes: int) -> float:
        """计算通信延迟。

        包含传播延迟和传输延迟。

        Args:
            distance_km: 传播距离 (km)。
            message_size_bytes: 消息大小 (字节)。

        Returns:
            总延迟 (毫秒)。
        """
        # 传播延迟 (光速)
        distance_m = distance_km * 1000
        propagation_delay_s = distance_m / self.speed_of_light

        # 传输延迟 (假设数据速率为带宽的 80%)
        data_rate_bps = self.bandwidth_mhz * 1e6 * 0.8
        transmission_delay_s = (message_size_bytes * 8) / data_rate_bps

        # 处理延迟 (固定开销)
        processing_delay_s = 0.001  # 1ms

        total_delay_ms = (propagation_delay_s + transmission_delay_s + processing_delay_s) * 1000
        return total_delay_ms

    def broadcast(self, params: dict[str, Any]) -> dict[str, Any]:
        """模拟 V2V 广播通信。

        计算每个接收者的 SNR、丢包率和延迟。

        Args:
            params: 广播参数字典，包含：
                - sender_position: 发送者位置 [x, y, z] (km)。
                - receiver_positions: 接收者位置列表，每个为 [x, y, z] (km)。
                - message_size_bytes: 消息大小 (字节)，默认 256。
                - data_rate_mbps: 数据速率 (Mbps)，默认 6。

        Returns:
            广播结果字典，包含：
                - receivers: 接收者结果列表，每个包含 snr, packet_loss,
                  latency_ms, received。
                - sender_position: 发送者位置。
                - n_receivers: 接收者数量。
                - n_received: 成功接收数量。
        """
        sender_position = params.get("sender_position", [0.0, 0.0, 0.1])
        receiver_positions = params.get("receiver_positions", [])
        message_size_bytes = params.get("message_size_bytes", 256)
        _data_rate_mbps = params.get("data_rate_mbps", 6)

        sender = np.array(sender_position, dtype=float)
        receivers = []

        for rx_pos in receiver_positions:
            rx = np.array(rx_pos, dtype=float)
            distance_km = float(np.linalg.norm(sender - rx))

            snr = self._compute_snr(distance_km)
            packet_loss = self._snr_to_packet_loss(snr)
            latency_ms = self._compute_latency(distance_km, message_size_bytes)

            # 根据丢包率随机决定是否成功接收
            received = np.random.rand() > packet_loss

            receivers.append({
                "position": rx_pos,
                "distance_km": round(distance_km, 6),
                "snr": round(snr, 2),
                "packet_loss": round(packet_loss, 4),
                "latency_ms": round(latency_ms, 3),
                "received": bool(received),
            })

        n_received = sum(1 for r in receivers if r["received"])

        return {
            "receivers": receivers,
            "sender_position": sender_position,
            "n_receivers": len(receivers),
            "n_received": n_received,
            "delivery_ratio": round(n_received / len(receivers), 4) if receivers else 0.0,
        }

    def unicast(self, params: dict[str, Any]) -> dict[str, Any]:
        """模拟点对点单播通信。

        Args:
            params: 单播参数字典，包含：
                - sender_position: 发送者位置 [x, y, z] (km)。
                - receiver_position: 接收者位置 [x, y, z] (km)。
                - message_size_bytes: 消息大小 (字节)，默认 1024。

        Returns:
            单播结果字典，包含：
                - snr: 信噪比 (dB)。
                - packet_loss: 丢包率。
                - latency_ms: 延迟 (毫秒)。
                - throughput_mbps: 吞吐量 (Mbps)。
                - received: 是否成功接收。
                - distance_km: 通信距离 (km)。
        """
        sender_position = params.get("sender_position", [0.0, 0.0, 0.1])
        receiver_position = params.get("receiver_position", [1.0, 0.0, 0.0])
        message_size_bytes = params.get("message_size_bytes", 1024)

        sender = np.array(sender_position, dtype=float)
        receiver = np.array(receiver_position, dtype=float)
        distance_km = float(np.linalg.norm(sender - receiver))

        snr = self._compute_snr(distance_km)
        packet_loss = self._snr_to_packet_loss(snr)
        latency_ms = self._compute_latency(distance_km, message_size_bytes)

        # 有效吞吐量 = 数据速率 * (1 - 丢包率)
        data_rate_mbps = self.bandwidth_mhz * 0.8
        throughput_mbps = data_rate_mbps * (1.0 - packet_loss)

        received = np.random.rand() > packet_loss

        return {
            "snr": round(snr, 2),
            "packet_loss": round(packet_loss, 4),
            "latency_ms": round(latency_ms, 3),
            "throughput_mbps": round(throughput_mbps, 2),
            "received": bool(received),
            "distance_km": round(distance_km, 6),
        }

    def channel_quality(self, params: dict[str, Any]) -> dict[str, Any]:
        """评估区域内的信道质量。

        Args:
            params: 信道质量评估参数字典，包含：
                - positions: 待评估位置列表，每个为 [x, y, z] (km)。
                - interference_sources: 干扰源列表，每个为
                  {"position": [x, y, z], "power_dbm": float}。

        Returns:
            信道质量评估结果，包含：
                - quality_map: 质量地图列表，每个位置包含 position, snr,
                  quality_level。
                - n_positions: 评估位置数量。
                - avg_snr: 平均 SNR (dB)。
        """
        positions = params.get("positions", [])
        interference_sources = params.get("interference_sources", [])

        quality_map = []

        for pos in positions:
            # 假设评估点为接收者，以 UAV 默认高度作为参考发射点
            ref_tx = np.array([0.0, 0.0, 0.1])  # 参考发射位置
            rx = np.array(pos, dtype=float)
            distance_km = float(np.linalg.norm(ref_tx - rx))

            snr = self._compute_snr(distance_km)

            # 计算干扰影响
            interference_power_dbm = 0.0
            for intf in interference_sources:
                intf_pos = np.array(intf["position"], dtype=float)
                intf_power = intf.get("power_dbm", 10)
                intf_distance_km = float(np.linalg.norm(rx - intf_pos))
                if intf_distance_km > 0:
                    intf_path_loss = self._path_loss(intf_distance_km)
                    interference_power_dbm += intf_power - intf_path_loss

            # 干扰降低有效 SNR
            if interference_power_dbm > 0:
                snr -= interference_power_dbm

            # 信道质量等级划分
            if snr >= 20:
                quality_level = "excellent"
            elif snr >= 15:
                quality_level = "good"
            elif snr >= 10:
                quality_level = "fair"
            elif snr >= self.snr_threshold_db:
                quality_level = "poor"
            else:
                quality_level = "unavailable"

            quality_map.append({
                "position": pos,
                "snr": round(snr, 2),
                "quality_level": quality_level,
            })

        avg_snr = (
            round(float(np.mean([q["snr"] for q in quality_map])), 2)
            if quality_map
            else 0.0
        )

        return {
            "quality_map": quality_map,
            "n_positions": len(positions),
            "avg_snr": avg_snr,
        }

    def network_topology(self, params: dict[str, Any]) -> dict[str, Any]:
        """生成 V2X 网络拓扑。

        在指定区域内随机分布节点，并根据通信范围建立连接。

        Args:
            params: 网络拓扑参数字典，包含：
                - node_count: 节点数量，默认 10。
                - area_size: 区域大小 [width, height] (km)，默认 [5, 5]。
                - connection_range: 连接范围 (km)，默认 2.0。

        Returns:
            网络拓扑结果，包含：
                - nodes: 节点列表，每个包含 id, position。
                - edges: 边列表，每个包含 source, target, distance_km, snr。
                - adjacency: 邻接表字典。
                - n_nodes: 节点数量。
                - n_edges: 边数量。
        """
        node_count = params.get("node_count", 10)
        area_size = params.get("area_size", [5.0, 5.0])
        connection_range = params.get("connection_range", 2.0)

        # 生成随机节点位置
        rng = np.random.default_rng()
        positions = rng.random((node_count, 3))
        positions[:, 0] *= area_size[0]  # x
        positions[:, 1] *= area_size[1]  # y
        positions[:, 2] = rng.uniform(0.01, 0.3, size=node_count)  # z (高度 10m-300m)

        nodes = []
        for i in range(node_count):
            nodes.append({
                "id": i,
                "position": positions[i].tolist(),
            })

        # 建立连接（基于通信范围和 SNR 阈值）
        edges = []
        adjacency: dict[int, list[int]] = {i: [] for i in range(node_count)}

        for i in range(node_count):
            for j in range(i + 1, node_count):
                distance_km = float(np.linalg.norm(positions[i] - positions[j]))
                if distance_km <= connection_range:
                    snr = self._compute_snr(distance_km)
                    if snr >= self.snr_threshold_db:
                        edges.append({
                            "source": i,
                            "target": j,
                            "distance_km": round(distance_km, 6),
                            "snr": round(snr, 2),
                        })
                        adjacency[i].append(j)
                        adjacency[j].append(i)

        return {
            "nodes": nodes,
            "edges": edges,
            "adjacency": adjacency,
            "n_nodes": node_count,
            "n_edges": len(edges),
        }
