package com.uav.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * API Version Filter
 * Parses URL major version, header minor version, and routes to gray-scale instances
 * Order: After UtmCallback, before EmergencyPriority
 */
@Slf4j
@Component
public class ApiVersionFilter implements GlobalFilter, Ordered {

    private static final Pattern VERSION_PATTERN = Pattern.compile("/api/v(\\d+)/");
    private static final String API_VERSION_HEADER = "X-API-Version";
    private static final String GRAY_VERSION_HEADER = "X-Gray-Version";
    private static final String VERSION_ATTR = "apiVersion";

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();
        String requestId = request.getHeaders().getFirst("X-Request-ID");

        // Parse major version from URL path
        String majorVersion = extractMajorVersion(path);

        // Parse minor version from header
        String minorVersion = request.getHeaders().getFirst(API_VERSION_HEADER);
        if (minorVersion == null || minorVersion.isEmpty()) {
            minorVersion = "0";
        }

        String fullVersion = majorVersion + "." + minorVersion;
        exchange.getAttributes().put(VERSION_ATTR, fullVersion);

        // Check for gray-scale routing
        String grayVersion = request.getHeaders().getFirst(GRAY_VERSION_HEADER);
        boolean isGray = isGrayRoute(grayVersion, fullVersion);

        log.info("[VERSION] id={} | path={} | major={} | minor={} | full={} | gray={}",
                requestId, path, majorVersion, minorVersion, fullVersion, isGray);

        // Add version headers to downstream request
        ServerHttpRequest mutatedRequest = request.mutate()
                .header("X-API-Major-Version", majorVersion)
                .header("X-API-Minor-Version", minorVersion)
                .header("X-API-Full-Version", fullVersion)
                .header("X-Gray-Route", String.valueOf(isGray))
                .build();

        return chain.filter(exchange.mutate().request(mutatedRequest).build());
    }

    private String extractMajorVersion(String path) {
        Matcher matcher = VERSION_PATTERN.matcher(path);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return "1"; // Default version
    }

    private boolean isGrayRoute(String grayVersion, String currentVersion) {
        if (grayVersion == null || grayVersion.isEmpty()) {
            return false;
        }
        // Simple gray-scale logic: if header version matches current version
        return grayVersion.equals(currentVersion);
    }

    @Override
    public int getOrder() {
        // After UtmCallback (HIGHEST+10), before EmergencyPriority
        return Ordered.HIGHEST_PRECEDENCE + 20;
    }
}
