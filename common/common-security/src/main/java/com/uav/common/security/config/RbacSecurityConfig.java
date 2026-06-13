package com.uav.common.security.config;

import com.uav.common.security.rbac.RbacAccessDecisionManager;
import com.uav.common.security.rbac.RbacPermissionEvaluator;
import com.uav.common.security.rbac.RbacUserDetailsService;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.access.expression.method.DefaultMethodSecurityExpressionHandler;
import org.springframework.security.access.expression.method.MethodSecurityExpressionHandler;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * RBAC 安全配置
 * <p>
 * 在现有 {@link SecurityConfig} 基础上扩展 RBAC 功能，提供：
 * <ul>
 *     <li>方法级安全（@PreAuthorize / @PostAuthorize）</li>
 *     <li>自定义权限评估器（@rbacPermissionEvaluator）</li>
 *     <li>基于数据库的 UserDetailsService</li>
 *     <li>BCrypt 密码编码器</li>
 *     <li>异步支持（审计日志异步写入）</li>
 * </ul>
 * <p>
 * 通过配置属性 {@code security.rbac.enabled=true} 激活。
 * <p>
 * 使用示例：
 * <pre>
 * &#64;PreAuthorize("hasRole('ADMIN')")
 * public Result&lt;TenantVO&gt; createTenant(...) { ... }
 *
 * &#64;PreAuthorize("hasPermission('api:v1:planning:POST:path', 'API')")
 * public Result&lt;PathResult&gt; planPath(...) { ... }
 *
 * &#64;PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
 * public Result&lt;Void&gt; approveFlightPlan(...) { ... }
 * </pre>
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
@EnableAsync
@ConditionalOnProperty(prefix = "security.rbac", name = "enabled", havingValue = "true", matchIfMissing = false)
public class RbacSecurityConfig {

    private final RbacUserDetailsService rbacUserDetailsService;
    private final RbacPermissionEvaluator rbacPermissionEvaluator;

    public RbacSecurityConfig(RbacUserDetailsService rbacUserDetailsService,
                              RbacPermissionEvaluator rbacPermissionEvaluator) {
        this.rbacUserDetailsService = rbacUserDetailsService;
        this.rbacPermissionEvaluator = rbacPermissionEvaluator;
    }

    /**
     * 配置基于数据库的认证提供者
     * <p>
     * 使用 {@link RbacUserDetailsService} 从数据库加载用户信息，
     * 使用 BCrypt 进行密码匹配。
     *
     * @return DaoAuthenticationProvider
     */
    @Bean
    public DaoAuthenticationProvider daoAuthenticationProvider() {
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider();
        provider.setUserDetailsService(rbacUserDetailsService);
        provider.setPasswordEncoder(passwordEncoder());
        return provider;
    }

    /**
     * 密码编码器（BCrypt）
     *
     * @return BCryptPasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * 认证管理器
     *
     * @param config 认证配置
     * @return AuthenticationManager
     * @throws Exception 配置异常
     */
    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    /**
     * 配置方法安全表达式处理器
     * <p>
     * 注册自定义 {@link RbacPermissionEvaluator}，使 @PreAuthorize 中
     * 的 hasPermission() 调用走 RBAC 权限校验逻辑。
     *
     * @return MethodSecurityExpressionHandler
     */
    @Bean
    public MethodSecurityExpressionHandler methodSecurityExpressionHandler() {
        DefaultMethodSecurityExpressionHandler handler = new DefaultMethodSecurityExpressionHandler();
        handler.setPermissionEvaluator(rbacPermissionEvaluator);
        return handler;
    }
}
