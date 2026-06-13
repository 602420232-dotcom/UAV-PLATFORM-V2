package com.uav.utm.config;

import com.uav.utm.ws.SubscriptionManager;
import com.uav.utm.ws.UtmWebSocketHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final UtmWebSocketHandler utmWebSocketHandler;

    public WebSocketConfig(UtmWebSocketHandler utmWebSocketHandler) {
        this.utmWebSocketHandler = utmWebSocketHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(utmWebSocketHandler, "/ws/v1/utm")
                .setAllowedOrigins("*");
    }
}
