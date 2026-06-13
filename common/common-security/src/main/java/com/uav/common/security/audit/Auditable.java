package com.uav.common.security.audit;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 审计日志注解
 * <p>
 * 标记在 Controller 或 Service 方法上，AOP 切面自动拦截并记录操作日志。
 * <p>
 * 使用示例：
 * <pre>
 * &#64;Auditable(action = "创建租户", resource = "Tenant")
 * &#64;PostMapping
 * public Result&lt;TenantVO&gt; createTenant(...) { ... }
 *
 * &#64;Auditable(action = "更新租户", resource = "Tenant", detail = "#id")
 * &#64;PutMapping("/{id}")
 * public Result&lt;TenantVO&gt; updateTenant(&#64;PathVariable Long id, ...) { ... }
 * </pre>
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Auditable {

    /**
     * 操作名称（如：创建租户、删除用户、审批飞行计划）
     */
    String action();

    /**
     * 资源类型（如：Tenant、ApiKey、FlightPlan、Weather）
     */
    String resource();

    /**
     * 操作详情，支持 SpEL 表达式（如：#id、#result.id、#request.name）
     * <p>
     * 默认为空字符串，不记录详情
     */
    String detail() default "";

    /**
     * 是否记录请求参数
     * <p>
     * 默认 true，记录方法入参的 JSON 表示
     */
    boolean recordParams() default true;

    /**
     * 是否记录返回结果
     * <p>
     * 默认 false，避免记录大量返回数据
     */
    boolean recordResult() default false;

    /**
     * 是否在异常时也记录审计日志
     * <p>
     * 默认 true，异常操作也需要审计追踪
     */
    boolean recordOnFailure() default true;
}
