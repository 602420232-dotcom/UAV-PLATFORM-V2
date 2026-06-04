package com.uav.bayesian.config;

import com.uav.bayesian.service.CacheService;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.client.RestTemplate;

import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@SuppressWarnings("unchecked")
@DisplayName("同化平台配置测试")
class DataAssimilationConfigTests {

    @Test
    @DisplayName("WebClientConfig创建")
    void testWebClientConfig() {
        WebClientConfig config = new WebClientConfig();
        WebClient.Builder builder = config.webClientBuilder();
        assertNotNull(builder);
        
        WebClient webClient = config.webClient(builder);
        assertNotNull(webClient);
    }

    @Test
    @DisplayName("ResilienceEventListener创建")
    void testResilienceEventListener() {
        CircuitBreakerRegistry registry = CircuitBreakerRegistry.ofDefaults();
        ResilienceEventListener listener = new ResilienceEventListener(registry);
        assertDoesNotThrow(listener::registerListeners);
    }

    @Test
    @DisplayName("ResilienceConfig创建")
    void testResilienceConfig() {
        ResilienceConfig config = new ResilienceConfig();
        assertNotNull(config.defaultCustomizer());
    }

    @Test
    @DisplayName("ProtocolConfig创建")
    void testProtocolConfig() {
        ProtocolConfig config = new ProtocolConfig();
        RestTemplate restTemplate = config.restTemplate();
        assertNotNull(restTemplate);
    }

    @Test
    @DisplayName("CacheService缓存设置")
    void testCacheServiceSet() {
        RedisTemplate<String, Object> template = mock(RedisTemplate.class);
        ValueOperations<String, Object> ops = mock(ValueOperations.class);
        when(template.opsForValue()).thenReturn(ops);

        CacheService cacheService = new CacheService(template);
        String key = "test-key";
        Object value = "test-value";
        long ttl = 300;
        assertDoesNotThrow(() -> cacheService.cache(key, value, ttl));
        verify(ops).set(key, value, ttl, TimeUnit.SECONDS);
    }

    @Test
    @DisplayName("CacheService缓存读取失败返回null")
    void testCacheServiceGetWithError() {
        RedisTemplate<String, Object> template = mock(RedisTemplate.class);
        RuntimeException redisError = new RuntimeException("Redis连接失败");
        when(template.opsForValue()).thenThrow(redisError);

        CacheService cacheService = new CacheService(template);
        String key = "test-key";
        Object result = cacheService.get(key);
        assertNull(result);
    }

    @Test
    @DisplayName("CacheService缓存删除")
    void testCacheServiceEvict() {
        RedisTemplate<String, Object> template = mock(RedisTemplate.class);
        ValueOperations<String, Object> ops = mock(ValueOperations.class);
        when(template.opsForValue()).thenReturn(ops);

        CacheService cacheService = new CacheService(template);
        String key = "test-key";
        assertDoesNotThrow(() -> cacheService.evict(key));
        verify(template).delete(key);
    }
}
