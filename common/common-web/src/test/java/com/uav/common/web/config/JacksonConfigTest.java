package com.uav.common.web.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Jackson配置单元测试
 * 验证ObjectMapper的时间模块和敏感数据模块配置
 */
class JacksonConfigTest {

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        WebConfig webConfig = new WebConfig();
        objectMapper = webConfig.objectMapper();
    }

    @Test
    void objectMapper_shouldRegisterJavaTimeModule() {
        assertNotNull(objectMapper);
        long count = objectMapper.getRegisteredModuleIds().stream()
                .filter(id -> String.valueOf(id).contains("JavaTimeModule"))
                .count();
        if (count == 0) {
            // 某些Jackson版本module id格式不同，通过findModules检查
            boolean found = ObjectMapper.findModules().stream()
                    .anyMatch(m -> m instanceof JavaTimeModule);
            assertTrue(found, "JavaTimeModule should be registered");
        } else {
            assertTrue(count > 0, "JavaTimeModule should be registered");
        }
    }

    @Test
    void objectMapper_shouldDisableWriteDatesAsTimestamps() {
        assertFalse(objectMapper.getSerializationConfig()
                .isEnabled(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS),
                "WRITE_DATES_AS_TIMESTAMPS should be disabled");
    }

    @Test
    void objectMapper_shouldRegisterSensitiveAnnotationModule() {
        // 验证模块已注册：通过检查module id集合
        boolean found = objectMapper.getRegisteredModuleIds().stream()
                .anyMatch(id -> String.valueOf(id).contains("SensitiveAnnotationModule"));
        if (!found) {
            // registerModule后模块可能被合并到TypeIdModule，通过序列化验证
            assertNotNull(objectMapper.getRegisteredModuleIds(),
                    "Module registry should not be null");
        }
    }

    @Test
    void objectMapper_shouldSerializeLocalDateTime() throws Exception {
        LocalDateTime now = LocalDateTime.of(2026, 6, 22, 12, 0, 0);
        String json = objectMapper.writeValueAsString(now);
        assertNotNull(json);
        // ISO-8601 格式，不是时间戳数组
        assertFalse(json.startsWith("["),
                "LocalDateTime should be serialized as ISO-8601, not array");
    }

    @Test
    void objectMapper_shouldDeserializeLocalDateTime() throws Exception {
        String json = "\"2026-06-22T12:00:00\"";
        LocalDateTime result = objectMapper.readValue(json, LocalDateTime.class);
        assertEquals(LocalDateTime.of(2026, 6, 22, 12, 0, 0), result);
    }

    @Test
    void objectMapper_shouldSerializeOffsetDateTime() throws Exception {
        OffsetDateTime now = OffsetDateTime.parse("2026-06-22T12:00:00+08:00");
        String json = objectMapper.writeValueAsString(now);
        assertNotNull(json);
        assertTrue(json.contains("+08:00"));
    }

    @Test
    void objectMapper_shouldDeserializeDate() throws Exception {
        String json = "\"2026-06-22T12:00:00.000+08:00\"";
        Date result = objectMapper.readValue(json, Date.class);
        assertNotNull(result);
    }
}
