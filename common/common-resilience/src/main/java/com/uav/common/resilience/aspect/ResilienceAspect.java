package com.uav.common.resilience.aspect;

import com.uav.common.resilience.annotation.WithCircuitBreaker;
import com.uav.common.resilience.annotation.WithRateLimit;
import com.uav.common.resilience.enums.RateLimitTier;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.ratelimiter.RateLimiter;
import io.github.resilience4j.ratelimiter.RateLimiterRegistry;
import io.github.resilience4j.ratelimiter.RequestNotPermitted;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.stereotype.Component;

import java.lang.reflect.Method;
import java.time.Duration;

/**
 * Resilience4j AOP切面
 */
@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class ResilienceAspect {

    private final CircuitBreakerRegistry circuitBreakerRegistry;
    private final RateLimiterRegistry rateLimiterRegistry;

    @Around("@annotation(com.uav.common.resilience.annotation.WithCircuitBreaker)")
    public Object aroundCircuitBreaker(ProceedingJoinPoint joinPoint) throws Throwable {
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        Method method = signature.getMethod();
        WithCircuitBreaker annotation = method.getAnnotation(WithCircuitBreaker.class);

        String name = annotation.name().isEmpty()
                ? method.getDeclaringClass().getSimpleName() + "." + method.getName()
                : annotation.name();

        CircuitBreaker cb = circuitBreakerRegistry.find(name)
                .orElseGet(() -> circuitBreakerRegistry.circuitBreaker(name,
                        io.github.resilience4j.circuitbreaker.CircuitBreakerConfig.custom()
                                .failureRateThreshold(annotation.failureRateThreshold())
                                .slowCallRateThreshold(annotation.slowCallRateThreshold())
                                .slowCallDurationThreshold(Duration.ofMillis(annotation.slowCallDurationThreshold()))
                                .waitDurationInOpenState(Duration.ofMillis(annotation.waitDurationInOpenState()))
                                .permittedNumberOfCallsInHalfOpenState(annotation.permittedNumberOfCallsInHalfOpenState())
                                .slidingWindowSize(annotation.slidingWindowSize())
                                .build()));

        return cb.executeCheckedSupplier(joinPoint::proceed);
    }

    @Around("@annotation(com.uav.common.resilience.annotation.WithRateLimit)")
    public Object aroundRateLimit(ProceedingJoinPoint joinPoint) throws Throwable {
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        Method method = signature.getMethod();
        WithRateLimit annotation = method.getAnnotation(WithRateLimit.class);

        String name = annotation.name().isEmpty()
                ? method.getDeclaringClass().getSimpleName() + "." + method.getName()
                : annotation.name();

        RateLimitTier tier = annotation.tier();
        int limitForPeriod = annotation.limitForPeriod() > 0 ? annotation.limitForPeriod() : tier.getLimitForPeriod();
        int limitRefreshPeriodMs = annotation.limitRefreshPeriodMs() > 0
                ? annotation.limitRefreshPeriodMs()
                : tier.getLimitRefreshPeriodMs();

        RateLimiter rl = rateLimiterRegistry.find(name)
                .orElseGet(() -> rateLimiterRegistry.rateLimiter(name,
                        io.github.resilience4j.ratelimiter.RateLimiterConfig.custom()
                                .limitForPeriod(limitForPeriod)
                                .limitRefreshPeriod(Duration.ofMillis(limitRefreshPeriodMs))
                                .timeoutDuration(Duration.ZERO)
                                .build()));

        try {
            return rl.executeCheckedSupplier(joinPoint::proceed);
        } catch (RequestNotPermitted e) {
            log.warn("限流触发 [{}]", name);
            throw new com.uav.common.core.exception.BizException(
                    com.uav.common.core.result.ResultCode.TOO_MANY_REQUESTS);
        }
    }
}
