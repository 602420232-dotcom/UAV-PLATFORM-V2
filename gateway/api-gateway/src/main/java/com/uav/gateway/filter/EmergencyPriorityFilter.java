package com.uav.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

/**
 * Emergency Priority Filter
 * Identifies emergency requests via X-Emergency-Level header and prioritizes them
 * Order: After ApiVersion, before RateLimit
 */
@Slf4j
@Component
public class EmergencyPriorityFilter implements GlobalFilter, Ordered {

    private static final String EMERGENCY_HEADER = "X-Emergency-Level";
    private static final String EMERGENCY_CRITICAL = "CRITICAL";
    private static final String EMERGENCY_ATTR = "emergencyLevel";
    private static final String PRIORITY_ATTR = "priority";

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String requestId = request.getHeaders().getFirst("X-Request-ID");
        String emergencyLevel = request.getHeaders().getFirst(EMERGENCY_HEADER);

        boolean isEmergency = EMERGENCY_CRITICAL.equalsIgnoreCase(emergencyLevel);

        exchange.getAttributes().put(EMERGENCY_ATTR, emergencyLevel != null ? emergencyLevel : "NORMAL");
        exchange.getAttributes().put(PRIORITY_ATTR, isEmergency ? 100 : 0);

        if (isEmergency) {
            log.warn("[EMERGENCY] CRITICAL request detected! id={} | path={} | level={}",
                    requestId, request.getURI().getPath(), emergencyLevel);

            // Add emergency markers to downstream request
            ServerHttpRequest mutatedRequest = request.mutate()
                    .header("X-Priority", "CRITICAL")
                    .header("X-Queue-Priority", "HIGH")
                    .build();

            return chain.filter(exchange.mutate().request(mutatedRequest).build());
        }

        log.debug("[EMERGENCY] Normal request id={} | level={}", requestId,
                emergencyLevel != null ? emergencyLevel : "NORMAL");
        return chain.filter(exchange);
    }

    @Override
    public int getOrder() {
        // After ApiVersion (HIGHEST+20), before RateLimit
        return Ordered.HIGHEST_PRECEDENCE + 30;
    }
}
