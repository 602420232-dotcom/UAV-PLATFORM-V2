package com.uav.gateway.handler;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

@Component
public class RateLimitHandler {

    private final ObjectMapper objectMapper;

    public RateLimitHandler(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public Mono<Void> handle(ServerWebExchange exchange) {
        exchange.getResponse().setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
        exchange.getResponse().getHeaders().setContentType(MediaType.APPLICATION_JSON);
        
        Map<String, Object> body = new HashMap<>();
        body.put("code", 429);
        body.put("message", "请求过于频繁，请稍后重试");
        body.put("timestamp", LocalDateTime.now().toString());
        body.put("retry-after", 60);
        
        final byte[] bytes = Objects.requireNonNull(toJsonBytes(body));
        final DataBuffer buffer = Objects.requireNonNull(
            exchange.getResponse().bufferFactory().wrap(bytes));
        return exchange.getResponse().writeWith(Objects.requireNonNull(Mono.just(buffer)));
    }

    private byte[] toJsonBytes(Map<String, Object> body) {
        try {
            return objectMapper.writeValueAsBytes(body);
        } catch (JsonProcessingException e) {
            return "{\"code\":429,\"message\":\"Rate limit exceeded\"}".getBytes(StandardCharsets.UTF_8);
        }
    }
}