package com.uav.weather.websocket;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketTransportRegistration;

/**
 * WebSocket 配置类
 * 配置 STOMP 消息代理、端点、跨域和认证拦截器
 */
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        // 配置内存消息代理，前缀为 /topic 的消息会被广播到所有订阅者
        registry.enableSimpleBroker("/topic", "/queue");

        // 配置客户端发送消息的前缀，以 /app 开头的消息会被路由到 @MessageMapping 注解的方法
        registry.setApplicationDestinationPrefixes("/app");

        // 配置用户点对点消息的前缀
        registry.setUserDestinationPrefix("/user");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // 注册 WebSocket 端点 /ws/weather，客户端通过此端点连接
        registry.addEndpoint("/ws/weather")
                // 允许的跨域来源
                .setAllowedOriginPatterns("*")
                // 启用 SockJS 回退选项（当 WebSocket 不可用时降级为 HTTP 长轮询）
                .withSockJS();

        // 同时注册原生 WebSocket 端点（不通过 SockJS）
        registry.addEndpoint("/ws/weather")
                .setAllowedOriginPatterns("*");
    }

    @Override
    public void configureWebSocketTransport(WebSocketTransportRegistration registration) {
        // 配置消息大小限制：128KB
        registration.setMessageSizeLimit(128 * 1024);
        // 配置发送缓冲区大小限制：512KB
        registration.setSendBufferSizeLimit(512 * 1024);
        // 配置发送超时：20秒
        registration.setSendTimeLimit(20 * 1000);
    }

    // 如果需要更细粒度的控制，可以实现自定义 ChannelInterceptor
    // @Override
    // public void configureClientInboundChannel(ChannelRegistration registration) {
    //     registration.interceptors(webSocketAuthInterceptor);
    // }
}
