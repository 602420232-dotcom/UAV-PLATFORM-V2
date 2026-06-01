package com.uav.common.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * JWT Token 生成和校验工具。
 * 配合 {@link JwtAuthenticationFilter} 使用。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtTokenProvider {

    private final JwtProperties jwtProperties;

    private SecretKey getKey() {
        return Keys.hmacShaKeyFor(jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8));
    }

    /**
     * 生成访问 Token
     */
    public String generateToken(String username, List<String> roles) {
        return generateToken(username, roles, null);
    }

    /**
     * 生成访问 Token（包含租户 ID）
     */
    public String generateToken(String username, List<String> roles, String tenantId) {
        Date now = new Date();
        return Jwts.builder()
                .setSubject(username)
                .claim("roles", roles)
                .claim("tenant_id", tenantId)
                .claim("jti", UUID.randomUUID().toString())
                .setIssuedAt(now)
                .setExpiration(new Date(now.getTime() + jwtProperties.getExpirationMs()))
                .signWith(getKey(), SignatureAlgorithm.HS256)
                .compact();
    }

    /**
     * 生成刷新 Token (更长有效期)
     */
    public String generateRefreshToken(String username) {
        Date now = new Date();
        return Jwts.builder()
                .setSubject(username)
                .claim("jti", UUID.randomUUID().toString())
                .setIssuedAt(now)
                .setExpiration(new Date(now.getTime() + jwtProperties.getRefreshExpirationMs()))
                .signWith(getKey(), SignatureAlgorithm.HS256)
                .compact();
    }

    /**
     * 刷新访问 Token
     */
    public String refreshAccessToken(String refreshToken) {
        try {
            Claims claims = validateAndGetClaims(refreshToken);
            String username = claims.getSubject();
            @SuppressWarnings("unchecked")
            List<String> roles = claims.get("roles", List.class);
            String tenantId = claims.get("tenant_id", String.class);
            if (roles == null || roles.isEmpty()) {
                roles = List.of("user");
            }
            return generateToken(username, roles, tenantId);
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid refresh token", e);
        }
    }

    /**
     * 验证 Token 并获取 Claims
     */
    public Claims validateAndGetClaims(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(getKey())
                .build()
                .parseClaimsJws(token)
                .getBody();
    }

    /**
     * 从 Token 中提取用户名
     */
    public String extractUsername(String token) {
        Claims claims = validateAndGetClaims(token);
        return claims.getSubject();
    }

    /**
     * 从 Token 中提取租户 ID
     */
    public String extractTenantId(String token) {
        Claims claims = validateAndGetClaims(token);
        return claims.get("tenant_id", String.class);
    }

    /**
     * 从 Token 中提取 JTI (Token ID)
     */
    public String extractJti(String token) {
        Claims claims = validateAndGetClaims(token);
        return claims.get("jti", String.class);
    }

    /**
     * 从 Token 中提取过期时间
     */
    public Date extractExpiration(String token) {
        Claims claims = validateAndGetClaims(token);
        return claims.getExpiration();
    }

    /**
     * 检查 Token 是否过期
     */
    public boolean isTokenExpired(String token) {
        try {
            Date expiration = extractExpiration(token);
            return expiration.before(new Date());
        } catch (Exception e) {
            log.warn("Failed to check token expiration: {}", e.getMessage());
            return true;
        }
    }

    /**
     * 从 Token 中提取角色
     */
    @SuppressWarnings("unchecked")
    public List<String> extractRoles(String token) {
        Claims claims = validateAndGetClaims(token);
        List<String> roles = claims.get("roles", List.class);
        return roles != null ? roles : List.of();
    }

    /**
     * 验证 Token 是否有效
     */
    public boolean validateToken(String token) {
        try {
            validateAndGetClaims(token);
            return !isTokenExpired(token);
        } catch (Exception e) {
            log.warn("Token validation failed: {}", e.getMessage());
            return false;
        }
    }
}
