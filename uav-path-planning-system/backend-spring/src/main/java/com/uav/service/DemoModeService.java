package com.uav.service;

import com.uav.config.UavProperties;
import com.uav.entity.DemoSession;
import com.uav.model.Role;
import com.uav.model.User;
import com.uav.repository.DemoSessionRepository;
import com.uav.repository.RoleRepository;
import com.uav.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
@Profile("!test")
public class DemoModeService {

    private static final String DEMO_SESSION_KEY_PREFIX = "demo:session:";
    private static final String DEMO_API_CALLS_KEY_PREFIX = "demo:api:calls:";

    private final UavProperties uavProperties;
    private final DemoSessionRepository demoSessionRepository;
    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final RedisTemplate<String, Object> redisTemplate;
    private final PasswordEncoder passwordEncoder;

    @Transactional
    public DemoSession createDemoUser(String ipAddress, String purpose) {
        log.info("Creating demo user, ipAddress={}, purpose={}", ipAddress, purpose);

        if (!uavProperties.getDemo().isEnabled()) {
            throw new IllegalStateException("Demo mode is not enabled");
        }

        long activeSessions = demoSessionRepository.countByIsActiveTrue();
        if (activeSessions >= uavProperties.getDemo().getMaxConcurrentSessions()) {
            throw new IllegalStateException("Max concurrent demo sessions reached");
        }

        String demoUserId = "demo_" + UUID.randomUUID().toString().substring(0, 8);
        String sessionId = UUID.randomUUID().toString();

        Optional<Role> demoRoleOpt = roleRepository.findByName("DEMO");
        Role demoRole;
        if (demoRoleOpt.isEmpty()) {
            demoRole = new Role();
            demoRole.setName("DEMO");
            demoRole = roleRepository.save(demoRole);
        } else {
            demoRole = demoRoleOpt.get();
        }

        User demoUser = new User();
        demoUser.setUsername(demoUserId);
        demoUser.setPassword(passwordEncoder.encode(UUID.randomUUID().toString()));
        demoUser.setEmail(demoUserId + "@demo.local");
        demoUser.setFullName("Demo User " + demoUserId.substring(5));
        demoUser.setEnabled(true);
        demoUser.setAccountNonExpired(true);
        demoUser.setAccountNonLocked(true);
        demoUser.setCredentialsNonExpired(true);
        demoUser.setRoles(Set.of(demoRole));

        demoUser = userRepository.save(demoUser);

        LocalDateTime now = LocalDateTime.now();
        LocalDateTime expiresAt = now.plusSeconds(uavProperties.getDemo().getSessionDuration());

        DemoSession demoSession = DemoSession.builder()
                .demoUserId(demoUserId)
                .userId(demoUser.getId())
                .tenantId(demoUserId)
                .sessionId(sessionId)
                .ipAddress(ipAddress)
                .purpose(purpose)
                .apiCalls(0)
                .startedAt(now)
                .expiresAt(expiresAt)
                .isActive(true)
                .build();

        demoSession = demoSessionRepository.save(demoSession);

        String redisKey = DEMO_SESSION_KEY_PREFIX + sessionId;
        long ttl = uavProperties.getDemo().getSessionDuration();
        redisTemplate.opsForValue().set(redisKey, demoSession, ttl, TimeUnit.SECONDS);

        String apiCallsKey = DEMO_API_CALLS_KEY_PREFIX + sessionId;
        redisTemplate.opsForValue().set(apiCallsKey, 0, ttl, TimeUnit.SECONDS);

        log.info("Demo user created successfully, demoUserId={}, sessionId={}", demoUserId, sessionId);
        return demoSession;
    }

    public boolean checkRateLimit(String sessionId) {
        String apiCallsKey = DEMO_API_CALLS_KEY_PREFIX + sessionId;
        Integer currentCalls = (Integer) redisTemplate.opsForValue().get(apiCallsKey);

        if (currentCalls == null) {
            Optional<DemoSession> sessionOpt = demoSessionRepository.findBySessionId(sessionId);
            if (sessionOpt.isPresent()) {
                currentCalls = sessionOpt.get().getApiCalls();
                long ttl = uavProperties.getDemo().getSessionDuration();
                redisTemplate.opsForValue().set(apiCallsKey, currentCalls, ttl, TimeUnit.SECONDS);
            } else {
                return false;
            }
        }

        return currentCalls < uavProperties.getDemo().getApiRateLimit();
    }

    public boolean isDemoSessionValid(String sessionId) {
        String redisKey = DEMO_SESSION_KEY_PREFIX + sessionId;
        DemoSession demoSession = (DemoSession) redisTemplate.opsForValue().get(redisKey);

        if (demoSession == null) {
            demoSession = demoSessionRepository.findBySessionId(sessionId).orElse(null);
        }

        if (demoSession == null) {
            log.warn("Demo session not found: {}", sessionId);
            return false;
        }

        if (!demoSession.getIsActive()) {
            log.warn("Demo session is inactive: {}", sessionId);
            return false;
        }

        if (demoSession.getExpiresAt().isBefore(LocalDateTime.now())) {
            log.warn("Demo session expired: {}", sessionId);
            return false;
        }

        return true;
    }

    @Transactional
    public void incrementApiCall(String sessionId) {
        String apiCallsKey = DEMO_API_CALLS_KEY_PREFIX + sessionId;
        String redisKey = DEMO_SESSION_KEY_PREFIX + sessionId;

        Long newCalls = redisTemplate.opsForValue().increment(apiCallsKey);

        DemoSession demoSession = (DemoSession) redisTemplate.opsForValue().get(redisKey);
        if (demoSession != null) {
            demoSession.setApiCalls(newCalls != null ? newCalls.intValue() : 0);
            redisTemplate.opsForValue().set(redisKey, demoSession, uavProperties.getDemo().getSessionDuration(), TimeUnit.SECONDS);
        }

        demoSessionRepository.findBySessionId(sessionId).ifPresent(session -> {
            session.setApiCalls(newCalls != null ? newCalls.intValue() : session.getApiCalls() + 1);
            demoSessionRepository.save(session);
        });

        log.debug("API call incremented for session: {}, new count: {}", sessionId, newCalls);
    }

    @Scheduled(cron = "0 0 * * * ?")
    @Transactional
    public void cleanUpExpiredSessions() {
        log.info("Starting cleanup of expired demo sessions...");

        LocalDateTime now = LocalDateTime.now();

        try {
            demoSessionRepository.deleteByExpiresAtBefore(now);
            log.info("Cleanup completed. Deleted expired demo sessions from database.");
        } catch (Exception e) {
            log.error("Error cleaning up expired demo sessions from database", e);
        }

        log.info("Expired demo sessions cleanup finished");
    }

    public Optional<DemoSession> getDemoSession(String sessionId) {
        String redisKey = DEMO_SESSION_KEY_PREFIX + sessionId;
        DemoSession demoSession = (DemoSession) redisTemplate.opsForValue().get(redisKey);

        if (demoSession == null) {
            demoSession = demoSessionRepository.findBySessionId(sessionId).orElse(null);
            if (demoSession != null) {
            long ttl = uavProperties.getDemo().getSessionDuration();
            redisTemplate.opsForValue().set(redisKey, demoSession, ttl, TimeUnit.SECONDS);
        }
        }

        return Optional.ofNullable(demoSession);
    }

    @Transactional
    public void deactivateDemoSession(String sessionId) {
        demoSessionRepository.findBySessionId(sessionId).ifPresent(session -> {
            session.setIsActive(false);
            demoSessionRepository.save(session);

            String redisKey = DEMO_SESSION_KEY_PREFIX + sessionId;
            redisTemplate.delete(redisKey);

            String apiCallsKey = DEMO_API_CALLS_KEY_PREFIX + sessionId;
            redisTemplate.delete(apiCallsKey);

            log.info("Demo session deactivated: {}", sessionId);
        });
    }
}
