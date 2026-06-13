package com.uav.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.UUID;

/**
 * Request Log Filter
 * Logs all incoming requests with timing and trace information
 * Order: HIGHEST (executes first)
 */
@Slf4j
@Component
public class RequestLogFilter implements GlobalFilter, Ordered {

    private static final String REQUEST_START_TIME = "requestStartTime";
    private static final String REQUEST_ID = "X-Request-ID";

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String requestId = UUID.randomUUID().toString().replace("-", "");
        
        // Add request ID to exchange attributes and response headers
        exchange.getAttributes().put(REQUEST_START_TIME, Instant.now().toEpochMilli());
        exchange.getAttributes().put(REQUEST_ID, requestId);

        ServerHttpRequest mutatedRequest = request.mutate()
                .header(REQUEST_ID, requestId)
                .build();

        String method = request.getMethod().name();
        String path = request.getURI().getPath();
        String clientIp = getClientIp(request);
        String userAgent = request.getHeaders().getFirst("User-Agent");

        log.info("[REQUEST] id={} | method={} | path={} | clientIp={} | userAgent={}",
                requestId, method, path, clientIp, userAgent);

        return chain.filter(exchange.mutate().request(mutatedRequest).build())
                .doFinally(signalType -> {
                    long startTime = exchange.getAttributeOrDefault(REQUEST_START_TIME, 0L);
                    long duration = Instant.now().toEpochMilli() - startTime;
                    int statusCode = exchange.getResponse().getStatusCode() != null
                            ? exchange.getResponse().getStatusCode().value() : 0;

                    log.info("[RESPONSE] id={} | status={} | duration={}ms | signal={}",
                            requestId, statusCode, duration, signalType);
                });
    }

    private String getClientIp(ServerHttpRequest request) {
        String ip = request.getHeaders().getFirst("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getHeaders().getFirst("X-Real-IP");
        }
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddress() != null
                    ? request.getRemoteAddress().getAddress().getHostAddress()
                    : "unknown";
        }
        return ip.split(",")[0].trim();
    }

    @Override
    public int getOrder() {
        // Highest priority - execute first
        return Ordered.HIGHEST_PRECEDENCE;
    }
}
