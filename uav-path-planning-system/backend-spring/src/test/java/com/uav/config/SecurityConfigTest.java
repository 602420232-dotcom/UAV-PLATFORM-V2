package com.uav.config;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("test")
@DisplayName("SecurityConfig 测试")
class SecurityConfigTest {

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private AuthenticationManager authenticationManager;

    @Test
    @DisplayName("密码编码器BCrypt创建")
    void testPasswordEncoder() {
        assertNotNull(passwordEncoder);
    }

    @Test
    @DisplayName("认证管理器创建")
    void testAuthenticationManager() {
        assertNotNull(authenticationManager);
    }
}

@SpringBootTest
@ActiveProfiles("test")
@DisplayName("SecurityAuditConfig 测试")
class SecurityAuditConfigTest {

    @Autowired
    private SecurityAuditConfig securityAuditConfig;

    @Test
    @DisplayName("审计配置Bean加载")
    void testAuditConfigLoaded() {
        assertNotNull(securityAuditConfig);
    }
}
