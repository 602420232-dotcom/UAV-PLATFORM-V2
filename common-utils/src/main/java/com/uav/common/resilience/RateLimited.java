package com.uav.common.resilience;

import java.lang.annotation.*;

/**
 * 限流注解
 * 
 * 标注在 Controller 方法上，启用本地限流保护。
 * 当请求超过指定阈值时返回 429 Too Many Requests。
 * 
 * 使用示例:
 * {@code @RateLimited(50)} — 每分钟最多 50 次请求
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface RateLimited {
    
    /**
     * @return 每分钟最大请求数
     */
    int value() default 100;
}
