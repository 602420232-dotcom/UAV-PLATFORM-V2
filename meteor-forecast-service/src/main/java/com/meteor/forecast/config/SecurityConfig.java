package com.meteor.forecast.config;

import com.uav.common.config.CommonSecurityConfig;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;

@Configuration
@EnableWebSecurity
@Import(CommonSecurityConfig.class)
public class SecurityConfig {
}
