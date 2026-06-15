package com.uav.common.security.config;

import com.uav.common.security.filter.HmacAuthenticationFilter;
import com.uav.common.security.filter.JwtAuthenticationFilter;
import com.uav.common.security.filter.TenantContextFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.core.env.Environment;
import org.springframework.core.env.Profiles;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

/**
 * Spring Security 配置
 * <p>
 * 禁用 Session，采用无状态 JWT 认证。
 * 过滤器顺序：TenantContextFilter -> HmacAuthenticationFilter -> JwtAuthenticationFilter
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
public class SecurityConfig {

    private final TenantContextFilter tenantContextFilter;
    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final Environment environment;

    @Autowired(required = false)
    private HmacAuthenticationFilter hmacAuthenticationFilter;

    public SecurityConfig(TenantContextFilter tenantContextFilter,
                          JwtAuthenticationFilter jwtAuthenticationFilter,
                          Environment environment) {
        this.tenantContextFilter = tenantContextFilter;
        this.jwtAuthenticationFilter = jwtAuthenticationFilter;
        this.environment = environment;
    }

    @Bean
    @Order(1)
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // 禁用 CSRF（无状态 API 不需要）
            .csrf(AbstractHttpConfigurer::disable)

            // 禁用 Session，采用无状态策略
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )

            // 配置请求授权
            .authorizeHttpRequests(auth -> {
                // 放行健康检查、公开端点
                auth.requestMatchers(
                    "/health",
                    "/actuator/**",
                    "/api/v1/auth/**",
                    "/public/**"
                ).permitAll();

                // Swagger/OpenAPI 端点仅在非生产环境放行
                boolean isProd = environment.acceptsProfiles(Profiles.of("prod", "production"));
                if (!isProd) {
                    auth.requestMatchers(
                        "/swagger-ui/**",
                        "/v3/api-docs/**"
                    ).permitAll();
                }

                // 其他请求需要认证
                auth.anyRequest().authenticated();
            })

            // 禁用默认表单登录和 HTTP Basic
            .formLogin(AbstractHttpConfigurer::disable)
            .httpBasic(AbstractHttpConfigurer::disable)

            // 按顺序添加自定义过滤器
            .addFilterBefore(tenantContextFilter, UsernamePasswordAuthenticationFilter.class)
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        // 仅在 HmacAuthenticationFilter 可用时添加（需要 ApiKeyService 实现）
        if (hmacAuthenticationFilter != null) {
            http.addFilterBefore(hmacAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
        }

        return http.build();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }
}
