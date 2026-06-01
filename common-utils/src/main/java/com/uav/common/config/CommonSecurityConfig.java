package com.uav.common.config;

import com.uav.common.security.CookieCsrfTokenRepository;
import com.uav.common.security.JwtAuthenticationFilter;
import com.uav.common.security.JwtProperties;
import com.uav.common.security.JwtTokenProvider;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.Optional;

/**
 * Common Security Configuration
 *
 * This configuration provides JWT-based security for services that don't have
 * their own SecurityConfig.
 *
 * Activation: Set uav.security.common-enabled=true in application.yml
 * (matchIfMissing=false -- must be explicitly enabled)
 *
 * Security features:
 * - JWT authentication via JwtAuthenticationFilter
 * - Stateless session management (no HTTP session)
 * - CSRF protection for non-API paths
 * - Strict CORS with explicit allowed origins
 * - All non-public endpoints require authentication
 */
@Configuration
@EnableWebSecurity
@ConditionalOnProperty(
    name = "uav.security.common-enabled",
    havingValue = "true",
    matchIfMissing = false
)
public class CommonSecurityConfig {

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @Autowired
    private JwtProperties jwtProperties;

    @Autowired(required = false)
    private Optional<RedisTemplate<String, String>> redisTemplate = Optional.empty();

    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter() {
        return new JwtAuthenticationFilter(jwtTokenProvider, jwtProperties, redisTemplate);
    }

    @Bean
    public SecurityFilterChain defaultSecurityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyEnabled())
                .ignoringRequestMatchers("/api/**", "/auth/**", "/actuator/**")
            )
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health", "/actuator/info").permitAll()
                .requestMatchers("/auth/**").permitAll()
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        String originsStr = System.getenv("CORS_ORIGINS");
        CorsConfiguration configuration = new CorsConfiguration();
        if (originsStr != null && !originsStr.isBlank()) {
            configuration.setAllowedOriginPatterns(Arrays.asList(originsStr.split(",")));
        } else {
            configuration.setAllowedOriginPatterns(Arrays.asList(
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080"
            ));
        }
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(Arrays.asList("Authorization", "Content-Type", "X-Requested-With", "Accept", "Origin"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
