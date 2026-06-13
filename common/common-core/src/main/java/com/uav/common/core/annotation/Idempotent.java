package com.uav.common.core.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 幂等控制注解
 * <p>
 * 标注在 Controller 方法上，拦截重复请求，防止重复提交。
 * 基于 Redis 实现幂等 Key 的存储与校验。
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Idempotent {

    /**
     * 幂等 Key 的 TTL（秒），默认 24 小时
     */
    int ttlSeconds() default 86400;

    /**
     * 重复请求时返回的错误消息
     */
    String message() default "重复请求，请勿重复提交";
}
