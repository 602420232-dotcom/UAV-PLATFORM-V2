package com.uav.service;

import com.uav.config.JwtUtil;
import com.uav.config.TokenType;
import com.uav.entity.RefreshToken;
import com.uav.entity.TokenBlacklist;
import com.uav.repository.RefreshTokenRepository;
import com.uav.repository.TokenBlacklistRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@Profile("!test")
@RequiredArgsConstructor
public class TokenBlacklistService {

    private static final String BLACKLIST_KEY_PREFIX = "blacklist:";
    private static final String REFRESH_TOKEN_KEY_PREFIX = "refresh:token:";
    private static final String BLACKLIST_USER_KEY_PREFIX = "blacklist:user:";

    private final TokenBlacklistRepository tokenBlacklistRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final RedisTemplate<String, Object> redisTemplate;
    private final JwtUtil jwtUtil;

    public boolean isTokenBlacklisted(String tokenId, TokenType tokenType) {
        String redisKey = getBlacklistKey(tokenId, tokenType);
        Boolean exists = redisTemplate.hasKey(redisKey);
        if (Boolean.TRUE.equals(exists)) {
            return true;
        }
        return tokenBlacklistRepository.existsByTokenId(tokenId);
    }

    @Transactional
    public void addToBlacklist(String token, TokenType tokenType, String reason) {
        String tokenId = jwtUtil.extractTokenId(token);
        Long userId = jwtUtil.extractUserId(token);
        Date expirationDate = jwtUtil.extractExpiration(token);
        LocalDateTime expiresAt = expirationDate.toInstant()
                .atZone(ZoneId.systemDefault())
                .toLocalDateTime();

        TokenBlacklist blacklist = TokenBlacklist.builder()
                .tokenId(tokenId)
                .userId(userId)
                .tokenType(tokenType)
                .reason(reason)
                .createdAt(LocalDateTime.now())
                .expiresAt(expiresAt)
                .build();

        tokenBlacklistRepository.save(blacklist);

        String redisKey = getBlacklistKey(tokenId, tokenType);
        long ttl = expirationDate.getTime() - System.currentTimeMillis();
        if (ttl > 0) {
            redisTemplate.opsForValue().set(redisKey, "1", ttl, TimeUnit.MILLISECONDS);
        }

        String userBlacklistKey = BLACKLIST_USER_KEY_PREFIX + userId;
        redisTemplate.opsForSet().add(userBlacklistKey, tokenId);
        redisTemplate.expire(userBlacklistKey, ttl, TimeUnit.MILLISECONDS);

        log.info("Token added to blacklist: tokenId={}, userId={}, type={}", tokenId, userId, tokenType);
    }

    @Transactional
    public void storeRefreshToken(String refreshToken, String deviceInfo, String ipAddress) {
        String tokenId = jwtUtil.extractTokenId(refreshToken);
        Long userId = jwtUtil.extractUserId(refreshToken);
        Date issuedDate = new Date();
        Date expirationDate = jwtUtil.extractExpiration(refreshToken);
        LocalDateTime issuedAt = issuedDate.toInstant()
                .atZone(ZoneId.systemDefault())
                .toLocalDateTime();
        LocalDateTime expiresAt = expirationDate.toInstant()
                .atZone(ZoneId.systemDefault())
                .toLocalDateTime();

        RefreshToken refreshTokenEntity = RefreshToken.builder()
                .userId(userId)
                .refreshTokenId(tokenId)
                .isUsed(false)
                .isRevoked(false)
                .issuedAt(issuedAt)
                .expiresAt(expiresAt)
                .deviceInfo(deviceInfo)
                .ipAddress(ipAddress)
                .build();

        refreshTokenRepository.save(refreshTokenEntity);

        String redisKey = REFRESH_TOKEN_KEY_PREFIX + tokenId;
        long ttl = expirationDate.getTime() - System.currentTimeMillis();
        if (ttl > 0) {
            redisTemplate.opsForValue().set(redisKey, refreshTokenEntity, ttl, TimeUnit.MILLISECONDS);
        }

        log.info("Refresh token stored: tokenId={}, userId={}", tokenId, userId);
    }

    public boolean isRefreshTokenValid(String refreshToken) {
        String tokenId = jwtUtil.extractTokenId(refreshToken);

        if (isTokenBlacklisted(tokenId, TokenType.REFRESH)) {
            log.warn("Refresh token is blacklisted: {}", tokenId);
            return false;
        }

        String redisKey = REFRESH_TOKEN_KEY_PREFIX + tokenId;
        RefreshToken refreshTokenEntity = (RefreshToken) redisTemplate.opsForValue().get(redisKey);

        if (refreshTokenEntity == null) {
            refreshTokenEntity = refreshTokenRepository.findByRefreshTokenId(tokenId).orElse(null);
        }

        if (refreshTokenEntity == null) {
            log.warn("Refresh token not found: {}", tokenId);
            return false;
        }

        if (refreshTokenEntity.getIsUsed() || refreshTokenEntity.getIsRevoked()) {
            log.warn("Refresh token is used or revoked: tokenId={}, used={}, revoked={}",
                    tokenId, refreshTokenEntity.getIsUsed(), refreshTokenEntity.getIsRevoked());
            return false;
        }

        return true;
    }

    @Transactional
    public void markRefreshTokenAsUsed(String refreshToken) {
        String tokenId = jwtUtil.extractTokenId(refreshToken);

        RefreshToken refreshTokenEntity = refreshTokenRepository.findByRefreshTokenId(tokenId)
                .orElse(null);

        if (refreshTokenEntity != null) {
            refreshTokenEntity.setIsUsed(true);
            refreshTokenRepository.save(refreshTokenEntity);
        }

        String redisKey = REFRESH_TOKEN_KEY_PREFIX + tokenId;
        redisTemplate.delete(redisKey);

        log.info("Refresh token marked as used: {}", tokenId);
    }

    @Scheduled(cron = "0 0 2 * * ?")
    @Transactional
    public void cleanUpExpiredTokens() {
        log.info("Starting cleanup of expired tokens...");

        LocalDateTime now = LocalDateTime.now();

        try {
            tokenBlacklistRepository.deleteByExpiresAtBefore(now);
            refreshTokenRepository.deleteByExpiresAtBefore(now);
            log.info("Cleanup completed. Deleted expired tokens from database.");
        } catch (Exception e) {
            log.error("Error cleaning up expired tokens from database", e);
        }

        log.info("Expired tokens cleanup finished");
    }

    private String getBlacklistKey(String tokenId, TokenType tokenType) {
        return BLACKLIST_KEY_PREFIX + tokenType.name().toLowerCase() + ":" + tokenId;
    }
}
