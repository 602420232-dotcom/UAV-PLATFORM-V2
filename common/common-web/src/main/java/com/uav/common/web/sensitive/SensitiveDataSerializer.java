package com.uav.common.web.sensitive;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.BeanProperty;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.ser.ContextualSerializer;

import java.io.IOException;

/**
 * 敏感数据 JSON 序列化器。
 * <p>
 * 在 JSON 序列化时，检测字段上的 {@link Sensitive} 注解，
 * 根据指定的 {@link SensitiveStrategy} 自动脱敏。
 * <p>
 * 使用方式：通过 {@link SensitiveAnnotationModule} 注册到 ObjectMapper。
 */
public class SensitiveDataSerializer extends JsonSerializer<String> implements ContextualSerializer {

    private SensitiveStrategy strategy;

    public SensitiveDataSerializer() {
    }

    public SensitiveDataSerializer(SensitiveStrategy strategy) {
        this.strategy = strategy;
    }

    @Override
    public void serialize(String value, JsonGenerator gen, SerializerProvider provider) throws IOException {
        if (strategy != null && value != null) {
            gen.writeString(strategy.desensitize(value));
        } else {
            gen.writeString(value);
        }
    }

    @Override
    public JsonSerializer<?> createContextual(SerializerProvider prov, BeanProperty property) {
        if (property != null) {
            Sensitive sensitive = property.getAnnotation(Sensitive.class);
            if (sensitive != null) {
                return new SensitiveDataSerializer(sensitive.strategy());
            }
        }
        return this;
    }
}
