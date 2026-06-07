package com.uav.common.websocket;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.lang.NonNull;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

@Service
@ConditionalOnClass(name = "org.apache.tomcat.websocket.WsWebSocketContainer")
public class WebSocketPublisher {

    private static final Logger log = LoggerFactory.getLogger(WebSocketPublisher.class);
    private final SimpMessagingTemplate messagingTemplate;

    public WebSocketPublisher(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
        log.info("WebSocketPublisher initialized");
    }

    public void publishWeatherUpdate(@NonNull Object data) {
        WebSocketMessage message = new WebSocketMessage("/topic/weather", data);
        messagingTemplate.convertAndSend("/topic/weather", message);
        log.debug("Published weather update");
    }

    public void publishDroneStatus(@NonNull Object data) {
        WebSocketMessage message = new WebSocketMessage("/topic/drones", data);
        messagingTemplate.convertAndSend("/topic/drones", message);
        log.debug("Published drone status update");
    }

    public void publishTaskUpdate(@NonNull Object data) {
        WebSocketMessage message = new WebSocketMessage("/topic/tasks", data);
        messagingTemplate.convertAndSend("/topic/tasks", message);
        log.debug("Published task update");
    }

    public void publishAlert(@NonNull Object data) {
        WebSocketMessage message = new WebSocketMessage("/topic/alerts", data);
        messagingTemplate.convertAndSend("/topic/alerts", message);
        log.debug("Published alert");
    }

    public void publishPlanningProgress(@NonNull Object data) {
        WebSocketMessage message = new WebSocketMessage("/topic/planning", data);
        messagingTemplate.convertAndSend("/topic/planning", message);
        log.debug("Published planning progress");
    }
}
