"""
WebSocket 实时状态同步 - 增强版
支持心跳检测、重连机制、连接健康监控和 Prometheus 指标
边缘节点与云端实时双向通信
"""
import logging
import asyncio
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# ==================== Prometheus 指标 ====================

try:
    from prometheus_client import Counter, Gauge
    HAS_PROMETHEUS = True

    ws_active_connections = Gauge(
        'websocket_active_connections',
        '当前活跃的 WebSocket 连接数',
        ['node_id']
    )
    ws_connections_total = Counter(
        'websocket_connections_total',
        'WebSocket 连接总数',
        ['node_id']
    )
    ws_disconnections_total = Counter(
        'websocket_disconnections_total',
        'WebSocket 断开总数',
        ['node_id', 'reason']
    )
    ws_reconnections_total = Counter(
        'websocket_reconnections_total',
        'WebSocket 重连总数',
        ['node_id']
    )
    ws_heartbeat_timeouts_total = Counter(
        'websocket_heartbeat_timeouts_total',
        '心跳超时总数',
        ['node_id']
    )
    ws_heartbeat_sent_total = Counter(
        'websocket_heartbeat_sent_total',
        '心跳发送总数',
        ['node_id']
    )
    ws_messages_received_total = Counter(
        'websocket_messages_received_total',
        '接收消息总数',
        ['node_id', 'msg_type']
    )
    ws_messages_sent_total = Counter(
        'websocket_messages_sent_total',
        '发送消息总数',
        ['node_id', 'msg_type']
    )
except ImportError:
    HAS_PROMETHEUS = False

    class _DummyMetric:
        """Prometheus 未安装时的空桩"""
        def labels(self, **kwargs): return self
        def inc(self, amount=1): pass
        def set(self, amount): pass

    ws_active_connections = _DummyMetric()
    ws_connections_total = _DummyMetric()
    ws_disconnections_total = _DummyMetric()
    ws_reconnections_total = _DummyMetric()
    ws_heartbeat_timeouts_total = _DummyMetric()
    ws_heartbeat_sent_total = _DummyMetric()
    ws_messages_received_total = _DummyMetric()
    ws_messages_sent_total = _DummyMetric()


# ==================== 消息类型定义 ====================


class MessageType(Enum):
    DRONE_STATUS = "drone_status"
    WEATHER_UPDATE = "weather_update"
    PATH_UPDATE = "path_update"
    TASK_ASSIGNMENT = "task_assignment"
    ALERT = "alert"
    MODEL_SYNC = "model_sync"
    HEARTBEAT = "heartbeat"


@dataclass
class WSMessage:
    msg_type: MessageType
    drone_id: str
    payload: dict
    timestamp: float
    msg_id: str = ""


@dataclass
class ConnectionInfo:
    """单个连接的完整信息"""
    websocket: object
    drone_id: str
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    reconnect_count: int = 0
    last_disconnect_time: float = 0.0
    heartbeat_task: Optional[asyncio.Task] = None
    remote_addr: Optional[str] = None


# ==================== 核心同步管理器 ====================


class WebSocketSync:
    """WebSocket 实时状态同步 - 增强版

    特性：
    - 每 30 秒发送心跳 ping
    - 60 秒无心跳自动断开（过期连接检测）
    - 重连计数器与指数退避建议
    - Prometheus 连接指标
    - 优雅断开与资源清理
    """

    HEARTBEAT_INTERVAL = 30       # 心跳发送间隔（秒）
    STALE_TIMEOUT = 60            # 无响应超时阈值（秒）

    # 指数退避参数
    BACKOFF_BASE = 5              # 基础退避时间（秒）
    BACKOFF_MAX = 300             # 最大退避时间（秒）

    def __init__(self, node_id: str = "coordinator"):
        self.node_id = node_id
        self.connections: Dict[str, ConnectionInfo] = {}
        self.subscribers: Dict[MessageType, List[Callable]] = {}
        self.drone_states: Dict[str, dict] = {}
        self.message_buffer: List[WSMessage] = []

    # ---- 订阅 / 发布 ----

    def register_handler(self, msg_type: MessageType, handler: Callable):
        """注册消息处理器"""
        if msg_type not in self.subscribers:
            self.subscribers[msg_type] = []
        self.subscribers[msg_type].append(handler)

    # ---- 连接生命周期 ----

    async def connect(self, drone_id: str, ws: object) -> ConnectionInfo:
        """建立 WebSocket 连接

        如果已存在同名连接，自动关闭旧连接并计入重连计数。
        """
        reconnect_count = 0
        if drone_id in self.connections:
            old_info = self.connections[drone_id]
            reconnect_count = old_info.reconnect_count + 1
            await self.disconnect(drone_id, reason="reconnect")

        # 获取对端地址
        remote_addr = None
        try:
            remote_addr = f"{ws.client.host}:{ws.client.port}"
        except Exception:
            pass

        conn_info = ConnectionInfo(
            websocket=ws,
            drone_id=drone_id,
            reconnect_count=reconnect_count,
            connected_at=time.time(),
            last_heartbeat=time.time(),
            remote_addr=remote_addr,
        )
        self.connections[drone_id] = conn_info
        self.drone_states[drone_id] = {
            'status': 'connected',
            'last_seen': time.time(),
            'reconnect_count': reconnect_count,
            'remote_addr': remote_addr,
        }

        # 启动针对该连接的心跳监控协程
        conn_info.heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(drone_id)
        )

        logger.info(
            f"无人机已连接: {drone_id} "
            f"(重连 #{reconnect_count}, 地址: {remote_addr})"
        )

        if HAS_PROMETHEUS:
            ws_active_connections.labels(node_id=self.node_id).set(
                len(self.connections)
            )
            ws_connections_total.labels(node_id=self.node_id).inc()
            if reconnect_count > 0:
                ws_reconnections_total.labels(node_id=self.node_id).inc()

        return conn_info

    async def disconnect(self, drone_id: str, reason: str = "normal"):
        """断开连接（增强版：取消心跳任务、更新指标）"""
        conn_info = self.connections.pop(drone_id, None)
        if conn_info is None:
            return

        # 取消心跳任务
        if conn_info.heartbeat_task is not None and not conn_info.heartbeat_task.done():
            conn_info.heartbeat_task.cancel()
            try:
                await conn_info.heartbeat_task
            except asyncio.CancelledError:
                pass

        # 更新状态
        if drone_id in self.drone_states:
            self.drone_states[drone_id]['status'] = 'disconnected'
            self.drone_states[drone_id]['last_seen'] = time.time()

        logger.info(
            f"无人机已断开: {drone_id} (原因: {reason})"
        )

        if HAS_PROMETHEUS:
            ws_active_connections.labels(node_id=self.node_id).set(
                len(self.connections)
            )
            ws_disconnections_total.labels(
                node_id=self.node_id, reason=reason
            ).inc()

    # ---- 消息收发 ----

    async def send_message(self, drone_id: str, msg_type: MessageType, data: dict) -> bool:
        """向指定连接发送 JSON 消息"""
        conn_info = self.connections.get(drone_id)
        if conn_info is None:
            logger.warning(f"发送消息失败，连接不存在: {drone_id}")
            return False

        try:
            await conn_info.websocket.send_json({
                'type': msg_type.value,
                'drone_id': drone_id,
                'payload': data,
                'timestamp': time.time(),
            })
            if HAS_PROMETHEUS:
                ws_messages_sent_total.labels(
                    node_id=self.node_id, msg_type=msg_type.value
                ).inc()
            return True
        except Exception as e:
            logger.error(f"发送消息失败 ({drone_id}): {e}")
            await self.disconnect(drone_id, reason="send_error")
            return False

    async def send_status(self, drone_id: str, status_data: dict):
        """发送实时状态（快捷方法）"""
        self.drone_states[drone_id] = status_data
        await self.send_message(drone_id, MessageType.DRONE_STATUS, status_data)

    async def broadcast(self, msg_type: MessageType, data: dict):
        """广播消息到所有连接"""
        msg = WSMessage(
            msg_type=msg_type, drone_id='broadcast',
            payload=data, timestamp=time.time(),
        )
        self.message_buffer.append(msg)

        # 调用本地订阅者
        for cb in self.subscribers.get(msg_type, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(data)
                else:
                    cb(data)
            except Exception as e:
                logger.error(f"广播回调失败: {e}")

        # 推送到所有 WebSocket 客户端
        for drone_id in list(self.connections.keys()):
            await self.send_message(drone_id, msg_type, data)

    async def handle_message(self, drone_id: str, message: dict) -> bool:
        """处理从客户端接收到的消息

        - pong/heartbeat → 更新心跳时间戳
        - 其他消息 → 转发给注册的订阅者
        """
        msg_type_raw = message.get('type', '')
        payload = message.get('payload', {})

        # 心跳响应处理
        if msg_type_raw in ('pong', 'heartbeat'):
            await self.update_heartbeat(drone_id)
            return True

        # 任何消息都视为连接活跃信号
        await self.update_heartbeat(drone_id)

        # 解析消息类型并通知订阅者
        try:
            msg_enum = MessageType(msg_type_raw)
        except ValueError:
            logger.warning(f"未知消息类型: {msg_type_raw} (来自 {drone_id})")
            return False

        if HAS_PROMETHEUS:
            ws_messages_received_total.labels(
                node_id=self.node_id, msg_type=msg_type_raw
            ).inc()

        for cb in self.subscribers.get(msg_enum, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(payload)
                else:
                    cb(payload)
            except Exception as e:
                logger.error(f"消息处理回调失败: {e}")

        return True

    # ---- 心跳逻辑 ----

    async def update_heartbeat(self, drone_id: str):
        """更新连接的最新心跳时间"""
        conn_info = self.connections.get(drone_id)
        if conn_info:
            conn_info.last_heartbeat = time.time()
            if drone_id in self.drone_states:
                self.drone_states[drone_id]['last_seen'] = time.time()

    async def _heartbeat_loop(self, drone_id: str):
        """单连接心跳监控循环

        每 30s 向客户端发送 ping；
        如果超过 60s 未收到任何响应，判定为过期连接并断开。
        """
        try:
            while drone_id in self.connections:
                conn_info = self.connections[drone_id]
                now = time.time()
                elapsed = now - conn_info.last_heartbeat

                # ---- 过期检测 ----
                if elapsed >= self.STALE_TIMEOUT:
                    logger.warning(
                        f"心跳超时，断开连接: {drone_id} "
                        f"(上次心跳: {elapsed:.1f}s 前)"
                    )
                    if HAS_PROMETHEUS:
                        ws_heartbeat_timeouts_total.labels(
                            node_id=self.node_id
                        ).inc()
                    await self.disconnect(drone_id, reason="heartbeat_timeout")
                    break

                # ---- 发送 ping ----
                try:
                    await conn_info.websocket.send_json({
                        'type': 'ping',
                        'timestamp': now,
                    })
                    if HAS_PROMETHEUS:
                        ws_heartbeat_sent_total.labels(
                            node_id=self.node_id
                        ).inc()
                except Exception as e:
                    logger.error(f"心跳发送失败 ({drone_id}): {e}")
                    await self.disconnect(drone_id, reason="heartbeat_failed")
                    break

                await asyncio.sleep(self.HEARTBEAT_INTERVAL)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"心跳循环异常 ({drone_id}): {e}")

    # ---- 查询接口 ----

    def get_connected_drones(self) -> List[str]:
        return list(self.connections.keys())

    def get_drone_state(self, drone_id: str) -> Optional[dict]:
        return self.drone_states.get(drone_id)

    def get_connection_info(self, drone_id: str) -> Optional[ConnectionInfo]:
        return self.connections.get(drone_id)

    def get_reconnect_backoff(self, drone_id: str) -> int:
        """计算建议的指数退避时间（秒）

        公式: min(BACKOFF_BASE * 2^attempt, BACKOFF_MAX)
        """
        conn_info = self.connections.get(drone_id)
        if conn_info is None:
            return 0
        delay = self.BACKOFF_BASE * (2 ** conn_info.reconnect_count)
        return int(min(delay, self.BACKOFF_MAX))

    async def get_health_status(self) -> dict:
        """获取所有连接的详细健康状态"""
        now = time.time()
        connections_health = {}
        for drone_id, info in self.connections.items():
            idle_seconds = now - info.last_heartbeat
            connections_health[drone_id] = {
                'connected_at': info.connected_at,
                'last_heartbeat': info.last_heartbeat,
                'age_seconds': round(now - info.connected_at, 1),
                'idle_seconds': round(idle_seconds, 1),
                'reconnect_count': info.reconnect_count,
                'suggested_backoff': self.get_reconnect_backoff(drone_id),
                'healthy': idle_seconds < self.STALE_TIMEOUT,
                'remote_addr': info.remote_addr,
            }

        return {
            'node_id': self.node_id,
            'total_connections': len(self.connections),
            'heartbeat_interval': self.HEARTBEAT_INTERVAL,
            'stale_timeout': self.STALE_TIMEOUT,
            'connections': connections_health,
            'total_messages_buffered': len(self.message_buffer),
        }

    async def cleanup(self):
        """优雅关闭：断开所有连接并清理资源"""
        for drone_id in list(self.connections.keys()):
            await self.disconnect(drone_id, reason="server_shutdown")
        self.message_buffer.clear()
        self.subscribers.clear()
        logger.info("WebSocket 同步管理器已清理")


# ==================== 独立 WebSocket 服务端（保持向后兼容）====================


class WebSocketServer:
    """WebSocket 服务端 — 与 api.py 配合使用

    建议通过 FastAPI 的 @app.websocket 挂载端点，
    直接使用 WebSocketSync 实例管理连接。
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.sync = WebSocketSync()
        self._server = None
        self._running = False

    async def start(self):
        logger.info(f"WebSocket 服务启动: ws://{self.host}:{self.port}")
        self._running = True
        return self

    async def stop(self):
        self._running = False
        await self.sync.cleanup()
        logger.info("WebSocket 服务停止")
