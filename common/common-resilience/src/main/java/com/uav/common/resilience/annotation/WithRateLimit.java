package com.uav.common.resilience.annotation;

import com.uav.common.resilience.enums.RateLimitTier;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 限流注解
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface WithRateLimit {

    /** 限流器名称 */
    String name() default "";

    /** 限流等级 */
    RateLimitTier tier() default RateLimitTier.DEFAULT;

    /** 周期内限制次数（覆盖tier默认值） */
    int limitForPeriod() default -1;

    /** 刷新周期毫秒（覆盖tier默认值） */
    int limitRefreshPeriodMs() default -1;
}
