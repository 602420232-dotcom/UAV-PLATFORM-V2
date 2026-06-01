package com.uav.common.security;

import io.jsonwebtoken.Claims;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.util.Date;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * JWT 认证过滤器
 * 支持 Token 黑名单检查（通过 Redis，可选依赖）
 */
@Slf4j
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String BLACKLIST_KEY_PREFIX = "blacklist:token:";

    private final JwtTokenProvider jwtTokenProvider;
    private final JwtProperties jwtProperties;
    private final Optional<RedisTemplate<String, String>> redisTemplate;

    @Autowired
    public JwtAuthenticationFilter(JwtTokenProvider jwtTokenProvider,
                                    JwtProperties jwtProperties,
                                    Optional<RedisTemplate<String, String>> redisTemplate) {
        this.jwtTokenProvider = jwtTokenProvider;
        this.jwtProperties = jwtProperties;
        this.redisTemplate = redisTemplate;
    }

    @PostConstruct
    public void validateConfig() {
        String profile = getActiveProfile();
        boolean isProduction = "prod".equals(profile) || "production".equals(profile);

        if (!jwtProperties.isEnabled() && isProduction) {
            throw new IllegalStateException(
                "JWT 认证在生产环境不可禁用。请设置 jwt.enabled=true 并配置 jwt.secret");
        }

        if (jwtProperties.isEnabled()) {
            if (jwtProperties.getSecret() == null || jwtProperties.getSecret().isEmpty()) {
                throw new IllegalStateException(
                    "JWT secret is NOT configured. Set JWT_SECRET environment variable or jwt.secret in application.yml");
            }
            if (jwtProperties.getSecret().length() < 32) {
                throw new IllegalStateException(
                    "JWT secret is too short (minimum 32 chars required, got " + jwtProperties.getSecret().length() + ")");
            }
        }
    }

    private String getActiveProfile() {
        return System.getenv("SPRING_PROFILES_ACTIVE");
    }

    @Override
    @SuppressWarnings("unchecked")
    protected void doFilterInternal(@NonNull HttpServletRequest request,
                                    @NonNull HttpServletResponse response,
                                    @NonNull FilterChain filterChain) throws ServletException, IOException {
        if (!jwtProperties.isEnabled() || isPublicPath(request.getRequestURI())) {
            filterChain.doFilter(request, response);
            return;
        }

        String header = request.getHeader(jwtProperties.getHeader());
        if (header == null || !header.startsWith(jwtProperties.getTokenPrefix())) {
            sendUnauthorized(response, "Missing or invalid Authorization header");
            return;
        }

        String token = header.substring(jwtProperties.getTokenPrefix().length());

        try {
            // 检查 Token 是否在黑名单中
            if (isTokenBlacklisted(token)) {
                log.warn("Token is in blacklist");
                sendUnauthorized(response, "Token has been revoked");
                return;
            }

            // 验证 Token 并获取 Claims
            Claims claims = jwtTokenProvider.validateAndGetClaims(token);

            // 提取用户信息
            String username = claims.getSubject();
            String tenantId = claims.get("tenant_id", String.class);
            List<String> roles = claims.get("roles", List.class);
            if (roles == null) {
                roles = List.of();
            }
            List<SimpleGrantedAuthority> authorities = roles.stream()
                    .map(SimpleGrantedAuthority::new)
                    .collect(Collectors.toList());

            // 创建认证对象（包含租户 ID）
            UsernamePasswordAuthenticationToken auth =
                    new UsernamePasswordAuthenticationToken(username, tenantId, authorities);
            auth.setDetails(tenantId);
            SecurityContextHolder.getContext().setAuthentication(auth);

        } catch (Exception e) {
            log.warn("JWT verification failed: {}", e.getMessage());
            sendUnauthorized(response, "Invalid token");
            return;
        }

        filterChain.doFilter(request, response);
    }

    /**
     * 检查 Token 是否在黑名单中
     */
    private boolean isTokenBlacklisted(String token) {
        return redisTemplate.map(template -> {
            try {
                String jti = jwtTokenProvider.extractJti(token);
                String blacklistKey = BLACKLIST_KEY_PREFIX + jti;
                return Boolean.TRUE.equals(template.hasKey(blacklistKey));
            } catch (Exception e) {
                log.warn("Failed to check token blacklist: {}", e.getMessage());
                return false;
            }
        }).orElse(false);
    }

    /**
     * 将 Token 加入黑名单
     */
    public void blacklistToken(String token) {
        redisTemplate.ifPresent(template -> {
            try {
                String jti = jwtTokenProvider.extractJti(token);
                Date expiration = jwtTokenProvider.extractExpiration(token);
                long ttl = expiration.getTime() - System.currentTimeMillis();

                if (ttl > 0) {
                    String blacklistKey = BLACKLIST_KEY_PREFIX + jti;
                    template.opsForValue().set(blacklistKey, "1", ttl, TimeUnit.MILLISECONDS);
                    log.info("Token added to blacklist: jti={}", jti);
                }
            } catch (Exception e) {
                log.error("Failed to blacklist token: {}", e.getMessage());
            }
        });
    }

    /**
     * 发送未授权响应
     */
    private void sendUnauthorized(HttpServletResponse response, String message) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":401,\"message\":\"" + message + "\"}");
    }

    /**
     * 检查是否为公开路径
     */
    private boolean isPublicPath(String uri) {
        return uri.equals("/actuator/health") || uri.equals("/actuator/info")
                || uri.startsWith("/api/public/") || uri.startsWith("/api/auth/")
                || uri.startsWith("/api/v1/auth/");
    }
}
