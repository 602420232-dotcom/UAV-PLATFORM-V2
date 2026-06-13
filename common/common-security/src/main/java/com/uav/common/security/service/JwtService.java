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
 */
@Slf4j
@Service
public class JwtService {

    @Value("${security.jwt.secret:uav-platform-default-secret-key-must-be-changed-in-production}")
    private String jwtSecret;

    @Value("${security.jwt.expiration:86400000}")
    private long jwtExpirationMs;

    @Value("${security.jwt.issuer:uav-platform}")
    private String issuer;

    /**
     * 从 token 中提取用户名（subject）
     */
    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    /**
     * 从 token 中提取指定声明
     */
    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    /**
     * 生成 JWT Token
     */
    public String generateToken(String username) {
        return generateToken(new HashMap<>(), username);
    }

    /**
     * 生成携带额外声明的 JWT Token
     */
    public String generateToken(Map<String, Object> extraClaims, String username) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtExpirationMs);

        return Jwts.builder()
                .claims(extraClaims)
                .subject(username)
                .issuer(issuer)
                .issuedAt(now)
                .expiration(expiry)
                .signWith(getSigningKey(), Jwts.SIG.HS256)
                .compact();
    }

    /**
     * 验证 token 是否有效（用户名匹配且未过期）
     */
    public boolean isTokenValid(String token, String username) {
        final String extractedUsername = extractUsername(token);
        return extractedUsername.equals(username) && !isTokenExpired(token);
    }

    /**
     * 验证 token 是否有效（仅校验签名和过期时间）
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
     */
    public boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    /**
     * 提取 token 过期时间
     */
    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    /**
     * 解析 token 获取全部声明
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
     */
    private SecretKey getSigningKey() {
        byte[] keyBytes = Decoders.BASE64.decode(jwtSecret);
        return Keys.hmacShaKeyFor(keyBytes);
    }
}
