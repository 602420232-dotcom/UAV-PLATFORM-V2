package com.uav.config;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("JwtUtil 单元测试")
class JwtUtilTest {

    private JwtUtil jwtUtil;
    private JwtProperties jwtProperties;
    private UserDetails userDetails;
    private static final Long TEST_USER_ID = 123L;
    private static final String TEST_TENANT_ID = "test-tenant-001";
    private static final String TEST_USERNAME = "testuser";

    @BeforeEach
    void setUp() {
        jwtProperties = new JwtProperties();
        jwtProperties.setSecret("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ");
        jwtProperties.setRefreshSecret("zyxwvutsrqponmlkjihgfedcba9876543210ZYXWVUTSRQPONMLKJIHGFEDCBA");
        jwtProperties.setAccessExpiration(3600);
        jwtProperties.setRefreshExpiration(86400);
        jwtProperties.setIssuer("uav-platform");
        jwtProperties.setEnabled(true);

        jwtUtil = new JwtUtil(jwtProperties);
        jwtUtil.init();

        userDetails = new User(
                TEST_USERNAME,
                "password",
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER"))
        );
    }

    @Test
    @DisplayName("生成访问令牌")
    void testGenerateAccessToken() {
        String token = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);
        assertNotNull(token);
        assertFalse(token.isEmpty());
    }

    @Test
    @DisplayName("生成刷新令牌")
    void testGenerateRefreshToken() {
        String token = jwtUtil.generateRefreshToken(userDetails, TEST_USER_ID);
        assertNotNull(token);
        assertFalse(token.isEmpty());
    }

    @Test
    @DisplayName("从访问令牌提取用户名")
    void testExtractUsernameFromAccessToken() {
        String token = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);
        String username = jwtUtil.extractUsername(token, TokenType.ACCESS);
        assertEquals(TEST_USERNAME, username);
    }

    @Test
    @DisplayName("从刷新令牌提取用户名")
    void testExtractUsernameFromRefreshToken() {
        String token = jwtUtil.generateRefreshToken(userDetails, TEST_USER_ID);
        String username = jwtUtil.extractUsername(token, TokenType.REFRESH);
        assertEquals(TEST_USERNAME, username);
    }

    @Test
    @DisplayName("从访问令牌提取用户ID")
    void testExtractUserIdFromAccessToken() {
        String token = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);
        Long userId = jwtUtil.extractUserId(token, TokenType.ACCESS);
        assertEquals(TEST_USER_ID, userId);
    }

    @Test
    @DisplayName("从刷新令牌提取用户ID")
    void testExtractUserIdFromRefreshToken() {
        String token = jwtUtil.generateRefreshToken(userDetails, TEST_USER_ID);
        Long userId = jwtUtil.extractUserId(token, TokenType.REFRESH);
        assertEquals(TEST_USER_ID, userId);
    }

    @Test
    @DisplayName("从访问令牌提取租户ID")
    void testExtractTenantIdFromAccessToken() {
        String token = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);
        String tenantId = jwtUtil.extractTenantId(token);
        assertEquals(TEST_TENANT_ID, tenantId);
    }

    @Test
    @DisplayName("从访问令牌提取角色")
    void testExtractRolesFromAccessToken() {
        String token = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);
        List<String> roles = jwtUtil.extractRoles(token);
        assertNotNull(roles);
        assertEquals(1, roles.size());
        assertEquals("ROLE_USER", roles.get(0));
    }

    @Test
    @DisplayName("从访问令牌提取令牌类型")
    void testExtractTokenTypeFromAccessToken() {
        String token = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);
        TokenType type = jwtUtil.extractTokenType(token, TokenType.ACCESS);
        assertEquals(TokenType.ACCESS, type);
    }

    @Test
    @DisplayName("从刷新令牌提取令牌类型")
    void testExtractTokenTypeFromRefreshToken() {
        String token = jwtUtil.generateRefreshToken(userDetails, TEST_USER_ID);
        TokenType type = jwtUtil.extractTokenType(token, TokenType.REFRESH);
        assertEquals(TokenType.REFRESH, type);
    }

    @Test
    @DisplayName("验证有效访问令牌")
    void testValidateValidAccessToken() {
        String token = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);
        assertTrue(jwtUtil.validateAccessToken(token, userDetails));
    }

    @Test
    @DisplayName("验证有效刷新令牌")
    void testValidateValidRefreshToken() {
        String token = jwtUtil.generateRefreshToken(userDetails, TEST_USER_ID);
        assertTrue(jwtUtil.validateRefreshToken(token, userDetails));
    }

    @Test
    @DisplayName("验证无效用户名的访问令牌返回false")
    void testValidateInvalidUsernameAccessToken() {
        UserDetails otherUser = new User("otheruser", "password", Collections.emptyList());
        String token = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);
        assertFalse(jwtUtil.validateAccessToken(token, otherUser));
    }

    @Test
    @DisplayName("验证无效用户名的刷新令牌返回false")
    void testValidateInvalidUsernameRefreshToken() {
        UserDetails otherUser = new User("otheruser", "password", Collections.emptyList());
        String token = jwtUtil.generateRefreshToken(userDetails, TEST_USER_ID);
        assertFalse(jwtUtil.validateRefreshToken(token, otherUser));
    }

    @Test
    @DisplayName("验证损坏的访问令牌返回false")
    void testValidateMalformedAccessToken() {
        assertFalse(jwtUtil.validateAccessToken("malformed-token", userDetails));
    }

    @Test
    @DisplayName("验证损坏的刷新令牌返回false")
    void testValidateMalformedRefreshToken() {
        assertFalse(jwtUtil.validateRefreshToken("malformed-token", userDetails));
    }

    @Test
    @DisplayName("验证空的访问令牌返回false")
    void testValidateEmptyAccessToken() {
        assertFalse(jwtUtil.validateAccessToken("", userDetails));
    }

    @Test
    @DisplayName("验证空的刷新令牌返回false")
    void testValidateEmptyRefreshToken() {
        assertFalse(jwtUtil.validateRefreshToken("", userDetails));
    }

    @Test
    @DisplayName("验证null的访问令牌返回false")
    void testValidateNullAccessToken() {
        assertFalse(jwtUtil.validateAccessToken(null, userDetails));
    }

    @Test
    @DisplayName("验证null的刷新令牌返回false")
    void testValidateNullRefreshToken() {
        assertFalse(jwtUtil.validateRefreshToken(null, userDetails));
    }

    @Test
    @DisplayName("使用错误密钥验证令牌返回false")
    void testValidateTokenWithWrongKey() {
        String token = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);

        JwtProperties wrongProperties = new JwtProperties();
        wrongProperties.setSecret("wrong-secret-abcdefghijklmnopqrstuvwxyz0123456789");
        wrongProperties.setRefreshSecret("wrong-refresh-secret-zyxwvutsrqponmlkjihgfedcba");
        wrongProperties.setAccessExpiration(3600);
        wrongProperties.setRefreshExpiration(86400);
        wrongProperties.setIssuer("uav-platform");
        wrongProperties.setEnabled(true);

        JwtUtil wrongJwtUtil = new JwtUtil(wrongProperties);
        wrongJwtUtil.init();

        assertFalse(wrongJwtUtil.validateAccessToken(token, userDetails));
    }

    @Test
    @DisplayName("使用错误的令牌类型验证返回false")
    void testValidateWrongTokenType() {
        String accessToken = jwtUtil.generateAccessToken(userDetails, TEST_USER_ID, TEST_TENANT_ID);
        String refreshToken = jwtUtil.generateRefreshToken(userDetails, TEST_USER_ID);

        assertFalse(jwtUtil.validateRefreshToken(accessToken, userDetails));
        assertFalse(jwtUtil.validateAccessToken(refreshToken, userDetails));
    }
}
