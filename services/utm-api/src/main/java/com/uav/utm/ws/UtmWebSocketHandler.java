package com.uav.utm.ws;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * UTM WebSocket 处理器
 * <p>
 * 处理客户端的 WebSocket 连接，支持：
 * <ul>
 *   <li>按 UAV ID 订阅位置更新: {@code {"action":"subscribe","channel":"uav:{uavId}"}}</li>
 *   <li>按区域订阅冲突告警: {@code {"action":"subscribe","channel":"area:{minLon},{minLat},{maxLon},{maxLat}"}}</li>
 *   <li>订阅全局告警: {@code {"action":"subscribe","channel":"alerts"}}</li>
 *   <li>取消订阅: {@code {"action":"unsubscribe","channel":"..."}}</li>
 * </ul>
 */
@Slf4j
@Component
public class UtmWebSocketHandler extends TextWebSocketHandler {

    private final ConcurrentHashMap<String, WebSocketSession> sessions = new ConcurrentHashMap<>();

    private final SubscriptionManager subscriptionManager;
    private final ObjectMapper objectMapper;

    public UtmWebSocketHandler(SubscriptionManager subscriptionManager, ObjectMapper objectMapper) {
        this.subscriptionManager = subscriptionManager;
        this.objectMapper = objectMapper;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        String sessionId = session.getId();
        sessions.put(sessionId, session);
        log.info("UTM WebSocket connection established: {}", sessionId);

        // 发送欢迎消息
        Map<String, Object> welcome = Map.of(
                "type", "WELCOME",
                "sessionId", sessionId,
                "message", "UTM WebSocket 连接成功"
        );
        session.sendMessage(new TextMessage(objectMapper.writeValueAsString(welcome)));
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        log.info("Received UTM message from {}: {}", session.getId(), payload);

        try {
            JsonNode jsonNode = objectMapper.readTree(payload);
            String action = jsonNode.path("action").asText("");
            String channel = jsonNode.path("channel").asText("");

            switch (action) {
                case "subscribe" -> handleSubscribe(session, channel);
                case "unsubscribe" -> handleUnsubscribe(session, channel);
                case "ping" -> handlePing(session);
                default -> {
                    log.warn("未知的 WebSocket action: {}, session: {}", action, session.getId());
                    sendError(session, "UNKNOWN_ACTION", "未知的操作: " + action);
                }
            }
        } catch (Exception e) {
            log.error("处理 WebSocket 消息失败, session: {}", session.getId(), e);
            sendError(session, "PARSE_ERROR", "消息解析失败: " + e.getMessage());
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        String sessionId = session.getId();
        sessions.remove(sessionId);
        // 清理该 session 的所有订阅
        subscriptionManager.removeAllSubscriptions(session);
        log.info("UTM WebSocket connection closed: {}, status: {}", sessionId, status);
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        log.error("UTM WebSocket transport error, session: {}", session.getId(), exception);
        if (session.isOpen()) {
            session.close(CloseStatus.SERVER_ERROR);
        }
    }

    // ===== 订阅处理 =====

    private void handleSubscribe(WebSocketSession session, String channel) {
        if (channel == null || channel.isEmpty()) {
            sendError(session, "INVALID_CHANNEL", "频道不能为空");
            return;
        }

        // 验证频道格式
        if (!isValidChannel(channel)) {
            sendError(session, "INVALID_CHANNEL", "无效的频道格式: " + channel);
            return;
        }

        subscriptionManager.subscribe(channel, session);

        Map<String, Object> response = Map.of(
                "type", "SUBSCRIBED",
                "channel", channel,
                "message", "订阅成功"
        );
        sendToSession(session.getId(), response);
    }

    private void handleUnsubscribe(WebSocketSession session, String channel) {
        if (channel == null || channel.isEmpty()) {
            sendError(session, "INVALID_CHANNEL", "频道不能为空");
            return;
        }

        subscriptionManager.unsubscribe(channel, session);

        Map<String, Object> response = Map.of(
                "type", "UNSUBSCRIBED",
                "channel", channel,
                "message", "取消订阅成功"
        );
        sendToSession(session.getId(), response);
    }

    private void handlePing(WebSocketSession session) {
        Map<String, Object> pong = Map.of("type", "PONG", "timestamp", System.currentTimeMillis());
        sendToSession(session.getId(), pong);
    }

    // ===== 频道验证 =====

    /**
     * 验证频道格式是否合法
     * <ul>
     *   <li>uav:{uavId} — UAV 位置订阅</li>
     *   <li>area:{minLon},{minLat},{maxLon},{maxLat} — 区域告警订阅</li>
     *   <li>alerts — 全局告警订阅</li>
     * </ul>
     */
    private boolean isValidChannel(String channel) {
        if ("alerts".equals(channel)) {
            return true;
        }
        if (channel.startsWith("uav:")) {
            String uavId = channel.substring(4);
            return !uavId.isEmpty();
        }
        if (channel.startsWith("area:")) {
            String coords = channel.substring(5);
            String[] parts = coords.split(",");
            if (parts.length == 4) {
                try {
                    for (String part : parts) {
                        Double.parseDouble(part.trim());
                    }
                    return true;
                } catch (NumberFormatException e) {
                    return false;
                }
            }
            return false;
        }
        return false;
    }

    // ===== 消息发送 =====

    /**
     * 向所有连接广播消息（保留原有方法）
     */
    public void broadcast(String message) {
        TextMessage textMessage = new TextMessage(message);
        sessions.forEach((id, session) -> {
            if (session.isOpen()) {
                try {
                    session.sendMessage(textMessage);
                } catch (IOException e) {
                    log.error("Failed to send WebSocket message to session {}", id, e);
                }
            }
        });
    }

    /**
     * 向指定 session 发送消息（保留原有方法）
     */
    public void sendToSession(String sessionId, String message) {
        WebSocketSession session = sessions.get(sessionId);
        if (session != null && session.isOpen()) {
            try {
                session.sendMessage(new TextMessage(message));
            } catch (IOException e) {
                log.error("Failed to send WebSocket message to session {}", sessionId, e);
            }
        }
    }

    /**
     * 向指定 session 发送对象消息（序列化为 JSON）
     */
    public void sendToSession(String sessionId, Object message) {
        try {
            String json = objectMapper.writeValueAsString(message);
            sendToSession(sessionId, json);
        } catch (Exception e) {
            log.error("序列化 WebSocket 消息失败, session: {}", sessionId, e);
        }
    }

    /**
     * 向订阅了指定 UAV 的客户端广播位置更新
     */
    public void broadcastUavPosition(String uavId, Object positionData) {
        subscriptionManager.broadcastToChannel("uav:" + uavId, positionData);
    }

    /**
     * 向告警频道广播告警
     */
    public void broadcastAlert(Object alertData) {
        subscriptionManager.broadcastToChannel("alerts", alertData);
    }

    /**
     * 向区域频道广播告警
     */
    public void broadcastAreaAlert(double minLon, double minLat, double maxLon, double maxLat, Object alertData) {
        String channel = String.format("area:%f,%f,%f,%f", minLon, minLat, maxLon, maxLat);
        subscriptionManager.broadcastToChannel(channel, alertData);
    }

    /**
     * 发送错误消息
     */
    private void sendError(WebSocketSession session, String code, String message) {
        Map<String, Object> error = Map.of(
                "type", "ERROR",
                "code", code,
                "message", message
        );
        sendToSession(session.getId(), error);
    }

    /**
     * 获取当前活跃连接数
     */
    public int getActiveSessionCount() {
        return sessions.size();
    }
}
