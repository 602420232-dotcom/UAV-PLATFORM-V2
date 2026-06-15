package com.uav.weather.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 气象数据 WebSocket 处理器
 * 支持基于 STOMP 协议的实时气象数据推送
 * 包含区域订阅/取消订阅、心跳检测机制
 */
@Slf4j
@Component
public class WeatherWebSocketHandler extends TextWebSocketHandler {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final ScheduledExecutorService heartbeatExecutor = Executors.newScheduledThreadPool(1);

    /**
     * 存储所有活跃会话
     */
    private final Set<WebSocketSession> sessions = ConcurrentHashMap.newKeySet();

    /**
     * 区域订阅映射：region -> sessions
     */
    private final Map<String, Set<WebSocketSession>> regionSubscriptions = new ConcurrentHashMap<>();

    /**
     * 会话订阅映射：session -> regions
     */
    private final Map<WebSocketSession, Set<String>> sessionSubscriptions = new ConcurrentHashMap<>();

    /**
     * 心跳间隔（30秒）
     */
    private static final long HEARTBEAT_INTERVAL_MS = 30000;

    public WeatherWebSocketHandler() {
        // 启动心跳检测定时任务
        heartbeatExecutor.scheduleAtFixedRate(this::sendHeartbeat, HEARTBEAT_INTERVAL_MS,
                HEARTBEAT_INTERVAL_MS, TimeUnit.MILLISECONDS);
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        log.info("WebSocket 连接建立: sessionId={}, remote={}", session.getId(), session.getRemoteAddress());
        sessions.add(session);
        sessionSubscriptions.put(session, ConcurrentHashMap.newKeySet());

        // 发送连接成功确认
        sendMessage(session, new WebSocketMessage("connected", "气象数据 WebSocket 连接成功", null));
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        log.debug("收到 WebSocket 消息: sessionId={}, payload={}", session.getId(), payload);

        try {
            ClientCommand command = objectMapper.readValue(payload, ClientCommand.class);

            switch (command.getAction()) {
                case "subscribe":
                    handleSubscribe(session, command.getRegion());
                    break;
                case "unsubscribe":
                    handleUnsubscribe(session, command.getRegion());
                    break;
                case "heartbeat":
                    handleHeartbeat(session);
                    break;
                case "query":
                    handleQuery(session, command.getRegion());
                    break;
                default:
                    sendMessage(session, new WebSocketMessage("error", "未知操作: " + command.getAction(), null));
            }
        } catch (Exception e) {
            log.error("处理 WebSocket 消息异常: sessionId={}", session.getId(), e);
            sendMessage(session, new WebSocketMessage("error", "消息处理失败: " + e.getMessage(), null));
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        log.info("WebSocket 连接关闭: sessionId={}, status={}", session.getId(), status);

        // 清理所有订阅
        Set<String> regions = sessionSubscriptions.get(session);
        if (regions != null) {
            for (String region : regions) {
                Set<WebSocketSession> regionSessions = regionSubscriptions.get(region);
                if (regionSessions != null) {
                    regionSessions.remove(session);
                    if (regionSessions.isEmpty()) {
                        regionSubscriptions.remove(region);
                    }
                }
            }
        }

        sessionSubscriptions.remove(session);
        sessions.remove(session);
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        log.error("WebSocket 传输错误: sessionId={}", session.getId(), exception);
        session.close(CloseStatus.SERVER_ERROR);
    }

    /**
     * 处理区域订阅请求
     */
    private void handleSubscribe(WebSocketSession session, String region) {
        if (region == null || region.trim().isEmpty()) {
            sendMessage(session, new WebSocketMessage("error", "区域标识不能为空", null));
            return;
        }

        regionSubscriptions.computeIfAbsent(region, k -> ConcurrentHashMap.newKeySet()).add(session);
        sessionSubscriptions.computeIfAbsent(session, k -> ConcurrentHashMap.newKeySet()).add(region);

        log.info("会话订阅区域: sessionId={}, region={}", session.getId(), region);
        sendMessage(session, new WebSocketMessage("subscribed", "已订阅区域: " + region, Map.of("region", region)));
    }

    /**
     * 处理取消订阅请求
     */
    private void handleUnsubscribe(WebSocketSession session, String region) {
        if (region == null) {
            // 取消所有订阅
            Set<String> regions = sessionSubscriptions.get(session);
            if (regions != null) {
                for (String r : regions) {
                    Set<WebSocketSession> regionSessions = regionSubscriptions.get(r);
                    if (regionSessions != null) {
                        regionSessions.remove(session);
                    }
                }
                regions.clear();
            }
            sendMessage(session, new WebSocketMessage("unsubscribed", "已取消所有订阅", null));
        } else {
            Set<WebSocketSession> regionSessions = regionSubscriptions.get(region);
            if (regionSessions != null) {
                regionSessions.remove(session);
            }
            Set<String> regions = sessionSubscriptions.get(session);
            if (regions != null) {
                regions.remove(region);
            }
            sendMessage(session, new WebSocketMessage("unsubscribed", "已取消订阅区域: " + region,
                    Map.of("region", region)));
        }
    }

    /**
     * 处理心跳响应
     */
    private void handleHeartbeat(WebSocketSession session) {
        sendMessage(session, new WebSocketMessage("heartbeat", "pong", null));
    }

    /**
     * 处理查询请求
     */
    private void handleQuery(WebSocketSession session, String region) {
        // 触发一次该区域的实时数据推送
        if (region != null && regionSubscriptions.containsKey(region)) {
            WeatherData mockData = generateMockWeatherData(region);
            sendMessage(session, new WebSocketMessage("weather_data", "实时气象数据", mockData));
        } else {
            sendMessage(session, new WebSocketMessage("error", "未订阅该区域或区域不存在", null));
        }
    }

    /**
     * 向指定区域的所有订阅会话推送气象数据
     */
    public void broadcastToRegion(String region, WeatherData data) {
        Set<WebSocketSession> regionSessions = regionSubscriptions.get(region);
        if (regionSessions == null || regionSessions.isEmpty()) {
            return;
        }

        WebSocketMessage message = new WebSocketMessage("weather_data", "实时气象数据推送", data);
        for (WebSocketSession session : regionSessions) {
            if (session.isOpen()) {
                sendMessage(session, message);
            }
        }
    }

    /**
     * 向所有活跃会话广播气象数据
     */
    public void broadcastToAll(WeatherData data) {
        WebSocketMessage message = new WebSocketMessage("weather_data", "全量实时气象数据", data);
        for (WebSocketSession session : sessions) {
            if (session.isOpen()) {
                sendMessage(session, message);
            }
        }
    }

    /**
     * 发送心跳消息到所有活跃会话
     */
    private void sendHeartbeat() {
        WebSocketMessage heartbeat = new WebSocketMessage("heartbeat", "ping", null);
        for (WebSocketSession session : sessions) {
            if (session.isOpen()) {
                sendMessage(session, heartbeat);
            }
        }
    }

    /**
     * 发送消息到指定会话
     */
    private void sendMessage(WebSocketSession session, WebSocketMessage message) {
        try {
            String json = objectMapper.writeValueAsString(message);
            session.sendMessage(new TextMessage(json));
        } catch (IOException e) {
            log.error("发送 WebSocket 消息失败: sessionId={}", session.getId(), e);
        }
    }

    /**
     * 生成模拟气象数据（用于测试）
     */
    private WeatherData generateMockWeatherData(String region) {
        return new WeatherData(
                region,
                25.0 + Math.random() * 10,  // 温度 25-35°C
                40.0 + Math.random() * 40,  // 湿度 40-80%
                2.0 + Math.random() * 8,    // 风速 2-10 m/s
                Math.random() * 360,          // 风向 0-360°
                System.currentTimeMillis()
        );
    }

    /**
     * 获取当前活跃会话数
     */
    public int getActiveSessionCount() {
        return sessions.size();
    }

    /**
     * 获取区域订阅统计
     */
    public Map<String, Integer> getRegionSubscriptionStats() {
        Map<String, Integer> stats = new ConcurrentHashMap<>();
        regionSubscriptions.forEach((region, sessions) -> stats.put(region, sessions.size()));
        return stats;
    }

    // ==================== 内部数据类 ====================

    @lombok.Data
    @lombok.AllArgsConstructor
    @lombok.NoArgsConstructor
    public static class ClientCommand {
        private String action;   // subscribe, unsubscribe, heartbeat, query
        private String region;   // 区域标识
    }

    @lombok.Data
    @lombok.AllArgsConstructor
    @lombok.NoArgsConstructor
    public static class WebSocketMessage {
        private String type;     // connected, weather_data, heartbeat, error, subscribed, unsubscribed
        private String message;
        private Object data;
    }

    @lombok.Data
    @lombok.AllArgsConstructor
    @lombok.NoArgsConstructor
    public static class WeatherData {
        private String region;
        private double temperature;   // 温度 (°C)
        private double humidity;      // 湿度 (%)
        private double windSpeed;     // 风速 (m/s)
        private double windDirection; // 风向 (°)
        private long timestamp;
    }
}
