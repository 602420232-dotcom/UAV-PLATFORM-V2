package org.springframework.boot.autoconfigure.web.embedded;

/**
 * Compatibility bridge for Spring Boot 4.0 + Spring Cloud Gateway 4.3.x.
 * <p>
 * In Spring Boot 4.0, {@code NettyWebServerFactoryCustomizer} was removed from
 * {@code spring-boot-autoconfigure} and moved to {@code spring-boot-reactor-netty}
 * under a different package. Spring Cloud Gateway 4.3.x still references the old
 * class path, causing {@link ClassNotFoundException} at startup.
 * <p>
 * This empty stub satisfies the class-loading check so Gateway's
 * {@code @ConditionalOnClass} annotations pass, while the actual customization
 * is handled by Spring Boot 4.0's own
 * {@code org.springframework.boot.reactor.netty.autoconfigure.NettyReactiveWebServerAutoConfiguration}.
 */
public abstract class NettyWebServerFactoryCustomizer {
}
