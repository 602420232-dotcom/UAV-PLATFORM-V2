package com.uav.controller;

import com.uav.config.JwtUtil;
import com.uav.config.SecurityAuditConfig;
import com.uav.repository.RoleRepository;
import com.uav.repository.UserRepository;
import com.uav.service.CustomUserDetailsService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import jakarta.servlet.http.HttpServletRequest;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("AuthController认证测试")
class AuthControllerTest {

    @Mock
    private AuthenticationManager authenticationManager;

    @Mock
    private CustomUserDetailsService userDetailsService;

    @Mock
    private JwtUtil jwtUtil;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private SecurityAuditConfig securityAuditConfig;

    @Mock
    private UserRepository userRepository;

    @Mock
    private RoleRepository roleRepository;

    @Mock
    private HttpServletRequest httpServletRequest;

    @InjectMocks
    private AuthController authController;

    private com.uav.dto.request.LoginRequest validRequest;

    @BeforeEach
    void setUp() {
        validRequest = new com.uav.dto.request.LoginRequest();
        validRequest.setUsername("testuser");
        validRequest.setPassword("testpass");
    }

    @Test
    @DisplayName("测试错误凭证处理")
    void testLoginWithBadCredentials() throws Exception {
        doThrow(new BadCredentialsException("Bad credentials"))
            .when(authenticationManager)
            .authenticate(any());

        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        Map<?, ?> body = (Map<?, ?>) response.getBody();
        assertEquals(401, body.get("code"));
        assertEquals("用户名或密码错误", body.get("message"));
        verify(securityAuditConfig).logAuthenticationFailure(eq("testuser"), eq("凭证错误"), any());
    }

    @Test
    @DisplayName("测试禁用账户处理")
    void testLoginWithDisabledAccount() throws Exception {
        doThrow(new DisabledException("Account disabled"))
            .when(authenticationManager)
            .authenticate(any());

        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        assertEquals(HttpStatus.FORBIDDEN, response.getStatusCode());
        Map<?, ?> body = (Map<?, ?>) response.getBody();
        assertEquals(403, body.get("code"));
        assertEquals("账户已被禁用", body.get("message"));
        verify(securityAuditConfig).logAuthenticationFailure(eq("testuser"), eq("账户已禁用"), any());
    }

    @Test
    @DisplayName("测试锁定账户处理")
    void testLoginWithLockedAccount() throws Exception {
        doThrow(new LockedException("Account locked"))
            .when(authenticationManager)
            .authenticate(any());

        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        assertEquals(HttpStatus.FORBIDDEN, response.getStatusCode());
        Map<?, ?> body = (Map<?, ?>) response.getBody();
        assertEquals(403, body.get("code"));
        assertEquals("账户已被锁定", body.get("message"));
        verify(securityAuditConfig).logAuthenticationFailure(eq("testuser"), eq("账户已锁定"), any());
    }

    @Test
    @DisplayName("测试用户不存在处理")
    void testLoginWithNonExistentUser() throws Exception {
        doThrow(new UsernameNotFoundException("User not found"))
            .when(authenticationManager)
            .authenticate(any());

        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        Map<?, ?> body = (Map<?, ?>) response.getBody();
        assertEquals(401, body.get("code"));
        assertEquals("用户名或密码错误", body.get("message"));
        verify(securityAuditConfig).logAuthenticationFailure(eq("testuser"), eq("凭证错误"), any());
    }

    @Test
    @DisplayName("测试成功登录")
    void testSuccessfulLogin() throws Exception {
        when(authenticationManager.authenticate(any())).thenReturn(mock(org.springframework.security.core.Authentication.class));

        UserDetails userDetails = org.springframework.security.core.userdetails.User.builder()
            .username("testuser")
            .password("password")
            .authorities(java.util.Collections.emptyList())
            .build();

        when(userDetailsService.loadUserByUsername("testuser")).thenReturn(userDetails);
        when(jwtUtil.generateAccessToken(any(), any(), any())).thenReturn("test-token");

        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        verify(securityAuditConfig).logAuthenticationSuccess(eq("testuser"), any());
    }
}
