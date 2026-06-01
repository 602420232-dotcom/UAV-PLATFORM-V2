package com.uav.common.security;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.quality.Strictness;
import org.mockito.junit.jupiter.MockitoSettings;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.test.util.ReflectionTestUtils;

import jakarta.servlet.FilterChain;
import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.Objects;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
@DisplayName("JwtAuthenticationFilter 集成测试")
class JwtAuthenticationFilterIntegrationTest {

    private static final String TEST_SECRET = "abcdefghijklmnopqrstuvwxyz0123456789";

    @Mock
    private FilterChain filterChain;

    private JwtAuthenticationFilter jwtAuthenticationFilter;

    @BeforeEach
    void setUp() {
        jwtAuthenticationFilter = new JwtAuthenticationFilter();
        ReflectionTestUtils.setField(jwtAuthenticationFilter, "jwtSecret", TEST_SECRET);
        ReflectionTestUtils.setField(
                Objects.requireNonNull(jwtAuthenticationFilter), "jwtEnabled", true);
        SecurityContextHolder.clearContext();
    }

    private String createValidToken() {
        SecretKey key = Keys.hmacShaKeyFor(TEST_SECRET.getBytes(StandardCharsets.UTF_8));
        return Jwts.builder()
                .subject("admin")
                .claim("roles", java.util.List.of("ROLE_ADMIN"))
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + 3600_000))
                .signWith(key)
                .compact();
    }

    @Test
    @DisplayName("白名单路径应直接放行")
    void publicPath_shouldSkipAuthentication() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/auth/login");
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response,
                Objects.requireNonNull(filterChain));

        verify(filterChain, times(1)).doFilter(request, response);
        assertNull(SecurityContextHolder.getContext().getAuthentication());
    }

    @Test
    @DisplayName("健康检查路径应直接放行")
    void healthPath_shouldSkipAuthentication() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/actuator/health");
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response,
                Objects.requireNonNull(filterChain));

        verify(filterChain, times(1)).doFilter(request, response);
    }

    @Test
    @DisplayName("缺少 Authorization 头应返回 401")
    void missingAuthHeader_shouldReturn401() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/drones");
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response,
                Objects.requireNonNull(filterChain));

        assertEquals(401, response.getStatus());
        verify(filterChain, never()).doFilter(request, response);
    }

    @Test
    @DisplayName("无效 Token 应返回 401")
    void invalidToken_shouldReturn401() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/drones");
        request.addHeader("Authorization", "Bearer invalid-token");
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response,
                Objects.requireNonNull(filterChain));

        assertEquals(401, response.getStatus());
        verify(filterChain, never()).doFilter(request, response);
    }

    @Test
    @DisplayName("有效的 Token 应设置认证上下文")
    void validToken_shouldSetAuthentication() throws Exception {
        String token = createValidToken();
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/drones");
        request.addHeader("Authorization", "Bearer " + token);
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response,
                Objects.requireNonNull(filterChain));

        verify(filterChain, times(1)).doFilter(request, response);
        assertNotNull(SecurityContextHolder.getContext().getAuthentication());
        assertEquals("admin", SecurityContextHolder.getContext().getAuthentication().getPrincipal());
    }
}
