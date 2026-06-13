package com.uav.gateway.filter;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.data.redis.core.ReactiveStringRedisTemplate;
import org.springframework.data.redis.core.script.RedisScript;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 * Rate Limit Filter
 * Implements rate limiting using Redis + Lua script
 * Supports: Tenant QPS, API Key QPS, WebSocket connection count
 * Order: After EmergencyPriority (last filter)
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class RateLimitFilter implements GlobalFilter, Ordered {

    private final ReactiveStringRedisTemplate redisTemplate;

    // Lua script for sliding window rate limiting
    private static final String RATE_LIMIT_LUA =
            "local key = KEYS[1]\n" +
            "local limit = tonumber(ARGV[1])\n" +
            "local window = tonumber(ARGV[2])\n" +
            "local now = tonumber(ARGV[3])\n" +
            "\n" +
            "redis.call('ZREMRANGEBYSCORE', key, 0, now - window)\n" +
            "local current = redis.call('ZCARD', key)\n" +
            "\n" +
            "if current >= limit then\n" +
            "    return {0, current}\n" +
            "end\n" +
            "\n" +
            "redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))\n" +
            "redis.call('EXPIRE', key, window)\n" +
            "return {1, current + 1}\n";

    private static final RedisScript<List<Long>> RATE_LIMIT_SCRIPT = RedisScript.of(
            RATE_LIMIT_LUA,
            (Class<List<Long>>) (Class<?>) List.class
    );

    private static final String TENANT_HEADER = "X-Tenant-ID";
    private static final String API_KEY_HEADER = "X-API-Key";
    private static final String WS_PATH_PREFIX = "/ws/";

    // Default limits
    private static final long DEFAULT_TENANT_QPS = 1000;
    private static final long DEFAULT_API_KEY_QPS = 100;
    private static final long DEFAULT_WS_CONNECTIONS = 50;
    private static final long WINDOW_SECONDS = 1;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String requestId = request.getHeaders().getFirst("X-Request-ID");
        String path = request.getURI().getPath();

        // Skip rate limiting for emergency requests
        String emergencyLevel = exchange.getAttributeOrDefault("emergencyLevel", "NORMAL");
        if ("CRITICAL".equals(emergencyLevel)) {
            log.info("[RATE-LIMIT] Skipping rate limit for emergency request id={}", requestId);
            return chain.filter(exchange);
        }

        // Determine rate limit type and key
        String tenantId = request.getHeaders().getFirst(TENANT_HEADER);
        String apiKey = request.getHeaders().getFirst(API_KEY_HEADER);
        boolean isWebSocket = path.startsWith(WS_PATH_PREFIX);

        if (isWebSocket) {
            return checkWebSocketLimit(exchange, chain, requestId, tenantId);
        }

        // Check API Key limit first (more specific)
        if (StringUtils.hasText(apiKey)) {
            return checkRateLimit(exchange, chain, "apikey:" + apiKey, DEFAULT_API_KEY_QPS, requestId, "API_KEY");
        }

        // Check Tenant limit
        if (StringUtils.hasText(tenantId)) {
            return checkRateLimit(exchange, chain, "tenant:" + tenantId, DEFAULT_TENANT_QPS, requestId, "TENANT");
        }

        // No identity found, allow with a very low default limit
        return checkRateLimit(exchange, chain, "anonymous:" + getClientIp(request), 10, requestId, "ANONYMOUS");
    }

    private Mono<Void> checkRateLimit(ServerWebExchange exchange, GatewayFilterChain chain,
                                       String key, long limit, String requestId, String type) {
        long now = Instant.now().toEpochMilli();
        long windowMs = WINDOW_SECONDS * 1000;

        List<String> keys = Collections.singletonList("ratelimit:" + key);
        List<String> args = Arrays.asList(
                String.valueOf(limit),
                String.valueOf(windowMs),
                String.valueOf(now)
        );

        return redisTemplate.execute(RATE_LIMIT_SCRIPT, keys, args)
                .next()
                .flatMap(result -> {
                    boolean allowed = result.get(0) == 1;
                    long current = result.get(1);

                    // Add rate limit headers
                    exchange.getResponse().getHeaders().add("X-RateLimit-Limit", String.valueOf(limit));
                    exchange.getResponse().getHeaders().add("X-RateLimit-Remaining", String.valueOf(Math.max(0, limit - current)));
                    exchange.getResponse().getHeaders().add("X-RateLimit-Reset", String.valueOf(now + windowMs));

                    if (allowed) {
                        log.debug("[RATE-LIMIT] Allowed {} | id={} | key={} | current={}/{}",
                                type, requestId, key, current, limit);
                        return chain.filter(exchange);
                    } else {
                        log.warn("[RATE-LIMIT] BLOCKED {} | id={} | key={} | current={}/{}",
                                type, requestId, key, current, limit);
                        return reject(exchange, HttpStatus.TOO_MANY_REQUESTS,
                                "Rate limit exceeded: " + type + " limit=" + limit);
                    }
                })
                .onErrorResume(e -> {
                    log.error("[RATE-LIMIT] Redis error, allowing request id={}", requestId, e);
                    return chain.filter(exchange);
                });
    }

    private Mono<Void> checkWebSocketLimit(ServerWebExchange exchange, GatewayFilterChain chain,
                                            String requestId, String tenantId) {
        String wsKey = "ws:" + (StringUtils.hasText(tenantId) ? tenantId : "anonymous");

        return redisTemplate.opsForValue()
                .increment(wsKey)
                .flatMap(count -> {
                    // Set expiry if this is the first connection
                    if (count == 1) {
                        return redisTemplate.expire(wsKey, java.time.Duration.ofHours(1))
                                .thenReturn(count);
                    }
                    return Mono.just(count);
                })
                .flatMap(count -> {
                    if (count > DEFAULT_WS_CONNECTIONS) {
                        log.warn("[RATE-LIMIT] WS connection limit exceeded id={} | count={}", requestId, count);
                        return reject(exchange, HttpStatus.TOO_MANY_REQUESTS,
                                "WebSocket connection limit exceeded");
                    }
                    log.debug("[RATE-LIMIT] WS connection allowed id={} | count={}/{}",
                            requestId, count, DEFAULT_WS_CONNECTIONS);
                    return chain.filter(exchange);
                })
                .onErrorResume(e -> {
                    log.error("[RATE-LIMIT] WS Redis error, allowing request id={}", requestId, e);
                    return chain.filter(exchange);
                });
    }

    private String getClientIp(ServerHttpRequest request) {
        String ip = request.getHeaders().getFirst("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddress() != null
                    ? request.getRemoteAddress().getAddress().getHostAddress()
                    : "unknown";
        }
        return ip.split(",")[0].trim();
    }

    private Mono<Void> reject(ServerWebExchange exchange, HttpStatus status, String message) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(status);
        response.getHeaders().add("Content-Type", "application/json");
        String body = String.format("{\"code\":429,\"message\":\"%s\"}", message);
        DataBuffer buffer = response.bufferFactory().wrap(body.getBytes(StandardCharsets.UTF_8));
        return response.writeWith(Mono.just(buffer));
    }

    @Override
    public int getOrder() {
        // After EmergencyPriority (HIGHEST+30), last filter
        return Ordered.HIGHEST_PRECEDENCE + 40;
    }
}
