package com.uav.gateway;

import com.uav.gateway.config.RateLimitConfig;
import com.uav.gateway.handler.RateLimitHandler;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.cloud.gateway.filter.ratelimit.KeyResolver;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("API网关测试")
class GatewayTests {

    @Test
    @DisplayName("RateLimitConfig IP密钥解析器")
    void testIpKeyResolver() {
        RateLimitConfig config = new RateLimitConfig();
        KeyResolver resolver = config.ipKeyResolver();
        assertNotNull(resolver);
    }

    @Test
    @DisplayName("RateLimitConfig 用户密钥解析器")
    void testUserKeyResolver() {
        RateLimitConfig config = new RateLimitConfig();
        KeyResolver resolver = config.userKeyResolver();
        assertNotNull(resolver);
    }

    @Test
    @DisplayName("IP密钥解析器从请求头获取")
    void testIpKeyResolverWithRequest() {
        RateLimitConfig config = new RateLimitConfig();
        KeyResolver resolver = config.ipKeyResolver();

        MockServerHttpRequest request = MockServerHttpRequest
            .get("/api/test")
            .remoteAddress(new java.net.InetSocketAddress("192.168.1.1", 8080))
            .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        var result = resolver.resolve(exchange).block();
        assertNotNull(result);
    }

    @Test
    @DisplayName("用户密钥解析器处理无用户头请求")
    void testUserKeyResolverWithAnonymous() {
        RateLimitConfig config = new RateLimitConfig();
        KeyResolver resolver = config.userKeyResolver();

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test").build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        var result = resolver.resolve(exchange).block();
        assertEquals("anonymous", result);
    }

    @Test
    @DisplayName("RateLimitHandler创建")
    void testRateLimitHandler() {
        com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        RateLimitHandler handler = new RateLimitHandler(mapper);
        assertNotNull(handler);
    }

    @Test
    @Disabled("需要 Nacos/Redis 基础设施")
    @DisplayName("应用启动")
    void testApplicationStartup() {
        assertDoesNotThrow(() -> GatewayApplication.main(new String[]{}));
    }
}