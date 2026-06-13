package org.springframework.boot.autoconfigure.data.redis;

/**
 * Compatibility bridge for Spring Boot 4.0 + Spring Cloud Gateway 4.3.x.
 * <p>
 * In Spring Boot 4.0, Redis auto-configuration classes were reorganized.
 * Spring Cloud Gateway's {@code GatewayRedisAutoConfiguration} references
 * this class via {@code @ConditionalOnClass}. This empty stub satisfies
 * the class-loading check.
 */
public abstract class RedisReactiveAutoConfiguration {
}
