"""
多协议支持模块

提供 HTTP REST 和 WebSocket 两种协议的支持，
确保服务端能够处理不同客户端的连接需求。
"""
import json
import logging

logger = logging.getLogger(__name__)


class MultiProtocolHandler:

    def __init__(self):
        self._ws_connections = set()

    async def handle_ws_message(self, websocket, message: str):
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "assimilate":
                result = {"type": "result", "status": "queued"}
                await websocket.send_json(result)
            elif msg_type == "subscribe":
                self._ws_connections.add(websocket)
                await websocket.send_json({"type": "subscribed"})
            elif msg_type == "unsubscribe":
                self._ws_connections.discard(websocket)
                await websocket.send_json({"type": "unsubscribed"})
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"未知消息类型: {msg_type}",
                })
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "无效的 JSON 格式",
            })

    async def broadcast(self, message: dict):
        disconnected = set()
        for ws in self._ws_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)
        self._ws_connections -= disconnected

    async def cleanup(self, websocket):
        self._ws_connections.discard(websocket)
