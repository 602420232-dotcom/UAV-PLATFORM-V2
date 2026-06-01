# Auth System v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a complete JWT authentication system with Access/Refresh Token separation, Token blacklisting, and full Demo mode features for both Java Spring Boot backend and Python microservices.

**Architecture:** Hybrid authentication with centralized JWT issuance in Java backend, API Gateway validation, and Python microservices verification. Demo mode with multi-layer rate limiting and data isolation.

**Tech Stack:** Java (Spring Boot 3.x, jjwt 0.12.x), Python (PyJWT, FastAPI), MySQL, Redis

---

## Phase 1: Java Spring Boot Backend Improvements

### Task 1: Improve JwtUtil for Access/Refresh Tokens

**Files:**
- Modify: `uav-path-planning-system/backend-spring/src/main/java/com/uav/config/JwtUtil.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/config/JwtProperties.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/config/TokenType.java`
- Test: `uav-path-planning-system/backend-spring/src/test/java/com/uav/config/JwtUtilTest.java`

- [ ] **Step 1: Read existing JwtUtil.java**

First, let's see the current implementation before modifying.

- [ ] **Step 2: Create TokenType enum**

```java
package com.uav.config;

public enum TokenType {
    ACCESS,
    REFRESH
}
```

- [ ] **Step 3: Create JwtProperties configuration**

```java
package com.uav.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {
    private String secret;
    private String refreshSecret;
    private long accessExpiration = 7200;
    private long refreshExpiration = 2592000;
    private String issuer = "uav-platform";

    public String getSecret() {
        return secret;
    }

    public void setSecret(String secret) {
        this.secret = secret;
    }

    public String getRefreshSecret() {
        return refreshSecret;
    }

    public void setRefreshSecret(String refreshSecret) {
        this.refreshSecret = refreshSecret;
    }

    public long getAccessExpiration() {
        return accessExpiration;
    }

    public void setAccessExpiration(long accessExpiration) {
        this.accessExpiration = accessExpiration;
    }

    public long getRefreshExpiration() {
        return refreshExpiration;
    }

    public void setRefreshExpiration(long refreshExpiration) {
        this.refreshExpiration = refreshExpiration;
    }

    public String getIssuer() {
        return issuer;
    }

    public void setIssuer(String issuer) {
        this.issuer = issuer;
    }
}
```

- [ ] **Step 4: Replace JwtUtil with improved implementation**

```java
package com.uav.config;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.Function;

@Slf4j
@Component
public class JwtUtil {

    private final JwtProperties jwtProperties;

    private SecretKey accessSigningKey;
    private SecretKey refreshSigningKey;

    public JwtUtil(JwtProperties jwtProperties) {
        this.jwtProperties = jwtProperties;
    }

    @PostConstruct
    public void init() {
        // Initialize access token signing key (HS512 requires 64-byte key)
        String accessSecret = jwtProperties.getSecret();
        if (accessSecret == null || accessSecret.getBytes(StandardCharsets.UTF_8).length < 64) {
            log.warn("JWT access secret too short, generating secure random key");
            this.accessSigningKey = Keys.secretKeyFor(SignatureAlgorithm.HS512);
        } else {
            this.accessSigningKey = Keys.hmacShaKeyFor(accessSecret.getBytes(StandardCharsets.UTF_8));
        }

        // Initialize refresh token signing key
        String refreshSecret = jwtProperties.getRefreshSecret();
        if (refreshSecret == null || refreshSecret.getBytes(StandardCharsets.UTF_8).length < 64) {
            log.warn("JWT refresh secret too short, generating secure random key");
            this.refreshSigningKey = Keys.secretKeyFor(SignatureAlgorithm.HS512);
        } else {
            this.refreshSigningKey = Keys.hmacShaKeyFor(refreshSecret.getBytes(StandardCharsets.UTF_8));
        }
    }

    private SecretKey getSigningKey(TokenType tokenType) {
        return tokenType == TokenType.ACCESS ? accessSigningKey : refreshSigningKey;
    }

    private long getExpiration(TokenType tokenType) {
        return tokenType == TokenType.ACCESS ? jwtProperties.getAccessExpiration() : jwtProperties.getRefreshExpiration();
    }

    public String extractUsername(String token, TokenType tokenType) {
        return extractClaim(token, Claims::getSubject, tokenType);
    }

    public Date extractExpiration(String token, TokenType tokenType) {
        return extractClaim(token, Claims::getExpiration, tokenType);
    }

    public String extractTokenId(String token, TokenType tokenType) {
        return extractClaim(token, Claims::getId, tokenType);
    }

    public TokenType extractTokenType(String token) {
        try {
            // Try access token first
            Claims claims = extractAllClaims(token, TokenType.ACCESS);
            String type = claims.get("tokenType", String.class);
            return TokenType.valueOf(type);
        } catch (Exception e) {
            // Then try refresh token
            try {
                Claims claims = extractAllClaims(token, TokenType.REFRESH);
                String type = claims.get("tokenType", String.class);
                return TokenType.valueOf(type);
            } catch (Exception ex) {
                throw new IllegalArgumentException("Invalid token type");
            }
        }
    }

    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver, TokenType tokenType) {
        final Claims claims = extractAllClaims(token, tokenType);
        return claimsResolver.apply(claims);
    }

    private Claims extractAllClaims(String token, TokenType tokenType) {
        return Jwts.parser()
                .verifyWith(getSigningKey(tokenType))
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    private Boolean isTokenExpired(String token, TokenType tokenType) {
        return extractExpiration(token, tokenType).before(new Date());
    }

    public String generateAccessToken(UserDetails userDetails, String tenantId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("roles", userDetails.getAuthorities().stream()
                .map(auth -> auth.getAuthority())
                .toList());
        claims.put("tenantId", tenantId);
        claims.put("tokenType", TokenType.ACCESS.name());
        return createToken(claims, userDetails.getUsername(), TokenType.ACCESS);
    }

    public String generateRefreshToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("tokenType", TokenType.REFRESH.name());
        return createToken(claims, userDetails.getUsername(), TokenType.REFRESH);
    }

    private String createToken(Map<String, Object> claims, String subject, TokenType tokenType) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + getExpiration(tokenType) * 1000);

        return Jwts.builder()
                .claims(claims)
                .subject(subject)
                .id(UUID.randomUUID().toString())
                .issuer(jwtProperties.getIssuer())
                .issuedAt(now)
                .expiration(expiryDate)
                .signWith(getSigningKey(tokenType))
                .compact();
    }

    public Boolean validateAccessToken(String token, UserDetails userDetails) {
        try {
            final String username = extractUsername(token, TokenType.ACCESS);
            return (username.equals(userDetails.getUsername()) && !isTokenExpired(token, TokenType.ACCESS));
        } catch (Exception e) {
            log.warn("Access token validation failed: {}", e.getMessage());
            return false;
        }
    }

    public Boolean validateRefreshToken(String token) {
        try {
            TokenType tokenType = extractTokenType(token);
            if (tokenType != TokenType.REFRESH) {
                return false;
            }
            return !isTokenExpired(token, TokenType.REFRESH);
        } catch (Exception e) {
            log.warn("Refresh token validation failed: {}", e.getMessage());
            return false;
        }
    }
}
```

- [ ] **Step 5: Write JwtUtil tests**

```java
package com.uav.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collections;

import static org.junit.jupiter.api.Assertions.*;

class JwtUtilTest {

    private JwtUtil jwtUtil;
    private UserDetails userDetails;

    @BeforeEach
    void setUp() {
        JwtProperties properties = new JwtProperties();
        properties.setSecret("test-secret-key-123456789012345678901234567890123456789012345678901234567890");
        properties.setRefreshSecret("test-refresh-key-123456789012345678901234567890123456789012345678901234567890");
        properties.setAccessExpiration(7200);
        properties.setRefreshExpiration(2592000);

        jwtUtil = new JwtUtil(properties);
        jwtUtil.init();

        userDetails = new User(
            "testuser",
            "password",
            Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER"))
        );
    }

    @Test
    void testGenerateAndValidateAccessToken() {
        String token = jwtUtil.generateAccessToken(userDetails, "default-tenant");
        
        assertNotNull(token);
        assertTrue(jwtUtil.validateAccessToken(token, userDetails));
        assertEquals("testuser", jwtUtil.extractUsername(token, TokenType.ACCESS));
    }

    @Test
    void testGenerateAndValidateRefreshToken() {
        String token = jwtUtil.generateRefreshToken(userDetails);
        
        assertNotNull(token);
        assertTrue(jwtUtil.validateRefreshToken(token));
        assertEquals("testuser", jwtUtil.extractUsername(token, TokenType.REFRESH));
    }

    @Test
    void testExtractTokenType() {
        String accessToken = jwtUtil.generateAccessToken(userDetails, "default-tenant");
        String refreshToken = jwtUtil.generateRefreshToken(userDetails);
        
        assertEquals(TokenType.ACCESS, jwtUtil.extractTokenType(accessToken));
        assertEquals(TokenType.REFRESH, jwtUtil.extractTokenType(refreshToken));
    }
}
```

- [ ] **Step 6: Update application.yml with JWT configuration**

Create/modify: `uav-path-planning-system/backend-spring/src/main/resources/application.yml`

```yaml
jwt:
  secret: ${JWT_SECRET:default-access-secret-123456789012345678901234567890123456789012345678901234567890}
  refresh-secret: ${JWT_REFRESH_SECRET:default-refresh-secret-123456789012345678901234567890123456789012345678901234567890}
  access-expiration: 7200
  refresh-expiration: 2592000
  issuer: uav-platform

demo:
  enabled: true
  max-concurrent-sessions: 1
  api-rate-limit: 1000
  session-duration: 86400
  data-isolation: logical

spring:
  redis:
    host: ${REDIS_HOST:localhost}
    port: ${REDIS_PORT:6379}
    password: ${REDIS_PASSWORD:}
```

---

### Task 2: Implement Token Blacklist Service

**Files:**
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/service/TokenBlacklistService.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/entity/TokenBlacklist.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/repository/TokenBlacklistRepository.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/entity/RefreshToken.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/repository/RefreshTokenRepository.java`
- Modify: `uav-path-planning-system/backend-spring/pom.xml` (if needed)

- [ ] **Step 1: Create TokenBlacklist entity**

```java
package com.uav.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "token_blacklist")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TokenBlacklist {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "token_id", unique = true, nullable = false)
    private String tokenId;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "token_type", nullable = false)
    @Enumerated(EnumType.STRING)
    private TokenType tokenType;

    @Column(name = "reason")
    private String reason;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
```

- [ ] **Step 2: Create RefreshToken entity**

```java
package com.uav.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "refresh_token_family")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RefreshToken {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "refresh_token_id", unique = true, nullable = false)
    private String refreshTokenId;

    @Column(name = "is_used", nullable = false)
    private Boolean isUsed = false;

    @Column(name = "is_revoked", nullable = false)
    private Boolean isRevoked = false;

    @Column(name = "issued_at", nullable = false)
    private LocalDateTime issuedAt;

    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;

    @Column(name = "device_info")
    private String deviceInfo;

    @Column(name = "ip_address")
    private String ipAddress;

    @PrePersist
    protected void onCreate() {
        issuedAt = LocalDateTime.now();
    }
}
```

- [ ] **Step 3: Create TokenBlacklistRepository**

```java
package com.uav.repository;

import com.uav.config.TokenType;
import com.uav.entity.TokenBlacklist;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.Optional;

@Repository
public interface TokenBlacklistRepository extends JpaRepository<TokenBlacklist, Long> {
    Optional<TokenBlacklist> findByTokenId(String tokenId);
    boolean existsByTokenId(String tokenId);
    void deleteByExpiresAtBefore(LocalDateTime now);
    void deleteByUserIdAndTokenType(Long userId, TokenType tokenType);
}
```

- [ ] **Step 4: Create RefreshTokenRepository**

```java
package com.uav.repository;

import com.uav.entity.RefreshToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {
    Optional<RefreshToken> findByRefreshTokenId(String refreshTokenId);
    List<RefreshToken> findByUserId(Long userId);
    List<RefreshToken> findByUserIdAndIsRevokedFalse(Long userId);
}
```

- [ ] **Step 5: Create TokenBlacklistService**

```java
package com.uav.service;

import com.uav.config.JwtUtil;
import com.uav.config.TokenType;
import com.uav.entity.RefreshToken;
import com.uav.entity.TokenBlacklist;
import com.uav.repository.RefreshTokenRepository;
import com.uav.repository.TokenBlacklistRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class TokenBlacklistService {

    private static final String BLACKLIST_KEY_PREFIX = "blacklist:";
    private static final String REFRESH_TOKEN_KEY_PREFIX = "refresh:token:";

    @Autowired
    private TokenBlacklistRepository tokenBlacklistRepository;

    @Autowired
    private RefreshTokenRepository refreshTokenRepository;

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    public boolean isTokenBlacklisted(String tokenId) {
        // Check Redis first
        String redisKey = BLACKLIST_KEY_PREFIX + tokenId;
        Boolean exists = redisTemplate.hasKey(redisKey);
        if (Boolean.TRUE.equals(exists)) {
            return true;
        }

        // Then check database
        return tokenBlacklistRepository.existsByTokenId(tokenId);
    }

    @Transactional
    public void addToBlacklist(String tokenId, Long userId, TokenType tokenType, String reason, Date expiresAt) {
        // Add to Redis
        String redisKey = BLACKLIST_KEY_PREFIX + tokenId;
        long ttl = calculateTtl(expiresAt);
        if (ttl > 0) {
            redisTemplate.opsForValue().set(redisKey, "1", ttl, TimeUnit.SECONDS);
        }

        // Add to database
        TokenBlacklist blacklist = new TokenBlacklist();
        blacklist.setTokenId(tokenId);
        blacklist.setUserId(userId);
        blacklist.setTokenType(tokenType);
        blacklist.setReason(reason);
        blacklist.setExpiresAt(LocalDateTime.ofInstant(expiresAt.toInstant(), ZoneId.systemDefault()));

        tokenBlacklistRepository.save(blacklist);
        log.info("Added token {} to blacklist for user {}, reason: {}", tokenId, userId, reason);
    }

    @Transactional
    public void blacklistAccessToken(String accessToken, Long userId, String reason) {
        String tokenId = jwtUtil.extractTokenId(accessToken, TokenType.ACCESS);
        Date expiresAt = jwtUtil.extractExpiration(accessToken, TokenType.ACCESS);
        addToBlacklist(tokenId, userId, TokenType.ACCESS, reason, expiresAt);
    }

    @Transactional
    public void blacklistRefreshToken(String refreshToken, Long userId, String reason) {
        String tokenId = jwtUtil.extractTokenId(refreshToken, TokenType.REFRESH);
        Date expiresAt = jwtUtil.extractExpiration(refreshToken, TokenType.REFRESH);
        addToBlacklist(tokenId, userId, TokenType.REFRESH, reason, expiresAt);

        // Mark as revoked in database
        Optional<RefreshToken> rt = refreshTokenRepository.findByRefreshTokenId(tokenId);
        rt.ifPresent(refreshTokenEntity -> {
            refreshTokenEntity.setIsRevoked(true);
            refreshTokenRepository.save(refreshTokenEntity);
        });
    }

    @Transactional
    public void blacklistAllUserTokens(Long userId, String reason) {
        // Blacklist all refresh tokens for this user
        List<RefreshToken> tokens = refreshTokenRepository.findByUserId(userId);
        for (RefreshToken token : tokens) {
            addToBlacklist(token.getRefreshTokenId(), userId, TokenType.REFRESH, reason, 
                token.getExpiresAt().atZone(ZoneId.systemDefault()).toInstant().toDate());
            token.setIsRevoked(true);
        }
        refreshTokenRepository.saveAll(tokens);

        log.info("Blacklisted all tokens for user {}, reason: {}", userId, reason);
    }

    public RefreshToken storeRefreshToken(Long userId, String refreshTokenId, 
            Date expiresAt, String deviceInfo, String ipAddress) {
        RefreshToken token = new RefreshToken();
        token.setUserId(userId);
        token.setRefreshTokenId(refreshTokenId);
        token.setExpiresAt(LocalDateTime.ofInstant(expiresAt.toInstant(), ZoneId.systemDefault()));
        token.setDeviceInfo(deviceInfo);
        token.setIpAddress(ipAddress);
        return refreshTokenRepository.save(token);
    }

    public boolean isRefreshTokenValid(String refreshTokenId) {
        // Check blacklist first
        if (isTokenBlacklisted(refreshTokenId)) {
            return false;
        }

        Optional<RefreshToken> token = refreshTokenRepository.findByRefreshTokenId(refreshTokenId);
        return token.isPresent() && !token.get().getIsUsed() && !token.get().getIsRevoked();
    }

    public void markRefreshTokenUsed(String refreshTokenId) {
        Optional<RefreshToken> token = refreshTokenRepository.findByRefreshTokenId(refreshTokenId);
        token.ifPresent(rt -> {
            rt.setIsUsed(true);
            refreshTokenRepository.save(rt);
            log.debug("Marked refresh token {} as used", refreshTokenId);
        });
    }

    @Scheduled(cron = "0 0 * * * ?") // Run every hour
    @Transactional
    public void cleanupExpiredTokens() {
        LocalDateTime now = LocalDateTime.now();
        tokenBlacklistRepository.deleteByExpiresAtBefore(now);
        log.info("Cleaned up expired tokens from blacklist");
    }

    private long calculateTtl(Date expiresAt) {
        long now = System.currentTimeMillis();
        long ttlMillis = expiresAt.getTime() - now;
        return Math.max(0, ttlMillis / 1000);
    }
}
```

---

### Task 3: Update AuthController with New Endpoints

**Files:**
- Modify: `uav-path-planning-system/backend-spring/src/main/java/com/uav/controller/AuthController.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/dto/LoginRequest.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/dto/LoginResponse.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/dto/RefreshTokenRequest.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/dto/RefreshTokenResponse.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/dto/DemoLoginResponse.java`

- [ ] **Step 1: Create DTOs**

LoginRequest.java:
```java
package com.uav.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class LoginRequest {
    @NotBlank(message = "Username is required")
    private String username;

    @NotBlank(message = "Password is required")
    private String password;
}
```

LoginResponse.java:
```java
package com.uav.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LoginResponse {
    private Integer code;
    private String message;
    private TokenData data;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TokenData {
        private String accessToken;
        private String refreshToken;
        private Long expiresIn;
        private String tokenType;
        private UserInfo user;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class UserInfo {
        private Long id;
        private String username;
        private List<String> roles;
    }
}
```

RefreshTokenRequest.java:
```java
package com.uav.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RefreshTokenRequest {
    @NotBlank(message = "Refresh token is required")
    private String refreshToken;
}
```

RefreshTokenResponse.java:
```java
package com.uav.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RefreshTokenResponse {
    private Integer code;
    private String message;
    private TokenData data;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TokenData {
        private String accessToken;
        private String refreshToken;
        private Long expiresIn;
    }
}
```

DemoLoginResponse.java:
```java
package com.uav.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DemoLoginResponse {
    private Integer code;
    private String message;
    private DemoData data;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DemoData {
        private String accessToken;
        private String refreshToken;
        private Long expiresIn;
        private String tokenType;
        private DemoInfo demoInfo;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DemoInfo {
        private String demoUserId;
        private String expirationTime;
        private Limits limits;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class Limits {
        private Integer apiCallsPerHour;
        private Integer concurrentSessions;
        private Integer validDuration;
    }
}
```

- [ ] **Step 2: Completely rewrite AuthController**

```java
package com.uav.controller;

import com.uav.config.JwtProperties;
import com.uav.config.JwtUtil;
import com.uav.config.TokenType;
import com.uav.dto.*;
import com.uav.entity.User;
import com.uav.repository.UserRepository;
import com.uav.service.CustomUserDetailsService;
import com.uav.service.DemoModeService;
import com.uav.service.TokenBlacklistService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.Date;
import java.util.List;

@Slf4j
@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private CustomUserDetailsService userDetailsService;

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private JwtProperties jwtProperties;

    @Autowired
    private TokenBlacklistService tokenBlacklistService;

    @Autowired
    private DemoModeService demoModeService;

    @Autowired
    private UserRepository userRepository;

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest request,
            HttpServletRequest httpRequest) {
        try {
            Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword())
            );

            UserDetails userDetails = (UserDetails) authentication.getPrincipal();
            User user = userRepository.findByUsername(request.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

            String tenantId = user.getTenantId() != null ? user.getTenantId() : "default";
            String accessToken = jwtUtil.generateAccessToken(userDetails, tenantId);
            String refreshToken = jwtUtil.generateRefreshToken(userDetails);

            String refreshTokenId = jwtUtil.extractTokenId(refreshToken, TokenType.REFRESH);
            Date expiresAt = jwtUtil.extractExpiration(refreshToken, TokenType.REFRESH);
            String ipAddress = getClientIpAddress(httpRequest);
            String userAgent = httpRequest.getHeader("User-Agent");

            tokenBlacklistService.storeRefreshToken(
                user.getId(),
                refreshTokenId,
                expiresAt,
                userAgent,
                ipAddress
            );

            List<String> roles = userDetails.getAuthorities().stream()
                .map(auth -> auth.getAuthority())
                .toList();

            LoginResponse response = LoginResponse.builder()
                .code(200)
                .message("Login successful")
                .data(LoginResponse.TokenData.builder()
                    .accessToken(accessToken)
                    .refreshToken(refreshToken)
                    .expiresIn(jwtProperties.getAccessExpiration())
                    .tokenType("Bearer")
                    .user(LoginResponse.UserInfo.builder()
                        .id(user.getId())
                        .username(user.getUsername())
                        .roles(roles)
                        .build())
                    .build())
                .build();

            log.info("User {} logged in successfully from IP {}", user.getUsername(), ipAddress);
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.warn("Login failed for user {}", request.getUsername(), e);
            LoginResponse errorResponse = LoginResponse.builder()
                .code(401)
                .message("Invalid username or password")
                .build();
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(errorResponse);
        }
    }

    @PostMapping("/demo-login")
    public ResponseEntity<DemoLoginResponse> demoLogin(
            @RequestBody(required = false) DemoModeService.DemoLoginRequest request,
            HttpServletRequest httpRequest) {
        try {
            String ipAddress = getClientIpAddress(httpRequest);
            DemoModeService.DemoLoginResult result = demoModeService.createDemoUser(request, ipAddress);

            DemoLoginResponse response = DemoLoginResponse.builder()
                .code(200)
                .message("Demo mode login successful")
                .data(DemoLoginResponse.DemoData.builder()
                    .accessToken(result.getAccessToken())
                    .refreshToken(result.getRefreshToken())
                    .expiresIn(jwtProperties.getAccessExpiration())
                    .tokenType("Bearer")
                    .demoInfo(DemoLoginResponse.DemoInfo.builder()
                        .demoUserId(result.getDemoUserId())
                        .expirationTime(result.getExpirationTime().toString())
                        .limits(DemoLoginResponse.Limits.builder()
                            .apiCallsPerHour(1000)
                            .concurrentSessions(1)
                            .validDuration(86400)
                            .build())
                        .build())
                    .build())
                .build();

            log.info("Demo user {} created from IP {}", result.getDemoUserId(), ipAddress);
            return ResponseEntity.ok(response);

        } catch (DemoModeService.DemoLimitExceededException e) {
            DemoLoginResponse errorResponse = DemoLoginResponse.builder()
                .code(429)
                .message(e.getMessage())
                .build();
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS).body(errorResponse);
        }
    }

    @PostMapping("/refresh")
    public ResponseEntity<RefreshTokenResponse> refreshToken(
            @Valid @RequestBody RefreshTokenRequest request,
            HttpServletRequest httpRequest) {
        try {
            if (!jwtUtil.validateRefreshToken(request.getRefreshToken())) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(RefreshTokenResponse.builder()
                        .code(401)
                        .message("Refresh token is invalid or expired")
                        .build());
            }

            String refreshTokenId = jwtUtil.extractTokenId(request.getRefreshToken(), TokenType.REFRESH);
            if (!tokenBlacklistService.isRefreshTokenValid(refreshTokenId)) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(RefreshTokenResponse.builder()
                        .code(401)
                        .message("Refresh token has been revoked or used")
                        .build());
            }

            String username = jwtUtil.extractUsername(request.getRefreshToken(), TokenType.REFRESH);
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            User user = userRepository.findByUsername(username).orElseThrow();

            String tenantId = user.getTenantId() != null ? user.getTenantId() : "default";
            String newAccessToken = jwtUtil.generateAccessToken(userDetails, tenantId);
            String newRefreshToken = jwtUtil.generateRefreshToken(userDetails);

            // Mark old refresh token as used
            tokenBlacklistService.markRefreshTokenUsed(refreshTokenId);

            // Store new refresh token
            String newRefreshTokenId = jwtUtil.extractTokenId(newRefreshToken, TokenType.REFRESH);
            Date expiresAt = jwtUtil.extractExpiration(newRefreshToken, TokenType.REFRESH);
            String ipAddress = getClientIpAddress(httpRequest);
            String userAgent = httpRequest.getHeader("User-Agent");

            tokenBlacklistService.storeRefreshToken(
                user.getId(),
                newRefreshTokenId,
                expiresAt,
                userAgent,
                ipAddress
            );

            RefreshTokenResponse response = RefreshTokenResponse.builder()
                .code(200)
                .message("Token refreshed successfully")
                .data(RefreshTokenResponse.TokenData.builder()
                    .accessToken(newAccessToken)
                    .refreshToken(newRefreshToken)
                    .expiresIn(jwtProperties.getAccessExpiration())
                    .build())
                .build();

            log.info("Token refreshed for user {}", username);
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.warn("Token refresh failed", e);
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(RefreshTokenResponse.builder()
                    .code(401)
                    .message("Invalid refresh token")
                    .build());
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(
            @RequestHeader(value = "Authorization", required = false) String authHeader,
            @RequestBody(required = false) RefreshTokenRequest refreshRequest,
            HttpServletRequest httpRequest) {
        try {
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                String accessToken = authHeader.substring(7);
                String username = jwtUtil.extractUsername(accessToken, TokenType.ACCESS);
                User user = userRepository.findByUsername(username).orElseThrow();

                String tokenId = jwtUtil.extractTokenId(accessToken, TokenType.ACCESS);
                tokenBlacklistService.addToBlacklist(
                    tokenId, user.getId(), TokenType.ACCESS, "User logout",
                    jwtUtil.extractExpiration(accessToken, TokenType.ACCESS)
                );

                if (refreshRequest != null && refreshRequest.getRefreshToken() != null) {
                    tokenBlacklistService.blacklistRefreshToken(
                        refreshRequest.getRefreshToken(),
                        user.getId(),
                        "User logout"
                    );
                }

                log.info("User {} logged out successfully", username);
            }

            return ResponseEntity.ok(new ApiResponse(200, "Logout successful"));

        } catch (Exception e) {
            log.warn("Logout error", e);
            return ResponseEntity.ok(new ApiResponse(200, "Logout successful"));
        }
    }

    @PostMapping("/revoke")
    public ResponseEntity<?> revokeToken(
            @RequestHeader("Authorization") String authHeader,
            @RequestBody(required = false) RefreshTokenRequest request,
            HttpServletRequest httpRequest) {
        try {
            String accessToken = authHeader.substring(7);
            String username = jwtUtil.extractUsername(accessToken, TokenType.ACCESS);
            User user = userRepository.findByUsername(username).orElseThrow();

            if (request != null && request.getRefreshToken() != null) {
                tokenBlacklistService.blacklistRefreshToken(
                    request.getRefreshToken(),
                    user.getId(),
                    "User revocation"
                );
            } else {
                tokenBlacklistService.blacklistAllUserTokens(user.getId(), "User revocation");
            }

            log.info("Tokens revoked for user {}", username);
            return ResponseEntity.ok(new ApiResponse(200, "Token revoked successfully"));

        } catch (Exception e) {
            log.warn("Token revocation failed", e);
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(new ApiResponse(401, "Invalid token"));
        }
    }

    @GetMapping("/me")
    public ResponseEntity<?> getCurrentUser(@RequestHeader("Authorization") String authHeader) {
        String accessToken = authHeader.substring(7);
        String username = jwtUtil.extractUsername(accessToken, TokenType.ACCESS);
        User user = userRepository.findByUsername(username).orElseThrow();

        List<String> roles = user.getRoles().stream()
            .map(role -> role.getName())
            .toList();

        return ResponseEntity.ok(new ApiResponse(200, "Success", new UserInfo(
            user.getId(),
            user.getUsername(),
            user.getEmail(),
            roles,
            user.getTenantId(),
            null,
            "DEMO".equals(user.getTenantId())
        )));
    }

    private String getClientIpAddress(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddr();
        }
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        return ip;
    }

    public record ApiResponse(Integer code, String message, Object data) {
        public ApiResponse(Integer code, String message) {
            this(code, message, null);
        }
    }

    public record UserInfo(
            Long id,
            String username,
            String email,
            List<String> roles,
            String tenantId,
            List<String> permissions,
            Boolean isDemo
    ) {}
}
```

---

### Task 4: Implement DemoModeService

**Files:**
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/service/DemoModeService.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/config/DemoProperties.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/entity/DemoSession.java`
- Create: `uav-path-planning-system/backend-spring/src/main/java/com/uav/repository/DemoSessionRepository.java`

- [ ] **Step 1: Create DemoProperties**

```java
package com.uav.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "demo")
public class DemoProperties {
    private Boolean enabled = true;
    private Integer maxConcurrentSessions = 1;
    private Integer apiRateLimit = 1000;
    private Integer sessionDuration = 86400;
    private String dataIsolation = "logical";

    public Boolean getEnabled() {
        return enabled;
    }

    public void setEnabled(Boolean enabled) {
        this.enabled = enabled;
    }

    public Integer getMaxConcurrentSessions() {
        return maxConcurrentSessions;
    }

    public void setMaxConcurrentSessions(Integer maxConcurrentSessions) {
        this.maxConcurrentSessions = maxConcurrentSessions;
    }

    public Integer getApiRateLimit() {
        return apiRateLimit;
    }

    public void setApiRateLimit(Integer apiRateLimit) {
        this.apiRateLimit = apiRateLimit;
    }

    public Integer getSessionDuration() {
        return sessionDuration;
    }

    public void setSessionDuration(Integer sessionDuration) {
        this.sessionDuration = sessionDuration;
    }

    public String getDataIsolation() {
        return dataIsolation;
    }

    public void setDataIsolation(String dataIsolation) {
        this.dataIsolation = dataIsolation;
    }
}
```

- [ ] **Step 2: Create DemoSession entity**

```java
package com.uav.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "demo_session")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class DemoSession {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "demo_user_id", unique = true, nullable = false)
    private String demoUserId;

    @Column(name = "user_id")
    private Long userId;

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @Column(name = "session_id")
    private String sessionId;

    @Column(name = "ip_address")
    private String ipAddress;

    @Column(name = "purpose")
    private String purpose;

    @Column(name = "api_calls", nullable = false)
    private Long apiCalls = 0L;

    @Column(name = "started_at", nullable = false)
    private LocalDateTime startedAt;

    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;

    @PrePersist
    protected void onCreate() {
        startedAt = LocalDateTime.now();
    }
}
```

- [ ] **Step 3: Create DemoSessionRepository**

```java
package com.uav.repository;

import com.uav.entity.DemoSession;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface DemoSessionRepository extends JpaRepository<DemoSession, Long> {
    Optional<DemoSession> findByDemoUserId(String demoUserId);
    Optional<DemoSession> findByUserId(Long userId);
    List<DemoSession> findByIsActiveTrue();
    List<DemoSession> findByIsActiveTrueAndExpiresAtAfter(LocalDateTime now);
    Long countByIsActiveTrue();
    void deleteByExpiresAtBefore(LocalDateTime now);
}
```

- [ ] **Step 4: Create DemoModeService**

```java
package com.uav.service;

import com.uav.config.DemoProperties;
import com.uav.config.JwtProperties;
import com.uav.config.JwtUtil;
import com.uav.config.TokenType;
import com.uav.entity.DemoSession;
import com.uav.entity.Role;
import com.uav.entity.User;
import com.uav.repository.DemoSessionRepository;
import com.uav.repository.RoleRepository;
import com.uav.repository.UserRepository;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class DemoModeService {

    private static final String DEMO_ROLE = "ROLE_DEMO";
    private static final String DEMO_SESSION_KEY_PREFIX = "demo:session:";
    private static final String DEMO_RATE_LIMIT_KEY_PREFIX = "ratelimit:demo:";

    @Autowired
    private DemoProperties demoProperties;

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private JwtProperties jwtProperties;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private DemoSessionRepository demoSessionRepository;

    @Autowired
    private TokenBlacklistService tokenBlacklistService;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    public static class DemoLimitExceededException extends RuntimeException {
        public DemoLimitExceededException(String message) {
            super(message);
        }
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DemoLoginRequest {
        private String purpose;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DemoLoginResult {
        private String accessToken;
        private String refreshToken;
        private String demoUserId;
        private LocalDateTime expirationTime;
    }

    @Transactional
    public DemoLoginResult createDemoUser(DemoLoginRequest request, String ipAddress) {
        if (!demoProperties.getEnabled()) {
            throw new DemoLimitExceededException("Demo mode is disabled");
        }

        Long activeSessions = demoSessionRepository.countByIsActiveTrue();
        if (activeSessions >= 100) {
            throw new DemoLimitExceededException("Demo service is currently at full capacity, please try again later");
        }

        String demoUserId = "demo_" + UUID.randomUUID().toString().substring(0, 8);
        String tenantId = "DEMO_TENANT_" + UUID.randomUUID().toString().substring(0, 8);
        String sessionId = UUID.randomUUID().toString();

        User demoUser = new User();
        demoUser.setUsername(demoUserId);
        demoUser.setPassword(passwordEncoder.encode("demo" + UUID.randomUUID()));
        demoUser.setEmail(demoUserId + "@demo.uav");
        demoUser.setFullName("Demo User " + demoUserId);
        demoUser.setTenantId(tenantId);
        demoUser.setEnabled(true);
        demoUser.setAccountNonExpired(true);
        demoUser.setAccountNonLocked(true);
        demoUser.setCredentialsNonExpired(true);

        Role demoRole = roleRepository.findByName(DEMO_ROLE)
            .orElseGet(() -> {
                Role r = new Role();
                r.setName(DEMO_ROLE);
                return roleRepository.save(r);
            });
        demoUser.setRoles(Set.of(demoRole));

        User savedUser = userRepository.save(demoUser);

        LocalDateTime now = LocalDateTime.now();
        LocalDateTime expiresAt = now.plusSeconds(demoProperties.getSessionDuration());

        DemoSession session = new DemoSession();
        session.setDemoUserId(demoUserId);
        session.setUserId(savedUser.getId());
        session.setTenantId(tenantId);
        session.setSessionId(sessionId);
        session.setIpAddress(ipAddress);
        session.setPurpose(request != null ? request.getPurpose() : null);
        session.setExpiresAt(expiresAt);
        session.setIsActive(true);
        demoSessionRepository.save(session);

        UserDetails userDetails = new org.springframework.security.core.userdetails.User(
            demoUser.getUsername(),
            demoUser.getPassword(),
            List.of(new SimpleGrantedAuthority(DEMO_ROLE))
        );

        String accessToken = jwtUtil.generateAccessToken(userDetails, tenantId);
        String refreshToken = jwtUtil.generateRefreshToken(userDetails);

        String refreshTokenId = jwtUtil.extractTokenId(refreshToken, TokenType.REFRESH);
        Date expiresAtDate = Date.from(expiresAt.atZone(ZoneId.systemDefault()).toInstant());
        tokenBlacklistService.storeRefreshToken(
            savedUser.getId(),
            refreshTokenId,
            expiresAtDate,
            "Demo Device",
            ipAddress
        );

        String redisSessionKey = DEMO_SESSION_KEY_PREFIX + demoUserId;
        redisTemplate.opsForValue().set(redisSessionKey, sessionId, demoProperties.getSessionDuration(), TimeUnit.SECONDS);

        return DemoLoginResult.builder()
            .accessToken(accessToken)
            .refreshToken(refreshToken)
            .demoUserId(demoUserId)
            .expirationTime(expiresAt)
            .build();
    }

    public boolean checkRateLimit(String demoUserId) {
        String hourKey = getCurrentHourKey();
        String rateLimitKey = DEMO_RATE_LIMIT_KEY_PREFIX + demoUserId + ":" + hourKey;
        Long current = redisTemplate.opsForValue().increment(rateLimitKey);

        if (current == 1) {
            redisTemplate.expire(rateLimitKey, 3600, TimeUnit.SECONDS);
        }

        boolean allowed = current <= demoProperties.getApiRateLimit();
        if (!allowed) {
            log.warn("Demo user {} exceeded rate limit: {} calls", demoUserId, current);
        }
        return allowed;
    }

    public boolean isDemoSessionValid(String demoUserId) {
        String redisKey = DEMO_SESSION_KEY_PREFIX + demoUserId;
        return Boolean.TRUE.equals(redisTemplate.hasKey(redisKey));
    }

    public Optional<DemoSession> getDemoSession(String demoUserId) {
        return demoSessionRepository.findByDemoUserId(demoUserId);
    }

    public void incrementApiCall(String demoUserId) {
        demoSessionRepository.findByDemoUserId(demoUserId).ifPresent(session -> {
            session.setApiCalls(session.getApiCalls() + 1);
            demoSessionRepository.save(session);
        });
    }

    @Scheduled(cron = "0 0 * * * ?")
    @Transactional
    public void cleanupExpiredSessions() {
        LocalDateTime now = LocalDateTime.now();
        List<DemoSession> expiredSessions = demoSessionRepository.findByIsActiveTrueAndExpiresAtAfter(now).stream()
            .filter(session -> session.getExpiresAt().isBefore(now))
            .toList();

        for (DemoSession session : expiredSessions) {
            session.setIsActive(false);
            demoSessionRepository.save(session);
            if (session.getUserId() != null) {
                tokenBlacklistService.blacklistAllUserTokens(session.getUserId(), "Demo session expired");
            }
            String redisKey = DEMO_SESSION_KEY_PREFIX + session.getDemoUserId();
            redisTemplate.delete(redisKey);
        }

        demoSessionRepository.deleteByExpiresAtBefore(now.minusDays(7));
        log.info("Cleaned up {} expired demo sessions", expiredSessions.size());
    }

    private String getCurrentHourKey() {
        return LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHH"));
    }
}
```

---

### Task 5: Update JWT Authentication Filter

**Files:**
- Modify: `common-utils/src/main/java/com/uav/common/security/JwtAuthenticationFilter.java`
- Create: `common-utils/src/main/java/com/uav/common/security/JwtTokenProvider.java`

- [ ] **Step 1: Update JwtAuthenticationFilter to use blacklist**

```java
package com.uav.common.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
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

import javax.crypto.SecretKey;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;

@Slf4j
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String BLACKLIST_KEY_PREFIX = "blacklist:";

    @Autowired
    private JwtTokenProvider tokenProvider;

    @Autowired(required = false)
    private RedisTemplate<String, String> redisTemplate;

    @Override
    protected void doFilterInternal(@NonNull HttpServletRequest request,
                                    @NonNull HttpServletResponse response,
                                    @NonNull FilterChain filterChain) throws ServletException, IOException {
        if (isPublicPath(request.getRequestURI())) {
            filterChain.doFilter(request, response);
            return;
        }

        String header = request.getHeader("Authorization");
        if (header == null || !header.startsWith("Bearer ")) {
            sendErrorResponse(response, 401, "Missing or invalid Authorization header");
            return;
        }

        try {
            String token = header.substring(7);
            Claims claims = tokenProvider.validateAndGetClaims(token);

            String tokenId = claims.getId();
            if (isTokenBlacklisted(tokenId)) {
                log.warn("Token {} is blacklisted", tokenId);
                sendErrorResponse(response, 401, "Token has been revoked");
                return;
            }

            String username = claims.getSubject();
            String tenantId = claims.get("tenantId", String.class);
            List<?> rawRoles = claims.get("roles", List.class);
            List<SimpleGrantedAuthority> authorities = rawRoles != null ?
                rawRoles.stream()
                    .filter(String.class::isInstance)
                    .map(String.class::cast)
                    .map(SimpleGrantedAuthority::new)
                    .toList() : List.of();

            UsernamePasswordAuthenticationToken auth =
                new UsernamePasswordAuthenticationToken(username, null, authorities);
            auth.setDetails(tenantId);
            SecurityContextHolder.getContext().setAuthentication(auth);

            filterChain.doFilter(request, response);

        } catch (Exception e) {
            log.warn("JWT verification failed: {}", e.getMessage());
            sendErrorResponse(response, 401, "Invalid token");
        }
    }

    private boolean isTokenBlacklisted(String tokenId) {
        if (redisTemplate == null) {
            return false;
        }
        String redisKey = BLACKLIST_KEY_PREFIX + tokenId;
        return Boolean.TRUE.equals(redisTemplate.hasKey(redisKey));
    }

    private boolean isPublicPath(String uri) {
        return uri.equals("/actuator/health") ||
               uri.equals("/actuator/info") ||
               uri.startsWith("/api/public/") ||
               uri.startsWith("/api/auth/") ||
               uri.startsWith("/api/v1/auth/");
    }

    private void sendErrorResponse(HttpServletResponse response, int status, String message) throws IOException {
        response.setStatus(status);
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");
        response.getWriter().write("{\"code\":" + status + ",\"message\":\"" + message + "\"}");
    }
}
```

- [ ] **Step 2: Create JwtTokenProvider**

```java
package com.uav.common.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;

@Slf4j
@Component
public class JwtTokenProvider {

    @Value("${jwt.secret:default-access-secret-123456789012345678901234567890123456789012345678901234567890}")
    private String jwtSecret;

    private SecretKey signingKey;

    @PostConstruct
    public void init() {
        byte[] keyBytes = jwtSecret.getBytes(StandardCharsets.UTF_8);
        if (keyBytes.length >= 64) {
            this.signingKey = Keys.hmacShaKeyFor(keyBytes);
        } else {
            log.warn("JWT secret too short, generating secure key for validation");
            this.signingKey = Keys.secretKeyFor(io.jsonwebtoken.SignatureAlgorithm.HS512);
        }
    }

    public Claims validateAndGetClaims(String token) {
        return Jwts.parser()
            .verifyWith(signingKey)
            .build()
            .parseSignedClaims(token)
            .getPayload();
    }

    public String extractUsername(String token) {
        return validateAndGetClaims(token).getSubject();
    }

    public String extractTenantId(String token) {
        return validateAndGetClaims(token).get("tenantId", String.class);
    }
}
```

---

### Task 6: Add Database Migration for New Tables

**Files:**
- Create: `uav-path-planning-system/backend-spring/src/main/resources/db/migration/V1__auth_system_tables.sql`

- [ ] **Step 1: Create SQL migration file**

```sql
-- Auth System v2 Tables

CREATE TABLE IF NOT EXISTS token_blacklist (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    token_id VARCHAR(255) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    token_type ENUM('ACCESS', 'REFRESH') NOT NULL,
    reason VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    INDEX idx_token_id (token_id),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS refresh_token_family (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    refresh_token_id VARCHAR(255) NOT NULL UNIQUE,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    issued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    device_info VARCHAR(255),
    ip_address VARCHAR(45),
    INDEX idx_user_id (user_id),
    INDEX idx_token_id (refresh_token_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS demo_session (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    demo_user_id VARCHAR(255) NOT NULL UNIQUE,
    user_id BIGINT,
    tenant_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    purpose VARCHAR(255),
    api_calls BIGINT NOT NULL DEFAULT 0,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_demo_user_id (demo_user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add tenant_id to users table if not exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(255) DEFAULT 'default';

-- Create index for tenant_id
CREATE INDEX IF NOT EXISTS idx_tenant_id ON users(tenant_id);
```

---

## Phase 2: Python Microservices Authentication

### Task 7: Python JWT Validation Module

**Files:**
- Create: `common-utils/src/main/python/jwt_auth.py`
- Create: `common-utils/src/main/python/demo_mode.py`
- Create: `common-utils/src/main/python/requirements.txt`

- [ ] **Step 1: Create Python JWT requirements**

Add to: `common-utils/src/main/python/requirements.txt`:
```
PyJWT>=2.8.0
cryptography>=41.0.0
redis>=5.0.0
pydantic>=2.0.0
fastapi>=0.100.0
```

- [ ] **Step 2: Create jwt_auth.py**

```python
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TokenType:
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"


class JwtAuthError(Exception):
    pass


class TokenBlacklistError(JwtAuthError):
    pass


class JwtAuth:
    def __init__(
        self,
        secret: str,
        refresh_secret: Optional[str] = None,
        algorithm: str = "HS512",
        issuer: str = "uav-platform",
        redis_client=None
    ):
        self.secret = secret
        self.refresh_secret = refresh_secret or secret
        self.algorithm = algorithm
        self.issuer = issuer
        self.redis_client = redis_client
        self._validate_key_length(secret)

    def _validate_key_length(self, key: str):
        key_bytes = key.encode("utf-8")
        if len(key_bytes) < 64:
            logger.warning("JWT secret is too short (minimum 64 bytes recommended for HS512)")

    def validate_token(self, token: str, token_type: str = TokenType.ACCESS) -> Dict[str, Any]:
        """Validate a JWT token and return its claims."""
        try:
            secret = self.secret if token_type == TokenType.ACCESS else self.refresh_secret
            claims = jwt.decode(
                token,
                secret,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                options={"verify_exp": True, "verify_iss": True}
            )
            
            if self.redis_client:
                token_id = claims.get("jti")
                if token_id and self._is_token_blacklisted(token_id):
                    raise TokenBlacklistError("Token has been revoked")
            
            return claims
        except jwt.ExpiredSignatureError:
            raise JwtAuthError("Token has expired")
        except jwt.InvalidIssuerError:
            raise JwtAuthError("Invalid token issuer")
        except jwt.InvalidTokenError as e:
            raise JwtAuthError(f"Invalid token: {str(e)}")

    def extract_username(self, token: str, token_type: str = TokenType.ACCESS) -> str:
        claims = self.validate_token(token, token_type)
        return claims.get("sub")

    def extract_tenant_id(self, token: str, token_type: str = TokenType.ACCESS) -> Optional[str]:
        claims = self.validate_token(token, token_type)
        return claims.get("tenantId")

    def extract_roles(self, token: str, token_type: str = TokenType.ACCESS) -> List[str]:
        claims = self.validate_token(token, token_type)
        return claims.get("roles", [])

    def is_demo_user(self, token: str) -> bool:
        try:
            claims = self.validate_token(token, TokenType.ACCESS)
            tenant_id = claims.get("tenantId", "")
            return tenant_id.startswith("DEMO_TENANT_")
        except JwtAuthError:
            return False

    def _is_token_blacklisted(self, token_id: str) -> bool:
        if not self.redis_client:
            return False
        key = f"blacklist:{token_id}"
        return self.redis_client.exists(key) > 0

    def get_current_user_info(self, token: str) -> Dict[str, Any]:
        claims = self.validate_token(token, TokenType.ACCESS)
        return {
            "username": claims.get("sub"),
            "tenant_id": claims.get("tenantId"),
            "roles": claims.get("roles", []),
            "is_demo": claims.get("tenantId", "").startswith("DEMO_TENANT_")
        }


# FastAPI integration helpers
def create_fastapi_dependency(jwt_auth: JwtAuth):
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

    security = HTTPBearer()

    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        try:
            token = credentials.credentials
            claims = jwt_auth.validate_token(token, TokenType.ACCESS)
            return jwt_auth.get_current_user_info(token)
        except JwtAuthError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

    return get_current_user
```

- [ ] **Step 3: Create demo_mode.py**

```python
import redis
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DemoModeService:
    def __init__(
        self,
        redis_client,
        api_rate_limit: int = 1000,
        max_concurrent_sessions: int = 1,
        session_duration: int = 86400
    ):
        self.redis_client = redis_client
        self.api_rate_limit = api_rate_limit
        self.max_concurrent_sessions = max_concurrent_sessions
        self.session_duration = session_duration
        self.session_key_prefix = "demo:session:"
        self.rate_limit_key_prefix = "ratelimit:demo:"

    def check_rate_limit(self, demo_user_id: str) -> bool:
        """Check if demo user is within rate limit."""
        hour_key = datetime.now().strftime("%Y%m%d%H")
        rate_limit_key