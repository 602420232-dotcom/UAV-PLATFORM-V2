package com.uav.common.resilience.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 熔断注解
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface WithCircuitBreaker {

    /** 熔断器名称 */
    String name() default "";

    /** 失败率阈值（百分比） */
    int failureRateThreshold() default 50;

    /** 慢调用率阈值（百分比） */
    int slowCallRateThreshold() default 80;

    /** 慢调用时间阈值（毫秒） */
    int slowCallDurationThreshold() default 2000;

    /** 熔断持续开放时间（毫秒） */
    int waitDurationInOpenState() default 30000;

    /** 半开状态允许调用数 */
    int permittedNumberOfCallsInHalfOpenState() default 5;

    /** 滑动窗口大小 */
    int slidingWindowSize() default 10;
}
