package com.uav.common.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnWebApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;


@Configuration
@ConditionalOnWebApplication(type = ConditionalOnWebApplication.Type.SERVLET)
@EnableWebSecurity
public class CommonSecurityConfig {

    @Value("${uav.security.actuator-public:false}")
    private boolean actuatorPublic;

    @Bean
    public SecurityFilterChain defaultSecurityFilterChain(HttpSecurity http) throws Exception {
        http
            .securityMatcher("/auth/**", "/actuator/**")
            // CSRF保护 - 启用并使用Cookie方式（适合前后端分离架构）
            .csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
                // API端点和登录端点禁用CSRF（这些端点使用JWT认证）
                .ignoringRequestMatchers("/api/**", "/auth/**")
            )
            .authorizeHttpRequests(auth -> {
                auth.requestMatchers("/actuator/health", "/actuator/health/**", "/actuator/info").permitAll();
                if (!actuatorPublic) {
                    auth.requestMatchers("/actuator/**").authenticated();
                }
                auth.requestMatchers("/auth/**").permitAll();
                auth.anyRequest().authenticated();
            })
            .httpBasic(httpBasic -> {});
        return http.build();
    }
}
