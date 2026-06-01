package com.uav.config;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.UnsupportedJwtException;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SignatureException;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtUtil {

    private final JwtProperties jwtProperties;

    private SecretKey accessSigningKey;
    private SecretKey refreshSigningKey;

    @PostConstruct
    public void init() {
        this.accessSigningKey = Keys.hmacShaKeyFor(jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8));
        this.refreshSigningKey = Keys.hmacShaKeyFor(jwtProperties.getRefreshSecret().getBytes(StandardCharsets.UTF_8));
    }

    public String generateAccessToken(UserDetails userDetails, Long userId, String tenantId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("token_type", TokenType.ACCESS.name());
        claims.put("user_id", userId);
        claims.put("tenant_id", tenantId);
        claims.put("roles", userDetails.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList()));
        return createToken(claims, userDetails.getUsername(), accessSigningKey, jwtProperties.getAccessExpiration());
    }

    public String generateRefreshToken(UserDetails userDetails, Long userId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("token_type", TokenType.REFRESH.name());
        claims.put("user_id", userId);
        return createToken(claims, userDetails.getUsername(), refreshSigningKey, jwtProperties.getRefreshExpiration());
    }

    private String createToken(Map<String, Object> claims, String subject, SecretKey key, long expirationSeconds) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expirationSeconds * 1000);

        return Jwts.builder()
                .claims(claims)
                .subject(subject)
                .issuer(jwtProperties.getIssuer())
                .issuedAt(now)
                .expiration(expiryDate)
                .id(UUID.randomUUID().toString())
                .signWith(key, Jwts.SIG.HS512)
                .compact();
    }

    public String extractUsername(String token, TokenType tokenType) {
        return extractClaim(token, tokenType, Claims::getSubject);
    }

    public Date extractExpiration(String token, TokenType tokenType) {
        return extractClaim(token, tokenType, Claims::getExpiration);
    }

    public String extractTokenId(String token, TokenType tokenType) {
        return extractClaim(token, tokenType, Claims::getId);
    }

    public Long extractUserId(String token, TokenType tokenType) {
        return extractClaim(token, tokenType, claims -> claims.get("user_id", Long.class));
    }

    public String extractTenantId(String token) {
        return extractClaim(token, TokenType.ACCESS, claims -> claims.get("tenant_id", String.class));
    }

    @SuppressWarnings("unchecked")
    public List<String> extractRoles(String token) {
        return extractClaim(token, TokenType.ACCESS, claims -> claims.get("roles", List.class));
    }

    public TokenType extractTokenType(String token, TokenType expectedType) {
        String type = extractClaim(token, expectedType, claims -> claims.get("token_type", String.class));
        return TokenType.valueOf(type);
    }

    public <T> T extractClaim(String token, TokenType tokenType, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token, tokenType);
        return claimsResolver.apply(claims);
    }

    private Claims extractAllClaims(String token, TokenType tokenType) {
        SecretKey key = tokenType == TokenType.ACCESS ? accessSigningKey : refreshSigningKey;
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public Boolean isTokenExpired(String token, TokenType tokenType) {
        try {
            return extractExpiration(token, tokenType).before(new Date());
        } catch (Exception e) {
            return true;
        }
    }

    public Boolean validateAccessToken(String token, UserDetails userDetails) {
        try {
            final String username = extractUsername(token, TokenType.ACCESS);
            final TokenType type = extractTokenType(token, TokenType.ACCESS);
            return (username.equals(userDetails.getUsername()) && !isTokenExpired(token, TokenType.ACCESS) && type == TokenType.ACCESS);
        } catch (Exception e) {
            log.warn("Access token validation failed: {}", e.getMessage());
            return false;
        }
    }

    public Boolean validateRefreshToken(String token, UserDetails userDetails) {
        try {
            final String username = extractUsername(token, TokenType.REFRESH);
            final TokenType type = extractTokenType(token, TokenType.REFRESH);
            return (username.equals(userDetails.getUsername()) && !isTokenExpired(token, TokenType.REFRESH) && type == TokenType.REFRESH);
        } catch (Exception e) {
            log.warn("Refresh token validation failed: {}", e.getMessage());
            return false;
        }
    }

    public Boolean validateToken(String token, TokenType tokenType) {
        try {
            extractAllClaims(token, tokenType);
            return !isTokenExpired(token, tokenType);
        } catch (ExpiredJwtException e) {
            log.warn("Token expired: {}", e.getMessage());
            return false;
        } catch (UnsupportedJwtException | MalformedJwtException | SignatureException | IllegalArgumentException e) {
            log.warn("Invalid token: {}", e.getMessage());
            return false;
        }
    }
}
