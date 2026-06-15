package com.uav.common.web.sensitive;

import com.fasterxml.jackson.databind.module.SimpleModule;

/**
 * 敏感数据注解 Jackson 模块。
 * <p>
 * 将 {@link SensitiveDataSerializer} 注册到 Jackson ObjectMapper，
 * 使标注了 {@link Sensitive} 注解的字段在 JSON 序列化时自动脱敏。
 */
public class SensitiveAnnotationModule extends SimpleModule {

    public SensitiveAnnotationModule() {
        super("SensitiveAnnotationModule");
        addSerializer(String.class, new SensitiveDataSerializer());
    }
}
