package com.uav.common.web.sensitive;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 敏感数据标注注解。
 * <p>
 * 标注在 DTO 字段上，在 JSON 序列化和日志输出时自动脱敏。
 * <p>
 * 使用示例：
 * <pre>
 *     public class UserDTO {
 *         &#64;Sensitive(strategy = SensitiveStrategy.PHONE)
 *         private String phone;
 *
 *         &#64;Sensitive(strategy = SensitiveStrategy.EMAIL)
 *         private String email;
 *
 *         &#64;Sensitive(strategy = SensitiveStrategy.ID_CARD)
 *         private String idCard;
 *     }
 * </pre>
 */
@Documented
@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Sensitive {

    /**
     * 脱敏策略
     */
    SensitiveStrategy strategy();
}
