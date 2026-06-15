package com.uav.gateway.filter;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

/**
 * V1 JWT Token Convert Filter
 * Converts V1 format JWT tokens to V2 format for backward compatibility during migration.
 *
 * <p>V1 Token characteristics:
 * <ul>
 *   <li>Issuer claim: "iss": "uav-platform-v1"</li>
 *   <li>User ID claim: "user_id" (V1) vs "sub" (V2)</li>
 *   <li>Role claim: "roles" (V1) vs "authorities" (V2)</li>
 * </ul>
 *
 * <p>Execution order: HIGHEST_PRECEDENCE + 5 (after RequestLog, before ApiVersion)</p>
 */
@Slf4j
@Component
public class V1JwtConvertFilter implements GlobalFilter, Ordered {

    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    // V1 Token characteristics
    private static final String V1_ISSUER = "uav-platform-v1";
    private static final String V1_USER_ID_CLAIM = "user_id";
    private static final String V1_ROLES_CLAIM = "roles";

    // V2 Token characteristics
    private static final String V2_ISSUER = "uav-platform-v2";
    private static final String V2_AUTHORITIES_CLAIM = "authorities";

    // Exchange attribute key for converted token
    public static final String CONVERTED_TOKEN_ATTR = "convertedJwtToken";
    public static final String TOKEN_VERSION_ATTR = "jwtTokenVersion";

    private final SecretKey v1SecretKey;
    private final SecretKey v2SecretKey;

    public V1JwtConvertFilter(
            @Value("${gateway.v1.jwt.secret:}") String v1Secret,
            @Value("${gateway.v2.jwt.secret:}") String v2Secret) {
        if (!StringUtils.hasText(v1Secret)) {
            log.warn("[JWT-CONVERT] V1 JWT secret not configured (gateway.v1.jwt.secret), V1 token conversion will be disabled");
        }
        if (!StringUtils.hasText(v2Secret)) {
            throw new IllegalArgumentException("V2 JWT secret must be configured via gateway.v2.jwt.secret");
        }
        this.v1SecretKey = StringUtils.hasText(v1Secret) ? deriveKey(v1Secret) : null;
        this.v2SecretKey = deriveKey(v2Secret);
    }

    private SecretKey deriveKey(String secret) {
        // Ensure key is at least 32 bytes for HS256
        String effectiveSecret = secret;
        if (effectiveSecret.getBytes(StandardCharsets.UTF_8).length < 32) {
            effectiveSecret = String.format("%-32s", effectiveSecret).replace(' ', '0');
        }
        return Keys.hmacShaKeyFor(effectiveSecret.getBytes(StandardCharsets.UTF_8));
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String requestId = request.getHeaders().getFirst("X-Request-ID");
        String authHeader = request.getHeaders().getFirst(AUTHORIZATION_HEADER);

        // No token, pass through (may be public endpoint)
        if (!StringUtils.hasText(authHeader) || !authHeader.startsWith(BEARER_PREFIX)) {
            log.debug("[JWT-CONVERT] No Bearer token found, passing through | id={}", requestId);
            return chain.filter(exchange);
        }

        String token = authHeader.substring(BEARER_PREFIX.length());

        // Try to determine token version and convert if needed
        return processToken(exchange, chain, token, requestId);
    }

    private Mono<Void> processToken(ServerWebExchange exchange, GatewayFilterChain chain,
                                     String token, String requestId) {
        try {
            // First, try to parse as V2 token
            if (isV2Token(token)) {
                log.debug("[JWT-CONVERT] V2 token detected, passing through | id={}", requestId);
                exchange.getAttributes().put(TOKEN_VERSION_ATTR, "v2");
                return chain.filter(exchange);
            }

            // Try to parse as V1 token
            if (isV1Token(token)) {
                log.info("[JWT-CONVERT] V1 token detected, converting to V2 | id={}", requestId);
                String convertedToken = convertV1ToV2(token);

                // Store converted token in attribute for other filters
                exchange.getAttributes().put(CONVERTED_TOKEN_ATTR, convertedToken);
                exchange.getAttributes().put(TOKEN_VERSION_ATTR, "v1-converted");

                // Mutate request with new token
                ServerHttpRequest mutatedRequest = exchange.getRequest().mutate()
                        .header(AUTHORIZATION_HEADER, BEARER_PREFIX + convertedToken)
                        .header("X-Token-Converted", "true")
                        .header("X-Original-Token-Version", "v1")
                        .build();

                return chain.filter(exchange.mutate().request(mutatedRequest).build());
            }

            // Unknown token format
            log.warn("[JWT-CONVERT] Unknown token format, rejecting | id={}", requestId);
            return reject(exchange, HttpStatus.UNAUTHORIZED, "Invalid token format");

        } catch (JwtException e) {
            log.warn("[JWT-CONVERT] Invalid token, rejecting | id={} | error={}", requestId, e.getMessage());
            return reject(exchange, HttpStatus.UNAUTHORIZED, "Invalid or expired token");
        } catch (Exception e) {
            log.error("[JWT-CONVERT] Unexpected error processing token | id={}", requestId, e);
            return reject(exchange, HttpStatus.UNAUTHORIZED, "Token processing error");
        }
    }

    /**
     * Check if token is V2 format by attempting to verify with V2 key
     */
    private boolean isV2Token(String token) {
        try {
            Jws<Claims> claims = Jwts.parser()
                    .verifyWith(v2SecretKey)
                    .build()
                    .parseSignedClaims(token);
            String issuer = claims.getPayload().getIssuer();
            return V2_ISSUER.equals(issuer) || claims.getPayload().containsKey(V2_AUTHORITIES_CLAIM);
        } catch (JwtException e) {
            return false;
        }
    }

    /**
     * Check if token is V1 format by attempting to verify with V1 key
     */
    private boolean isV1Token(String token) {
        if (v1SecretKey == null) {
            return false;
        }
        try {
            Jws<Claims> claims = Jwts.parser()
                    .verifyWith(v1SecretKey)
                    .build()
                    .parseSignedClaims(token);
            String issuer = claims.getPayload().getIssuer();
            return V1_ISSUER.equals(issuer) || claims.getPayload().containsKey(V1_USER_ID_CLAIM);
        } catch (JwtException e) {
            return false;
        }
    }

    /**
     * Convert V1 token to V2 format
     */
    private String convertV1ToV2(String v1Token) {
        Jws<Claims> v1Claims = Jwts.parser()
                .verifyWith(v1SecretKey)
                .build()
                .parseSignedClaims(v1Token);

        Claims body = v1Claims.getPayload();

        // Extract V1 claims
        String userId = String.valueOf(body.get(V1_USER_ID_CLAIM));
        @SuppressWarnings("unchecked")
        List<String> roles = body.get(V1_ROLES_CLAIM, List.class);

        // Build V2 claims
        Date now = new Date();
        Date expiration = body.getExpiration();
        Date issuedAt = body.getIssuedAt();

        // If no expiration in V1, set default 24 hours
        if (expiration == null) {
            expiration = new Date(now.getTime() + 86400000);
        }
        if (issuedAt == null) {
            issuedAt = now;
        }

        // Convert roles to authorities format
        List<String> authorities = roles != null
                ? roles.stream().map(r -> "ROLE_" + r.toUpperCase()).collect(Collectors.toList())
                : List.of("ROLE_USER");

        return Jwts.builder()
                .subject(userId)
                .issuer(V2_ISSUER)
                .issuedAt(issuedAt)
                .expiration(expiration)
                .claim(V2_AUTHORITIES_CLAIM, authorities)
                // Preserve other V1 claims that may be needed
                .claim("original_iss", body.getIssuer())
                .claim("converted_at", now.getTime())
                .signWith(v2SecretKey)
                .compact();
    }

    private Mono<Void> reject(ServerWebExchange exchange, HttpStatus status, String message) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(status);
        response.getHeaders().add("Content-Type", "application/json");
        String body = String.format("{\"code\":%d,\"message\":\"%s\"}", status.value(), message);
        DataBuffer buffer = response.bufferFactory().wrap(body.getBytes(StandardCharsets.UTF_8));
        return response.writeWith(Mono.just(buffer));
    }

    @Override
    public int getOrder() {
        // After RequestLog (HIGHEST), before ApiVersion (HIGHEST+20)
        // Must execute before any authentication filter
        return Ordered.HIGHEST_PRECEDENCE + 5;
    }
}
