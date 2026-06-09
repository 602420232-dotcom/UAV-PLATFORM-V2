package com.uav.bayesian.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("CacheService 单元测试")
class CacheServiceTest {

    @Mock
    private RedisTemplate<String, Object> redisTemplate;

    @Mock
    private ValueOperations<String, Object> valueOperations;

    private CacheService cacheService;

    @BeforeEach
    void setUp() {
        // 显式构造函数注入
        cacheService = new CacheService(redisTemplate);
    }

    @Nested
    @DisplayName("cache")
    class CacheTests {
        @Test
        @DisplayName("正常缓存写入")
        void shouldCacheSuccessfully() {
            when(redisTemplate.opsForValue()).thenReturn(valueOperations);
            String key = "testKey";
            Object value = "testValue";
            long ttl = 60;
            cacheService.cache(key, value, ttl);
            verify(valueOperations).set(key, value, ttl, TimeUnit.SECONDS);
        }

        @Test
        @DisplayName("Redis异常时不应抛异常")
        void shouldNotThrowOnRedisError() {
            when(redisTemplate.opsForValue()).thenThrow(new RuntimeException("Redis down"));
            String key = "key";
            Object value = "value";
            long ttl = 60;
            assertDoesNotThrow(() -> cacheService.cache(key, value, ttl));
        }
    }

    @Nested
    @DisplayName("get")
    class GetTests {
        @Test
        @DisplayName("命中缓存返回数据")
        void shouldReturnCachedValue() {
            String key = "key";
            Object cachedValue = "cachedValue";
            when(redisTemplate.opsForValue()).thenReturn(valueOperations);
            when(valueOperations.get(key)).thenReturn(cachedValue);
            Object result = cacheService.get(key);
            assertNotNull(result);
            assertEquals(cachedValue.toString(), result.toString());
        }

        @Test
        @DisplayName("未命中缓存返回null")
        void shouldReturnNullOnMiss() {
            String key = "key";
            when(redisTemplate.opsForValue()).thenReturn(valueOperations);
            when(valueOperations.get(key)).thenReturn(null);
            Object result = cacheService.get(key);
            assertNull(result);
        }

        @Test
        @DisplayName("Redis异常时返回null")
        void shouldReturnNullOnRedisError() {
            String key = "key";
            when(redisTemplate.opsForValue()).thenThrow(new RuntimeException("Redis down"));
            Object result = cacheService.get(key);
            assertNull(result);
        }
    }

    @Nested
    @DisplayName("evict")
    class EvictTests {
        @Test
        @DisplayName("正常删除缓存")
        void shouldEvictSuccessfully() {
            String key = "key";
            assertDoesNotThrow(() -> cacheService.evict(key));
            verify(redisTemplate).delete(key);
        }

        @Test
        @DisplayName("Redis异常时不应抛异常")
        void shouldNotThrowOnRedisError() {
            String key = "key";
            RuntimeException redisError = new RuntimeException("Redis down");
            doThrow(redisError).when(redisTemplate).delete(key);
            assertDoesNotThrow(() -> cacheService.evict(key));
        }
    }
}
