package com.uav.config;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Collections;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("JwtUtil 单元测试")
class JwtUtilTest {

    private JwtUtil jwtUtil;
    private UserDetails userDetails;

    @BeforeEach
    void setUp() {
        jwtUtil = new JwtUtil();
        ReflectionTestUtils.setField(jwtUtil, "secret", "abcdefghijklmnopqrstuvwxyz0123456789ABCDEF");
        ReflectionTestUtils.setField(jwtUtil, "expiration", 3600000L);
        jwtUtil.init();

        userDetails = new User("testuser", "password", Collections.emptyList());
    }

    @Test
    @DisplayName("生成JWT令牌")
    void testGenerateToken() {
        String token = jwtUtil.generateToken(userDetails);
        assertNotNull(token);
        assertFalse(token.isEmpty());
    }

    @Test
    @DisplayName("从令牌提取用户名")
    void testExtractUsername() {
        String token = jwtUtil.generateToken(userDetails);
        String username = jwtUtil.extractUsername(token);
        assertEquals("testuser", username);
    }

    @Test
    @DisplayName("验证有效令牌")
    void testValidateValidToken() {
        String token = jwtUtil.generateToken(userDetails);
        assertTrue(jwtUtil.validateToken(token, userDetails));
    }

    @Test
    @DisplayName("验证无效令牌返回false")
    void testValidateInvalidToken() {
        UserDetails otherUser = new User("otheruser", "password", Collections.emptyList());
        String token = jwtUtil.generateToken(userDetails);
        assertFalse(jwtUtil.validateToken(token, otherUser));
    }

    @Test
    @DisplayName("验证损坏令牌返回false")
    void testValidateMalformedToken() {
        assertFalse(jwtUtil.validateToken("malformed-token", userDetails));
    }

    @Test
    @DisplayName("验证空令牌返回false")
    void testValidateEmptyToken() {
        assertFalse(jwtUtil.validateToken("", userDetails));
    }

    @Test
    @DisplayName("验证null令牌返回false")
    void testValidateNullToken() {
        assertFalse(jwtUtil.validateToken(null, userDetails));
    }

    @Test
    @DisplayName("短密钥自动生成安全密钥")
    void testShortKeyAutoGenerates() {
        JwtUtil shortKeyUtil = new JwtUtil();
        ReflectionTestUtils.setField(shortKeyUtil, "secret", "short");
        ReflectionTestUtils.setField(shortKeyUtil, "expiration", 3600000L);
        shortKeyUtil.init();

        String token = shortKeyUtil.generateToken(userDetails);
        assertNotNull(token);
        assertEquals("testuser", shortKeyUtil.extractUsername(token));
    }
}