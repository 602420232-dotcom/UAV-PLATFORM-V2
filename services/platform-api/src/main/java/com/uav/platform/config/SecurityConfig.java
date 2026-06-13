package com.uav.platform.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;

/**
 * Platform API 安全配置示例
 * <p>
 * 通过 @EnableMethodSecurity 启用方法级安全，支持在 Controller/Service 中
 * 使用 @PreAuthorize、@PostAuthorize、@PreFilter、@PostFilter 注解进行
 * 细粒度的访问控制。
 * <p>
 * 基础的 SecurityFilterChain 已由 common-security 模块中的
 * {@link com.uav.common.security.config.SecurityConfig} 提供，
 * 本配置类专注于启用方法级安全能力。
 * <p>
 * RBAC 扩展能力（数据库用户、角色、权限）通过设置
 * {@code security.rbac.enabled=true} 激活，由 common-security 模块中的
 * {@link com.uav.common.security.config.RbacSecurityConfig} 自动装配。
 * <p>
 * 使用示例：
 * <pre>
 * // 仅 ADMIN 角色可访问
 * &#64;PreAuthorize("hasRole('ADMIN')")
 * public Result&lt;Tenant&gt; createTenant(...) { ... }
 *
 * // ADMIN 或 OPERATOR 角色可访问
 * &#64;PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
 * public Result&lt;Page&lt;Tenant&gt;&gt; listTenants(...) { ... }
 *
 * // 基于 RBAC 权限码校验（需 security.rbac.enabled=true）
 * &#64;PreAuthorize("hasPermission('tenant:create', 'API')")
 * public Result&lt;Tenant&gt; create(...) { ... }
 * </pre>
 */
@Configuration
@EnableMethodSecurity(prePostEnabled = true)
public class SecurityConfig {
    /*
     * 基础的 HTTP 安全配置（SecurityFilterChain、过滤器链等）
     * 已在 common-security 模块的 SecurityConfig 中统一定义：
     *
     * - 放行端点：/health, /actuator/**, /swagger-ui/**, /v3/api-docs/**, /api/v1/auth/**, /public/**
     * - 其他端点需要认证
     * - 过滤器顺序：TenantContextFilter -> HmacAuthenticationFilter -> JwtAuthenticationFilter
     *
     * 如需自定义 platform-api 特有的端点放行规则，可在子模块中定义
     * 一个新的 @Order(2) SecurityFilterChain Bean，例如：
     *
     * @Bean
     * @Order(2)
     * public SecurityFilterChain platformSecurityFilterChain(HttpSecurity http) throws Exception {
     *     http.authorizeHttpRequests(auth -> auth
     *         .requestMatchers("/api/v1/tenants/public/**").permitAll()
     *     );
     *     return http.build();
     * }
     */
}
