package com.uav.common.annotation;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 标记该 Controller 类或方法为存根/桩实现。
 * <p>
 * 存根端点返回硬编码的 Mock 数据，仅供前端联调或演示环境使用。
 * 生产环境应使用真实的业务服务替代。
 * <p>
 * 使用示例:
 * <pre>{@code
 * @StubController(reason = "前端联调使用，待集成真实服务", plannedBy = "Q3-2026")
 * @RestController
 * public class DemoController { ... }
 * }</pre>
 */
@Target({ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface StubController {

    /** 存根原因 */
    String reason() default "演示/开发联调使用";

    /** 计划替换的真实服务名称 */
    String plannedReplacement() default "";

    /** 计划完成时间 */
    String plannedBy() default "";
}
