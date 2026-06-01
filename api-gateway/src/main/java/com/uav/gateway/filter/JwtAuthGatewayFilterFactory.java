package com.uav.gateway.filter;

import com.uav.common.security.JwtTokenProvider;
import io.jsonwebtoken.Claims;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.List;

/**
 * Gateway JWT 认证过滤器工厂。
 * <p>
 * 在网关层统一校验所有请求的 JWT Token，将用户身份透传到下游微服务。
 * 支持白名单路径跳过认证（如 /auth/login, /actuator/health）。
 * </p>
 *
 * 使用方式 (application.yml):
 * <pre>{@code
 * spring:
 *   cloud:
 *     gateway:
 *       routes:
 *         - id: uav-platform
 *           uri: http://uav-platform:8080
 *           predicates:
 *             - Path=/api/**
 *           filters:
 *             - JwtAuth
 * }</pre>
 */
@Slf4j
@Component
public class JwtAuthGatewayFilterFactory
        extends AbstractGatewayFilterFactory<JwtAuthGatewayFilterFactory.Config> {

    private static final String BEARER_PREFIX = "Bearer ";
    private static final List<String> PUBLIC_PATHS = List.of(
            "/api/auth/login", "/api/auth/register",
            "/api/public/", "/actuator/health", "/actuator/info"
    );

    private final JwtTokenProvider jwtTokenProvider;

    public JwtAuthGatewayFilterFactory(JwtTokenProvider jwtTokenProvider) {
        super(Config.class);
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            ServerHttpRequest request = exchange.getRequest();
            String path = request.getURI().getPath();

            // 白名单路径直接放行
            if (isPublicPath(path)) {
                log.debug("JwtAuth: skipping public path [{}]", path);
                return chain.filter(exchange);
            }

            // 从 Authorization Header 提取 Token
            String authHeader = request.getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
            if (authHeader == null || !authHeader.startsWith(BEARER_PREFIX)) {
                log.warn("JwtAuth: missing or invalid Authorization header for [{}]", path);
                return unauthorized(exchange, "Missing or invalid Authorization header");
            }

            String token = authHeader.substring(BEARER_PREFIX.length()).trim();

            // 校验 Token
            try {
                if (!jwtTokenProvider.validateToken(token)) {
                    log.warn("JwtAuth: token validation failed for [{}]", path);
                    return unauthorized(exchange, "Token expired or invalid");
                }

                Claims claims = jwtTokenProvider.validateAndGetClaims(token);
                String username = claims.getSubject();
                String jti = claims.get("jti", String.class);
                @SuppressWarnings("unchecked")
                List<String> roles = claims.get("roles", List.class);
                String tenantId = claims.get("tenant_id", String.class);

                log.debug("JwtAuth: authenticated user [{}] for [{}]", username, path);

                // 将用户身份注入请求头，透传到下游微服务
                ServerHttpRequest mutatedRequest = request.mutate()
                        .header("X-User-Id", username)
                        .header("X-User-Roles", roles != null ? String.join(",", roles) : "")
                        .header("X-Token-Jti", jti)
                        .header("X-Tenant-Id", tenantId != null ? tenantId : "")
                        .build();

                return chain.filter(exchange.mutate().request(mutatedRequest).build());

            } catch (io.jsonwebtoken.ExpiredJwtException e) {
                log.warn("JwtAuth: expired token for [{}]", path);
                return unauthorized(exchange, "Token expired");
            } catch (io.jsonwebtoken.JwtException | IllegalArgumentException e) {
                log.warn("JwtAuth: invalid token for [{}]: {}", path, e.getMessage());
                return unauthorized(exchange, "Invalid token");
            }
        };
    }

    private boolean isPublicPath(String path) {
        return PUBLIC_PATHS.stream().anyMatch(path::startsWith);
    }

    private Mono<Void> unauthorized(ServerWebExchange exchange, String message) {
        exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
        exchange.getResponse().getHeaders().add(HttpHeaders.CONTENT_TYPE, "application/json");
        byte[] body = String.format(
                "{\"code\":401,\"message\":\"%s\",\"timestamp\":%d}",
                message, System.currentTimeMillis()
        ).getBytes(java.nio.charset.StandardCharsets.UTF_8);
        return exchange.getResponse()
                .writeWith(Mono.just(exchange.getResponse().bufferFactory().wrap(body)));
    }

    public static class Config {
        private boolean enabled = true;

        public boolean isEnabled() {
            return enabled;
        }

        public void setEnabled(boolean enabled) {
            this.enabled = enabled;
        }
    }
}
