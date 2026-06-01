package com.uav.config;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("SecurityConfig 测试")
class SecurityConfigTest {

    @Test
    @DisplayName("密码编码器BCrypt创建")
    void testPasswordEncoder() {
        SecurityConfig config = new SecurityConfig();
        assertNotNull(config.passwordEncoder());
    }

    @Test
    @DisplayName("认证管理器创建")
    void testAuthenticationManager() {
        SecurityConfig config = new SecurityConfig();
        assertNotNull(config.authenticationManager());
    }
}

@DisplayName("SecurityAuditConfig 测试")
class SecurityAuditConfigTest {

    @Test
    @DisplayName("审计日志配置")
    void testAuditEventPublisher() {
        com.uav.common.audit.SecurityAuditor auditor = new com.uav.common.audit.SecurityAuditor();
        assertDoesNotThrow(auditor::publisher);
    }

    @Test
    @DisplayName("Spring审计事件发布器")
    void testAuditLogger() {
        assertDoesNotThrow(() -> new com.uav.platform.config.SecurityAuditConfig());
    }
}