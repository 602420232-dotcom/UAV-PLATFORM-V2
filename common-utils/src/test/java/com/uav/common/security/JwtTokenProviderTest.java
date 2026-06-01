package com.uav.common.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.quality.Strictness;
import org.mockito.junit.jupiter.MockitoSettings;

import java.util.Date;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
@DisplayName("JwtTokenProvider 单元测试")
class JwtTokenProviderTest {

    private JwtTokenProvider jwtTokenProvider;

    @Mock
    private JwtProperties jwtProperties;

    @BeforeEach
    void setUp() {
        when(jwtProperties.getSecret()).thenReturn("dGVzdFNlY3JldEtleUZvckpXVDI1NkJpdHM=");
        when(jwtProperties.getExpirationMs()).thenReturn(7200000L);
        when(jwtProperties.getRefreshExpirationMs()).thenReturn(2592000000L);
        when(jwtProperties.getIssuer()).thenReturn("uav-platform");
        when(jwtProperties.getTokenPrefix()).thenReturn("Bearer ");
        when(jwtProperties.getHeader()).thenReturn("Authorization");
        when(jwtProperties.isEnabled()).thenReturn(true);

        jwtTokenProvider = new JwtTokenProvider(jwtProperties);
    }

    @Nested
    @DisplayName("Token 生成")
    class TokenGeneration {

        @Test
        @DisplayName("生成访问 Token 应包含用户信息和角色")
        void generateToken_shouldIncludeUserAndRoles() {
            String token = jwtTokenProvider.generateToken("admin", List.of("ADMIN", "USER"));

            assertNotNull(token);
            assertTrue(token.split("\\.").length == 3);
            assertEquals("admin", jwtTokenProvider.extractUsername(token));
            assertTrue(jwtTokenProvider.extractRoles(token).contains("ADMIN"));
            assertTrue(jwtTokenProvider.extractRoles(token).contains("USER"));
        }

        @Test
        @DisplayName("生成访问 Token 应包含租户 ID")
        void generateToken_shouldIncludeTenantId() {
            String token = jwtTokenProvider.generateToken("user1", List.of("USER"), "tenant-001");

            assertNotNull(token);
            assertEquals("tenant-001", jwtTokenProvider.extractTenantId(token));
        }

        @Test
        @DisplayName("每次生成的 Token 应有不同的 JTI")
        void generateToken_shouldHaveUniqueJti() {
            String token1 = jwtTokenProvider.generateToken("admin", List.of("ADMIN"));
            String token2 = jwtTokenProvider.generateToken("admin", List.of("ADMIN"));

            assertNotEquals(
                    jwtTokenProvider.extractJti(token1),
                    jwtTokenProvider.extractJti(token2)
            );
        }

        @Test
        @DisplayName("生成刷新 Token 应成功")
        void generateRefreshToken_shouldSucceed() {
            String refreshToken = jwtTokenProvider.generateRefreshToken("admin");

            assertNotNull(refreshToken);
            assertTrue(jwtTokenProvider.validateToken(refreshToken));
        }
    }

    @Nested
    @DisplayName("Token 验证")
    class TokenValidation {

        @Test
        @DisplayName("有效的 Token 应通过验证")
        void validateToken_withValidToken_shouldReturnTrue() {
            String token = jwtTokenProvider.generateToken("admin", List.of("ADMIN"));

            assertTrue(jwtTokenProvider.validateToken(token));
        }

        @Test
        @DisplayName("无效的 Token 应返回 false")
        void validateToken_withInvalidToken_shouldReturnFalse() {
            assertFalse(jwtTokenProvider.validateToken("invalid.token.here"));
            assertFalse(jwtTokenProvider.validateToken(""));
            assertFalse(jwtTokenProvider.validateToken(null));
        }

        @Test
        @DisplayName("篡改的 Token 应返回 false")
        void validateToken_withTamperedToken_shouldReturnFalse() {
            String token = jwtTokenProvider.generateToken("admin", List.of("ADMIN"));
            String tampered = token.substring(0, token.lastIndexOf('.')) + ".tampered";

            assertFalse(jwtTokenProvider.validateToken(tampered));
        }
    }

    @Nested
    @DisplayName("Token 刷新")
    class TokenRefresh {

        @Test
        @DisplayName("使用有效的刷新 Token 应生成新的访问 Token")
        void refreshAccessToken_withValidRefreshToken_shouldGenerateNewToken() {
            String refreshToken = jwtTokenProvider.generateRefreshToken("admin");

            String newAccessToken = jwtTokenProvider.refreshAccessToken(refreshToken);

            assertNotNull(newAccessToken);
            assertEquals("admin", jwtTokenProvider.extractUsername(newAccessToken));
        }

        @Test
        @DisplayName("使用无效的刷新 Token 应抛出异常")
        void refreshAccessToken_withInvalidRefreshToken_shouldThrow() {
            assertThrows(IllegalArgumentException.class,
                    () -> jwtTokenProvider.refreshAccessToken("invalid.refresh.token"));
        }
    }

    @Nested
    @DisplayName("Claims 提取")
    class ClaimsExtraction {

        @Test
        @DisplayName("提取过期时间应成功")
        void extractExpiration_shouldReturnDate() {
            String token = jwtTokenProvider.generateToken("admin", List.of("ADMIN"));

            Date expiration = jwtTokenProvider.extractExpiration(token);

            assertNotNull(expiration);
            assertTrue(expiration.after(new Date()));
        }

        @Test
        @DisplayName("Token 应在有效期内")
        void isTokenExpired_withValidToken_shouldReturnFalse() {
            String token = jwtTokenProvider.generateToken("admin", List.of("ADMIN"));

            assertFalse(jwtTokenProvider.isTokenExpired(token));
        }
    }
}
