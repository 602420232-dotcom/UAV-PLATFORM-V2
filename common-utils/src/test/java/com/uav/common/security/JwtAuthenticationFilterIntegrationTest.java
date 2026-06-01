package com.uav.common.security;

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

import jakarta.servlet.FilterChain;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
@DisplayName("JwtAuthenticationFilter 集成测试")
class JwtAuthenticationFilterIntegrationTest {

    @Mock
    private JwtTokenProvider jwtTokenProvider;

    @Mock
    private JwtProperties jwtProperties;

    @Mock
    private FilterChain filterChain;

    private JwtAuthenticationFilter jwtAuthenticationFilter;

    @BeforeEach
    void setUp() {
        when(jwtProperties.isEnabled()).thenReturn(true);
        when(jwtProperties.getHeader()).thenReturn("Authorization");
        when(jwtProperties.getTokenPrefix()).thenReturn("Bearer ");
        jwtAuthenticationFilter = new JwtAuthenticationFilter(jwtTokenProvider, jwtProperties, Optional.empty());
        SecurityContextHolder.clearContext();
    }

    @Test
    @DisplayName("白名单路径应直接放行")
    void publicPath_shouldSkipAuthentication() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/auth/login");
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        verify(filterChain, times(1)).doFilter(request, response);
        assertNull(SecurityContextHolder.getContext().getAuthentication());
    }

    @Test
    @DisplayName("健康检查路径应直接放行")
    void healthPath_shouldSkipAuthentication() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/actuator/health");
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        verify(filterChain, times(1)).doFilter(request, response);
    }

    @Test
    @DisplayName("缺少 Authorization 头应返回 401")
    void missingAuthHeader_shouldReturn401() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/drones");
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        assertEquals(401, response.getStatus());
        verify(filterChain, never()).doFilter(request, response);
    }

    @Test
    @DisplayName("无效 Token 应返回 401")
    void invalidToken_shouldReturn401() throws Exception {
        when(jwtTokenProvider.validateAndGetClaims("invalid-token")).thenThrow(new RuntimeException("Invalid token"));

        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/drones");
        request.addHeader("Authorization", "Bearer invalid-token");
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        assertEquals(401, response.getStatus());
        verify(filterChain, never()).doFilter(request, response);
    }

    @Test
    @DisplayName("有效的 Token 应设置认证上下文")
    void validToken_shouldSetAuthentication() throws Exception {
        String token = "valid.jwt.token";
        io.jsonwebtoken.Claims claims = mock(io.jsonwebtoken.Claims.class);
        when(claims.getSubject()).thenReturn("admin");
        when(claims.get("tenant_id", String.class)).thenReturn("tenant-001");
        when(claims.get("roles", java.util.List.class)).thenReturn(java.util.List.of("ROLE_ADMIN"));
        when(jwtTokenProvider.validateAndGetClaims(token)).thenReturn(claims);

        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/drones");
        request.addHeader("Authorization", "Bearer " + token);
        MockHttpServletResponse response = new MockHttpServletResponse();

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        verify(filterChain, times(1)).doFilter(request, response);
        assertNotNull(SecurityContextHolder.getContext().getAuthentication());
        assertEquals("admin", SecurityContextHolder.getContext().getAuthentication().getPrincipal());
    }
}
