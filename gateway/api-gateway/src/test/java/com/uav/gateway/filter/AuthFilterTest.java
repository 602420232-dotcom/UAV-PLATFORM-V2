package com.uav.gateway.filter;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.http.HttpMethod;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.net.URI;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * API Gateway 认证过滤器单元测试
 * <p>
 * 由于项目中没有单独的 AuthFilter，使用 ApiVersionFilter 测试路由匹配与过滤逻辑。
 */
@DisplayName("Gateway 过滤器测试")
class AuthFilterTest {

    private ApiVersionFilter apiVersionFilter;
    private GatewayFilterChain filterChain;
    private ArgumentCaptor<ServerWebExchange> exchangeCaptor;

    @BeforeEach
    void setUp() {
        apiVersionFilter = new ApiVersionFilter();
        filterChain = mock(GatewayFilterChain.class);
        exchangeCaptor = ArgumentCaptor.forClass(ServerWebExchange.class);
        when(filterChain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());
    }

    @Test
    @DisplayName("API 版本路径 /api/v1/ 应正确提取 major version")
    void apiV1PathShouldExtractMajorVersionOne() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/weather/point")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        Mono<Void> result = apiVersionFilter.filter(exchange, filterChain);

        StepVerifier.create(result).verifyComplete();
        assertEquals("1.0", exchange.getAttribute("apiVersion"));
    }

    @Test
    @DisplayName("API 版本路径 /api/v2/ 应正确提取 major version")
    void apiV2PathShouldExtractMajorVersionTwo() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v2/planning/path")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        Mono<Void> result = apiVersionFilter.filter(exchange, filterChain);

        StepVerifier.create(result).verifyComplete();
        assertEquals("2.0", exchange.getAttribute("apiVersion"));
    }

    @Test
    @DisplayName("非版本路径应使用默认版本 1")
    void nonVersionPathShouldUseDefaultVersion() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/actuator/health")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        Mono<Void> result = apiVersionFilter.filter(exchange, filterChain);

        StepVerifier.create(result).verifyComplete();
        assertEquals("1.0", exchange.getAttribute("apiVersion"));
    }

    @Test
    @DisplayName("请求头 X-API-Version 应被解析为 minor version")
    void apiVersionHeaderShouldBeParsedAsMinorVersion() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/weather/point")
                .header("X-API-Version", "5")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        Mono<Void> result = apiVersionFilter.filter(exchange, filterChain);

        StepVerifier.create(result).verifyComplete();
        assertEquals("1.5", exchange.getAttribute("apiVersion"));
    }

    @Test
    @DisplayName("gray version 匹配时应设置灰度路由标记为 true")
    void grayVersionMatchShouldSetGrayRouteTrue() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/weather/point")
                .header("X-API-Version", "3")
                .header("X-Gray-Version", "1.3")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        Mono<Void> result = apiVersionFilter.filter(exchange, filterChain);

        StepVerifier.create(result).verifyComplete();

        verify(filterChain).filter(exchangeCaptor.capture());
        ServerHttpRequest mutatedRequest = exchangeCaptor.getValue().getRequest();
        assertEquals("true", mutatedRequest.getHeaders().getFirst("X-Gray-Route"));
    }

    @Test
    @DisplayName("gray version 不匹配时应设置灰度路由标记为 false")
    void grayVersionMismatchShouldSetGrayRouteFalse() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/weather/point")
                .header("X-API-Version", "3")
                .header("X-Gray-Version", "2.0")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        Mono<Void> result = apiVersionFilter.filter(exchange, filterChain);

        StepVerifier.create(result).verifyComplete();

        verify(filterChain).filter(exchangeCaptor.capture());
        ServerHttpRequest mutatedRequest = exchangeCaptor.getValue().getRequest();
        assertEquals("false", mutatedRequest.getHeaders().getFirst("X-Gray-Route"));
    }

    @Test
    @DisplayName("无 gray version 头时应设置灰度路由标记为 false")
    void noGrayVersionHeaderShouldSetGrayRouteFalse() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v1/weather/point")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        Mono<Void> result = apiVersionFilter.filter(exchange, filterChain);

        StepVerifier.create(result).verifyComplete();

        verify(filterChain).filter(exchangeCaptor.capture());
        ServerHttpRequest mutatedRequest = exchangeCaptor.getValue().getRequest();
        assertEquals("false", mutatedRequest.getHeaders().getFirst("X-Gray-Route"));
    }

    @Test
    @DisplayName("过滤器应向下游传递版本相关请求头")
    void filterShouldPassVersionHeadersToDownstream() {
        MockServerHttpRequest request = MockServerHttpRequest
                .get("/api/v2/assimilation/tasks")
                .header("X-API-Version", "7")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        Mono<Void> result = apiVersionFilter.filter(exchange, filterChain);

        StepVerifier.create(result).verifyComplete();

        verify(filterChain).filter(exchangeCaptor.capture());
        ServerHttpRequest mutatedRequest = exchangeCaptor.getValue().getRequest();
        assertEquals("2", mutatedRequest.getHeaders().getFirst("X-API-Major-Version"));
        assertEquals("7", mutatedRequest.getHeaders().getFirst("X-API-Minor-Version"));
        assertEquals("2.7", mutatedRequest.getHeaders().getFirst("X-API-Full-Version"));
    }

    @Test
    @DisplayName("过滤器顺序应高于默认顺序")
    void filterOrderShouldBeHighPrecedence() {
        int order = apiVersionFilter.getOrder();
        assertTrue(order < 0, "过滤器顺序应高于默认顺序（Ordered.HIGHEST_PRECEDENCE + 20）");
    }

    @Test
    @DisplayName("POST 请求应正确通过过滤器")
    @SuppressWarnings("null")
    void postRequestShouldPassThroughFilter() {
        MockServerHttpRequest request = MockServerHttpRequest
                .method(HttpMethod.POST, URI.create("/api/v1/risk/assess"))
                .header("Content-Type", "application/json")
                .build();
        MockServerWebExchange exchange = MockServerWebExchange.from(request);

        Mono<Void> result = apiVersionFilter.filter(exchange, filterChain);

        StepVerifier.create(result).verifyComplete();
        verify(filterChain).filter(any(ServerWebExchange.class));
    }
}
