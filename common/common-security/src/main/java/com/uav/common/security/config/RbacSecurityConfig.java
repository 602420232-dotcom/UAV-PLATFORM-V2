package com.uav.common.security.config;

import com.uav.common.security.rbac.RbacPermissionEvaluator;
import com.uav.common.security.rbac.RbacUserDetailsService;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.access.expression.method.DefaultMethodSecurityExpressionHandler;
import org.springframework.security.access.expression.method.MethodSecurityExpressionHandler;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
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
 * 仅在 RbacUserRepository Bean 可用时激活（需要 Spring Data JPA + RBAC 数据库表）。
 */
@Configuration
@EnableMethodSecurity(prePostEnabled = true)
@EnableAsync
@ConditionalOnBean(com.uav.common.security.rbac.RbacUserRepository.class)
public class RbacSecurityConfig {

    private final RbacUserDetailsService rbacUserDetailsService;
    private final RbacPermissionEvaluator rbacPermissionEvaluator;

    public RbacSecurityConfig(RbacUserDetailsService rbacUserDetailsService,
                              RbacPermissionEvaluator rbacPermissionEvaluator) {
        this.rbacUserDetailsService = rbacUserDetailsService;
        this.rbacPermissionEvaluator = rbacPermissionEvaluator;
    }

    /**
     * 暴露 UserDetailsService Bean
     * <p>
     * Spring Security 7.x 中 DaoAuthenticationProvider 构造器需要 UserDetailsService 参数，
     * 且 setUserDetailsService() 方法已被移除。
     * 这里直接暴露 UserDetailsService Bean，由 Spring Security 自动配置机制完成认证提供者的创建。
     *
     * @return UserDetailsService
     */
    @Bean("rbacUserDetailsServiceBean")
    public org.springframework.security.core.userdetails.UserDetailsService userDetailsService() {
        return rbacUserDetailsService;
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
