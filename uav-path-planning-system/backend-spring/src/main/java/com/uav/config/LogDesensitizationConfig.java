package com.uav.config;

import ch.qos.logback.classic.pattern.MessageConverter;
import ch.qos.logback.classic.spi.ILoggingEvent;

import java.util.HashMap;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * 日志脱敏工具类
 * 对敏感信息进行统一脱敏处理
 *
 * 注意：此类已从 @Configuration 改为纯工具类，
 * 因为其不定义任何 Spring Bean。如需启用日志脱敏，
 * 请在 logback.xml 中配置 DesensitizationMessageConverter。
 */
public final class LogDesensitizationConfig {

    private LogDesensitizationConfig() {
    }

    /**
     * 脱敏规则映射
     */
    private static final Map<String, Pattern> DESENSITIZATION_PATTERNS = new HashMap<>();

    static {
        DESENSITIZATION_PATTERNS.put("idCard", Pattern.compile("(\\d{4})\\d{10}(\\d{4})"));
        DESENSITIZATION_PATTERNS.put("phone", Pattern.compile("(\\d{3})\\d{4}(\\d{4})"));
        DESENSITIZATION_PATTERNS.put("email", Pattern.compile("(\\w{1})\\w+@(\\w+\\.\\w+)"));
        DESENSITIZATION_PATTERNS.put("bankCard", Pattern.compile("(\\d{6})\\d{8,10}(\\d{4})"));
        DESENSITIZATION_PATTERNS.put("password", Pattern.compile("\"password\"\\s*:\\s*\"[^\"]+\""));
    }

    /**
     * 脱敏处理消息转换器
     */
    public static class DesensitizationMessageConverter extends MessageConverter {

        @Override
        public String convert(ILoggingEvent event) {
            String message = super.convert(event);
            return desensitize(message);
        }
    }

    /**
     * 脱敏处理方法
     */
    public static String desensitize(String message) {
        if (message == null) {
            return null;
        }

        String result = message;

        result = DESENSITIZATION_PATTERNS.get("idCard").matcher(result).replaceAll("$1**********$2");
        result = DESENSITIZATION_PATTERNS.get("phone").matcher(result).replaceAll("$1****$2");
        result = DESENSITIZATION_PATTERNS.get("email").matcher(result).replaceAll("$1****@$2");
        result = DESENSITIZATION_PATTERNS.get("bankCard").matcher(result).replaceAll("$1********$2");
        result = DESENSITIZATION_PATTERNS.get("password").matcher(result).replaceAll("\"password\": \"***\"");

        return result;
    }
}
