package com.uav.common.core.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

/**
 * Redis 配置类
 * <p>
 * Spring Boot 4.0 / Spring Data Redis 3.4+ 不再自动创建 RedisTemplate&lt;String, Object&gt; Bean，
 * 此配置类提供统一的 RedisTemplate 和 StringRedisTemplate 实例。
 * </p>
 */
@Configuration
public class RedisConfig {

    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);

        StringRedisSerializer stringSerializer = new StringRedisSerializer();
        GenericJackson2JsonRedisSerializer jsonSerializer = new GenericJackson2JsonRedisSerializer();

        // Key 使用 String 序列化
        template.setKeySerializer(stringSerializer);
        // Value 使用 Jackson JSON 序列化
        template.setValueSerializer(jsonSerializer);

        // Hash Key 使用 String 序列化
        template.setHashKeySerializer(stringSerializer);
        // Hash Value 使用 Jackson JSON 序列化
        template.setHashValueSerializer(jsonSerializer);

        // 默认序列化器
        template.setDefaultSerializer(jsonSerializer);
        template.setEnableDefaultSerializer(true);

        template.afterPropertiesSet();
        return template;
    }

    @Bean
    public StringRedisTemplate stringRedisTemplate(RedisConnectionFactory connectionFactory) {
        return new StringRedisTemplate(connectionFactory);
    }
}
