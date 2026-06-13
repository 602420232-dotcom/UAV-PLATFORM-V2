package com.uav.utm.ws;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import java.io.IOException;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArraySet;

/**
 * WebSocket 订阅管理器
 * <p>
 * 管理客户端订阅的频道，支持按频道广播消息。
 * <p>
 * 频道格式:
 * <ul>
 *   <li>{@code uav:{uavId}} — 订阅某个 UAV 的位置更新</li>
 *   <li>{@code area:{minLon},{minLat},{maxLon},{maxLat}} — 订阅某个区域的冲突告警</li>
 *   <li>{@code alerts} — 订阅全局告警</li>
 * </ul>
 */
@Slf4j
@Component
public class SubscriptionManager {

    private final ConcurrentHashMap<String, Set<WebSocketSession>> channelSubscriptions = new ConcurrentHashMap<>();

    /** session -> 订阅的频道集合（反向索引） */
    private final ConcurrentHashMap<String, Set<String>> sessionChannels = new ConcurrentHashMap<>();

    private final ObjectMapper objectMapper;

    public SubscriptionManager(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    /**
     * 订阅频道
     *
     * @param channel 频道名称
     * @param session WebSocket 会话
     */
    public void subscribe(String channel, WebSocketSession session) {
        channelSubscriptions.computeIfAbsent(channel, k -> new CopyOnWriteArraySet<>()).add(session);
        sessionChannels.computeIfAbsent(session.getId(), k -> new CopyOnWriteArraySet<>()).add(channel);
        log.info("Session {} 订阅了频道: {}", session.getId(), channel);
    }

    /**
     * 取消订阅频道
     *
     * @param channel 频道名称
     * @param session WebSocket 会话
     */
    public void unsubscribe(String channel, WebSocketSession session) {
        Set<WebSocketSession> sessions = channelSubscriptions.get(channel);
        if (sessions != null) {
            sessions.remove(session);
            if (sessions.isEmpty()) {
                channelSubscriptions.remove(channel);
            }
        }
        Set<String> channels = sessionChannels.get(session.getId());
        if (channels != null) {
            channels.remove(channel);
            if (channels.isEmpty()) {
                sessionChannels.remove(session.getId());
            }
        }
        log.info("Session {} 取消订阅频道: {}", session.getId(), channel);
    }

    /**
     * 向频道广播消息
     *
     * @param channel 频道名称
     * @param message 消息对象（将序列化为 JSON）
     */
    public void broadcastToChannel(String channel, Object message) {
        Set<WebSocketSession> sessions = channelSubscriptions.get(channel);
        if (sessions == null || sessions.isEmpty()) {
            return;
        }

        try {
            String json;
            if (message instanceof String) {
                json = (String) message;
            } else {
                json = objectMapper.writeValueAsString(message);
            }
            TextMessage textMessage = new TextMessage(json);

            for (WebSocketSession session : sessions) {
                if (session.isOpen()) {
                    try {
                        session.sendMessage(textMessage);
                    } catch (IOException e) {
                        log.error("向频道 {} 的 session {} 发送消息失败", channel, session.getId(), e);
                    }
                }
            }
        } catch (Exception e) {
            log.error("广播消息到频道 {} 失败", channel, e);
        }
    }

    /**
     * 获取指定 session 订阅的所有频道
     *
     * @param session WebSocket 会话
     * @return 频道集合
     */
    public Set<String> getSubscriptions(WebSocketSession session) {
        return sessionChannels.getOrDefault(session.getId(), Set.of());
    }

    /**
     * 根据 sessionId 获取订阅的频道
     *
     * @param sessionId 会话ID
     * @return 频道集合
     */
    public Set<String> getSubscriptionsById(String sessionId) {
        return sessionChannels.getOrDefault(sessionId, Set.of());
    }

    /**
     * 移除 session 的所有订阅（连接关闭时调用）
     *
     * @param session WebSocket 会话
     */
    public void removeAllSubscriptions(WebSocketSession session) {
        Set<String> channels = sessionChannels.remove(session.getId());
        if (channels != null) {
            for (String channel : channels) {
                Set<WebSocketSession> sessions = channelSubscriptions.get(channel);
                if (sessions != null) {
                    sessions.remove(session);
                    if (sessions.isEmpty()) {
                        channelSubscriptions.remove(channel);
                    }
                }
            }
            log.info("Session {} 的所有订阅已清理, 共 {} 个频道", session.getId(), channels.size());
        }
    }

    /**
     * 获取当前所有活跃频道
     *
     * @return 频道名称集合
     */
    public Set<String> getActiveChannels() {
        return Set.copyOf(channelSubscriptions.keySet());
    }

    /**
     * 获取指定频道的订阅者数量
     *
     * @param channel 频道名称
     * @return 订阅者数量
     */
    public int getSubscriberCount(String channel) {
        Set<WebSocketSession> sessions = channelSubscriptions.get(channel);
        return sessions != null ? sessions.size() : 0;
    }
}
