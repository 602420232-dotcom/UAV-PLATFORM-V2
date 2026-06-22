package com.uav.common.security.config;

import com.uav.common.security.filter.HmacAuthenticationFilter;
import com.uav.common.security.filter.JwtAuthenticationFilter;
import com.uav.common.security.filter.TenantContextFilter;
import jakarta.annotation.Nullable;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

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
    @Nullable
    private final HmacAuthenticationFilter hmacAuthenticationFilter;

    public SecurityConfig(TenantContextFilter tenantContextFilter,
                          JwtAuthenticationFilter jwtAuthenticationFilter,
                          @Nullable HmacAuthenticationFilter hmacAuthenticationFilter) {
        this.tenantContextFilter = tenantContextFilter;
        this.jwtAuthenticationFilter = jwtAuthenticationFilter;
        this.hmacAuthenticationFilter = hmacAuthenticationFilter;
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
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/health").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/api/v1/dashboard/global").permitAll()
                .requestMatchers("/api/v1/weather/point", "/api/v1/weather/region", "/api/v1/weather/wind-profile").permitAll()
                .requestMatchers("/api/v1/system/config/demo-mode").permitAll()
                .requestMatchers("/public/**").permitAll()
                .anyRequest().authenticated()
            )

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

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
