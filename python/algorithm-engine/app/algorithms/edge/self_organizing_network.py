"""自组织网络模块。

边缘设备自组织网络拓扑管理，
动态调整通信链路，实现自适应网络连接。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SelfOrganizingNetwork:
    """自组织网络管理器。

    管理边缘设备间的自组织网络拓扑，
    根据设备位置和信号质量动态调整通信链路。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_hops = self.config.get("max_hops", 5)
        self.min_snr = self.config.get("min_snr", 10.0)
        self.topology: dict[str, list[str]] = {}

    def organize(self, params: dict[str, Any]) -> dict[str, Any]:
        """组织自组织网络拓扑。

        Args:
            params: 网络组织参数字典，包含：
                - nodes: 节点列表，每个节点包含 {"id": str, "position": [x, y, z]}。
                - signal_range: 通信范围（米），默认 500。
                - interference: 干扰系数，默认 0.1。

        Returns:
            网络组织结果字典，包含：
                - topology: 网络拓扑邻接表。
                - network_metrics: 网络性能指标。
                - connectivity: 网络连通性信息。
        """
        np.random.seed(42)

        nodes = params.get("nodes", [])
        signal_range = params.get("signal_range", 500.0)
        interference = params.get("interference", 0.1)

        t_start = _time.perf_counter()

        if not nodes:
            return {
                "topology": {},
                "network_metrics": {"avg_degree": 0, "max_degree": 0, "n_links": 0},
                "connectivity": {"connected": False, "n_components": 0},
            }

        # 计算节点间距离
        n = len(nodes)
        positions = np.array([node["position"] for node in nodes], dtype=float)
        distances = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = float(np.linalg.norm(positions[i] - positions[j]))
                distances[i][j] = d
                distances[j][i] = d

        # 构建拓扑：信号范围内的节点建立链路
        topology: dict[str, list[str]] = {}
        link_qualities: dict[tuple[str, str], float] = {}
        node_degrees: dict[str, int] = {}

        for i, node_i in enumerate(nodes):
            nid_i = node_i["id"]
            topology[nid_i] = []
            node_degrees[nid_i] = 0

        for i in range(n):
            for j in range(i + 1, n):
                nid_i = nodes[i]["id"]
                nid_j = nodes[j]["id"]
                d = distances[i][j]

                if d <= signal_range:
                    # 计算信噪比（模拟）
                    snr = 20.0 * np.log10(signal_range / max(d, 1.0)) - interference * 10
                    snr = max(0, snr)

                    if snr >= self.min_snr:
                        topology[nid_i].append(nid_j)
                        topology[nid_j].append(nid_i)
                        link_qualities[(nid_i, nid_j)] = round(float(snr), 2)
                        link_qualities[(nid_j, nid_i)] = round(float(snr), 2)
                        node_degrees[nid_i] += 1
                        node_degrees[nid_j] += 1

        # 计算网络指标
        degrees = list(node_degrees.values())
        n_links = sum(degrees) // 2
        avg_degree = float(np.mean(degrees)) if degrees else 0.0
        max_degree = max(degrees) if degrees else 0

        # 检查连通性（BFS）
        visited = set()
        components = 0
        for node in nodes:
            nid = node["id"]
            if nid not in visited:
                components += 1
                queue = [nid]
                visited.add(nid)
                while queue:
                    current = queue.pop(0)
                    for neighbor in topology.get(current, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

        connected = components == 1

        t_end = _time.perf_counter()
        organize_time = (t_end - t_start) * 1000

        return {
            "topology": topology,
            "network_metrics": {
                "avg_degree": round(avg_degree, 2),
                "max_degree": max_degree,
                "n_links": n_links,
                "n_nodes": n,
                "organize_time_ms": round(organize_time, 3),
            },
            "connectivity": {
                "connected": connected,
                "n_components": components,
                "visited_nodes": len(visited),
            },
            "link_qualities": link_qualities,
        }
