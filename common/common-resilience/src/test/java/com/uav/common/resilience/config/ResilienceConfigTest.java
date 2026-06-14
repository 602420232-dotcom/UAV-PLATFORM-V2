package com.uav.common.resilience.config;

import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.ratelimiter.RateLimiterConfig;
import io.github.resilience4j.ratelimiter.RateLimiterRegistry;
import io.github.resilience4j.retry.RetryConfig;
import io.github.resilience4j.retry.RetryRegistry;
import io.github.resilience4j.timelimiter.TimeLimiterConfig;
import io.github.resilience4j.timelimiter.TimeLimiterRegistry;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("ResilienceConfig 配置加载测试")
@ExtendWith(MockitoExtension.class)
class ResilienceConfigTest {

    @Test
    @DisplayName("CircuitBreakerRegistry 应包含正确的默认配置")
    void circuitBreakerRegistryShouldHaveCorrectDefaultConfig() {
        ResilienceConfig config = new ResilienceConfig();
        CircuitBreakerRegistry registry = config.circuitBreakerRegistry();

        assertNotNull(registry);

        CircuitBreakerConfig defaultConfig = registry.getDefaultConfig();
        assertEquals(50.0f, defaultConfig.getFailureRateThreshold(), 0.01f);
        assertEquals(80.0f, defaultConfig.getSlowCallRateThreshold(), 0.01f);
        assertEquals(Duration.ofSeconds(2), defaultConfig.getSlowCallDurationThreshold());
        assertEquals(30000L, defaultConfig.getWaitIntervalFunctionInOpenState().apply(1));
        assertEquals(5, defaultConfig.getPermittedNumberOfCallsInHalfOpenState());
        assertEquals(10, defaultConfig.getSlidingWindowSize());
        assertEquals(5, defaultConfig.getMinimumNumberOfCalls());
    }

    @Test
    @DisplayName("RetryRegistry 应包含正确的默认配置")
    void retryRegistryShouldHaveCorrectDefaultConfig() {
        ResilienceConfig config = new ResilienceConfig();
        RetryRegistry registry = config.retryRegistry();

        assertNotNull(registry);

        RetryConfig defaultConfig = registry.getDefaultConfig();
        assertEquals(3, defaultConfig.getMaxAttempts());
        assertEquals(500L, defaultConfig.getIntervalBiFunction().apply(1, null));
    }

    @Test
    @DisplayName("RateLimiterRegistry 应包含正确的默认配置")
    void rateLimiterRegistryShouldHaveCorrectDefaultConfig() {
        ResilienceConfig config = new ResilienceConfig();
        RateLimiterRegistry registry = config.rateLimiterRegistry();

        assertNotNull(registry);

        RateLimiterConfig defaultConfig = registry.getDefaultConfig();
        assertEquals(100, defaultConfig.getLimitForPeriod());
        assertEquals(Duration.ofSeconds(1), defaultConfig.getLimitRefreshPeriod());
        assertEquals(Duration.ZERO, defaultConfig.getTimeoutDuration());
    }

    @Test
    @DisplayName("TimeLimiterRegistry 应包含正确的默认配置")
    void timeLimiterRegistryShouldHaveCorrectDefaultConfig() {
        ResilienceConfig config = new ResilienceConfig();
        TimeLimiterRegistry registry = config.timeLimiterRegistry();

        assertNotNull(registry);

        TimeLimiterConfig defaultConfig = registry.getDefaultConfig();
        assertEquals(Duration.ofSeconds(5), defaultConfig.getTimeoutDuration());
        assertTrue(defaultConfig.shouldCancelRunningFuture());
    }

    @Test
    @DisplayName("CircuitBreaker 状态转换应正确")
    void circuitBreakerStateTransitionShouldWork() {
        ResilienceConfig config = new ResilienceConfig();
        CircuitBreakerRegistry registry = config.circuitBreakerRegistry();
        CircuitBreaker cb = registry.circuitBreaker("test-cb");

        assertEquals(CircuitBreaker.State.CLOSED, cb.getState());

        for (int i = 0; i < 10; i++) {
            cb.onError(0, TimeUnit.MILLISECONDS, new RuntimeException("test"));
        }

        assertEquals(CircuitBreaker.State.OPEN, cb.getState());
    }
}
