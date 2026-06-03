package com.uav.common.resilience;

import com.uav.common.dto.ApiResponse;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;

/**
 * 限流切面
 * 
 * 在方法级别添加 @RateLimited 注解即可启用限流。
 * 当请求超过阈值时，返回 429 响应而非继续执行。
 */
@Aspect
@Component
public class RateLimitAspect {

    private static final Logger log = LoggerFactory.getLogger(RateLimitAspect.class);
    private final RateLimitService rateLimitService;

    public RateLimitAspect(RateLimitService rateLimitService) {
        this.rateLimitService = rateLimitService;
    }

    @Around("@annotation(rateLimited)")
    public Object checkRateLimit(ProceedingJoinPoint joinPoint, RateLimited rateLimited) throws Throwable {
        int maxRequests = rateLimited.value();
        String methodName = joinPoint.getSignature().toShortString();

        if (rateLimitService.tryAcquire(maxRequests)) {
            return joinPoint.proceed();
        }

        log.warn("Rate limited: {} (max: {}/min)", methodName, maxRequests);
        return ResponseEntity.status(429)
            .body(ApiResponse.error(429, "请求频率超限，请稍后重试"));
    }
}
