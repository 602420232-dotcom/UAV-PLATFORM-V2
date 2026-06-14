package com.uav.common.web.config;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Jackson ObjectMapper 配置单元测试
 */
@DisplayName("Jackson ObjectMapper 配置测试")
@SpringBootTest(classes = WebConfig.class)
class JacksonConfigTest {

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("ObjectMapper Bean 应已加载")
    void objectMapperBeanShouldBeLoaded() {
        assertNotNull(objectMapper, "ObjectMapper 应被 Spring 容器管理");
    }

    @Test
    @DisplayName("日期时间应序列化为 ISO-8601 字符串格式")
    void dateTimeShouldBeSerializedAsIsoString() throws JsonProcessingException {
        LocalDateTime dateTime = LocalDateTime.of(2024, 6, 14, 10, 30, 0);
        String json = objectMapper.writeValueAsString(dateTime);

        assertNotNull(json);
        assertTrue(json.contains("2024"));
        assertTrue(json.contains("10:30"));
    }

    @Test
    @DisplayName("LocalDate 应序列化为字符串而非时间戳数组")
    void localDateShouldBeSerializedAsString() throws JsonProcessingException {
        LocalDate date = LocalDate.of(2024, 6, 14);
        String json = objectMapper.writeValueAsString(date);

        assertNotNull(json);
        // 禁用时间戳后应为字符串形式
        assertTrue(json.contains("2024"));
    }

    @Test
    @DisplayName("WRITE_DATES_AS_TIMESTAMPS 特性应被禁用")
    void writeDatesAsTimestampsShouldBeDisabled() {
        assertFalse(
                objectMapper.getSerializationConfig().isEnabled(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS),
                "日期应序列化为字符串格式"
        );
    }

    @Test
    @DisplayName("空对象应能正常序列化不抛出异常")
    void emptyObjectShouldSerializeWithoutException() throws JsonProcessingException {
        Map<String, Object> emptyMap = Map.of();
        String json = objectMapper.writeValueAsString(emptyMap);

        assertEquals("{}", json);
    }

    @Test
    @DisplayName("嵌套对象序列化应包含正确日期格式")
    void nestedObjectShouldContainCorrectDateFormat() throws JsonProcessingException {
        record TestRecord(String name, LocalDateTime createdAt) {}

        TestRecord record = new TestRecord("test", LocalDateTime.of(2024, 1, 1, 0, 0, 0));
        String json = objectMapper.writeValueAsString(record);

        assertNotNull(json);
        assertTrue(json.contains("test"));
        assertTrue(json.contains("2024"));
    }
}
