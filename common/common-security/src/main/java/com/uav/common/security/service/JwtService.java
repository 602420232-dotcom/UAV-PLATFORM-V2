package com.uav.common.security.service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.UnsupportedJwtException;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SignatureException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

/**
 * JWT 生成与验证服务
 * <p>
 * 基于 JJWT 0.12.6，支持 token 生成、解析、校验、刷新。
 * Access Token 有效期 30 分钟，Refresh Token 有效期 7 天。
 */
@Slf4j
@Service
public class JwtService {

    @Value("${security.jwt.secret}")
    private String jwtSecret;

    /** Access Token 过期时间：30 分钟（1800000ms） */
    @Value("${security.jwt.expiration:1800000}")
    private long jwtExpirationMs;

    /** Refresh Token 过期时间：7 天（604800000ms） */
    @Value("${security.jwt.refresh-expiration:604800000}")
    private long jwtRefreshExpirationMs;

    @Value("${security.jwt.issuer:uav-platform}")
    private String issuer;

    private static final String CLAIM_TOKEN_TYPE = "token_type";
    private static final String TOKEN_TYPE_ACCESS = "access";
    private static final String TOKEN_TYPE_REFRESH = "refresh";

    /**
     * 从 token 中提取用户名（subject）
     *
     * @param token JWT token
     * @return 用户名
     */
    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    /**
     * 从 token 中提取指定声明
     *
     * @param <T>            声明值类型
     * @param token          JWT token
     * @param claimsResolver 声明解析函数
     * @return 指定声明的值
     */
    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    /**
     * 生成 JWT Access Token
     *
     * @param username 用户名
     * @return JWT access token 字符串
     */
    public String generateToken(String username) {
        return generateToken(new HashMap<>(), username);
    }

    /**
     * 生成携带额外声明的 JWT Access Token
     *
     * @param extraClaims 额外声明
     * @param username    用户名
     * @return JWT access token 字符串
     */
    public String generateToken(Map<String, Object> extraClaims, String username) {
        Map<String, Object> claims = new HashMap<>(extraClaims);
        claims.put(CLAIM_TOKEN_TYPE, TOKEN_TYPE_ACCESS);

        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtExpirationMs);

        return Jwts.builder()
                .claims(claims)
                .subject(username)
                .issuer(issuer)
                .issuedAt(now)
                .expiration(expiry)
                .signWith(getSigningKey())
                .compact();
    }

    /**
     * 生成 JWT Refresh Token（有效期 7 天）
     *
     * @param username 用户名
     * @return JWT refresh token 字符串
     */
    public String generateRefreshToken(String username) {
        Map<String, Object> claims = new HashMap<>();
        claims.put(CLAIM_TOKEN_TYPE, TOKEN_TYPE_REFRESH);

        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtRefreshExpirationMs);

        return Jwts.builder()
                .claims(claims)
                .subject(username)
                .issuer(issuer)
                .issuedAt(now)
                .expiration(expiry)
                .signWith(getSigningKey())
                .compact();
    }

    /**
     * 验证 Refresh Token 是否有效
     * <p>
     * 校验签名、过期时间，并确认 token 类型为 refresh。
     *
     * @param token    JWT refresh token
     * @param username 用户名
     * @return 是否有效
     */
    public boolean validateRefreshToken(String token, String username) {
        try {
            final Claims claims = extractAllClaims(token);
            String tokenType = claims.get(CLAIM_TOKEN_TYPE, String.class);

            if (!TOKEN_TYPE_REFRESH.equals(tokenType)) {
                log.warn("JWT token 类型不匹配: 期望 refresh, 实际 {}", tokenType);
                return false;
            }

            String extractedUsername = claims.getSubject();
            return extractedUsername.equals(username) && !claims.getExpiration().before(new Date());
        } catch (ExpiredJwtException e) {
            log.warn("JWT refresh token 已过期: {}", e.getMessage());
        } catch (UnsupportedJwtException e) {
            log.warn("不支持的 JWT refresh token: {}", e.getMessage());
        } catch (MalformedJwtException e) {
            log.warn("格式错误的 JWT refresh token: {}", e.getMessage());
        } catch (SignatureException e) {
            log.warn("JWT refresh token 签名验证失败: {}", e.getMessage());
        } catch (IllegalArgumentException e) {
            log.warn("JWT refresh token 为空或非法: {}", e.getMessage());
        }
        return false;
    }

    /**
     * 验证 access token 是否有效（用户名匹配且未过期）
     *
     * @param token    JWT token
     * @param username 用户名
     * @return 是否有效
     */
    public boolean isTokenValid(String token, String username) {
        final String extractedUsername = extractUsername(token);
        return extractedUsername.equals(username) && !isTokenExpired(token);
    }

    /**
     * 验证 token 是否有效（仅校验签名和过期时间）
     *
     * @param token JWT token
     * @return 是否有效
     */
    public boolean validateToken(String token) {
        try {
            extractAllClaims(token);
            return true;
        } catch (ExpiredJwtException e) {
            log.warn("JWT token 已过期: {}", e.getMessage());
        } catch (UnsupportedJwtException e) {
            log.warn("不支持的 JWT token: {}", e.getMessage());
        } catch (MalformedJwtException e) {
            log.warn("格式错误的 JWT token: {}", e.getMessage());
        } catch (SignatureException e) {
            log.warn("JWT 签名验证失败: {}", e.getMessage());
        } catch (IllegalArgumentException e) {
            log.warn("JWT token 为空或非法: {}", e.getMessage());
        }
        return false;
    }

    /**
     * 判断 token 是否已过期
     *
     * @param token JWT token
     * @return 是否已过期
     */
    public boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    /**
     * 提取 token 过期时间
     *
     * @param token JWT token
     * @return 过期时间
     */
    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    /**
     * 解析 token 获取全部声明
     *
     * @param token JWT token
     * @return 声明对象
     */
    private Claims extractAllClaims(String token) {
        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    /**
     * 获取签名密钥
     *
     * @return 签名密钥
     */
    private SecretKey getSigningKey() {
        if (jwtSecret == null || jwtSecret.isBlank()) {
            throw new IllegalStateException("security.jwt.secret is not configured");
        }
        byte[] keyBytes = Decoders.BASE64.decode(jwtSecret);
        return Keys.hmacShaKeyFor(keyBytes);
    }
}
