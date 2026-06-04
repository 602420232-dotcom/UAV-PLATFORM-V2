package com.uav.bayesian.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.lang.NonNull;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class CacheService {

    private final RedisTemplate<String, Object> redisTemplate;

    public CacheService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public void cache(@NonNull String key, @Nullable Object value, long ttlSeconds) {
        try {
            ValueOperations<String, Object> ops = redisTemplate.opsForValue();
            if (ops != null) {
                if (value != null) {
                    ops.set(key, value, ttlSeconds, TimeUnit.SECONDS);
                    log.debug("缓存设置: {} (TTL={}s)", key, ttlSeconds);
                } else {
                    redisTemplate.delete(key);
                    log.debug("缓存删除（值为null）: {}", key);
                }
            }
        } catch (Exception e) {
            log.warn("缓存写入失败: {}", e.getMessage());
        }
    }

    @Nullable
    public <T> T get(@NonNull String key, @NonNull Class<T> clazz) {
        try {
            ValueOperations<String, Object> ops = redisTemplate.opsForValue();
            if (ops != null) {
                Object resultObj = ops.get(key);
                if (resultObj != null && clazz.isInstance(resultObj)) {
                    return clazz.cast(resultObj);
                }
            }
            return null;
        } catch (Exception e) {
            log.warn("缓存读取失败: {}", e.getMessage());
            return null;
        }
    }

    @Nullable
    public Object get(@NonNull String key) {
        try {
            ValueOperations<String, Object> ops = redisTemplate.opsForValue();
            return ops.get(key);
        } catch (Exception e) {
            log.warn("缓存读取失败: {}", e.getMessage());
            return null;
        }
    }

    public void evict(@NonNull String key) {
        try {
            redisTemplate.delete(key);
        } catch (Exception e) {
            log.warn("缓存删除失败: {}", e.getMessage());
        }
    }
}
