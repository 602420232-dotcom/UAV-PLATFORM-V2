package com.uav.controller;

import com.uav.common.exception.BusinessException;
import com.uav.config.JwtUtil;
import com.uav.config.SecurityAuditConfig;
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
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import jakarta.servlet.http.HttpServletRequest;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * AuthController单元测试
 *
 * <p>测试认证控制器的异常处理和输入验证：
 * <ul>
 *   <li>空用户名/密码验证</li>
 *   <li>错误凭证处理</li>
 *   <li>账户状态处理</li>
 * </ul>
 *
 * @author UAV Team
 * @version 1.0.0
 */
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
    private HttpServletRequest httpServletRequest;

    @InjectMocks
    private AuthController authController;

    private Map<String, String> validRequest;

    @BeforeEach
    void setUp() {
        validRequest = new HashMap<>();
        validRequest.put("username", "testuser");
        validRequest.put("password", "testpass");
    }

    @Test
    @DisplayName("测试空用户名验证")
    void testLoginWithEmptyUsername() {
        // Given
        Map<String, String> request = new HashMap<>();
        request.put("username", "");
        request.put("password", "testpass");

        // When & Then
        BusinessException exception = assertThrows(BusinessException.class, () -> {
            authController.login(request, httpServletRequest);
        });

        assertEquals("VALIDATION_ERROR", exception.getErrorCode());
        assertTrue(exception.getMessage().contains("用户名不能为空"));
    }

    @Test
    @DisplayName("测试null用户名验证")
    void testLoginWithNullUsername() {
        // Given
        Map<String, String> request = new HashMap<>();
        request.put("username", null);
        request.put("password", "testpass");

        // When & Then
        BusinessException exception = assertThrows(BusinessException.class, () -> {
            authController.login(request, httpServletRequest);
        });

        assertEquals("VALIDATION_ERROR", exception.getErrorCode());
        assertTrue(exception.getMessage().contains("用户名不能为空"));
    }

    @Test
    @DisplayName("测试空密码验证")
    void testLoginWithEmptyPassword() {
        // Given
        Map<String, String> request = new HashMap<>();
        request.put("username", "testuser");
        request.put("password", "");

        // When & Then
        BusinessException exception = assertThrows(BusinessException.class, () -> {
            authController.login(request, httpServletRequest);
        });

        assertEquals("VALIDATION_ERROR", exception.getErrorCode());
        assertTrue(exception.getMessage().contains("密码不能为空"));
    }

    @Test
    @DisplayName("测试空白密码验证")
    void testLoginWithBlankPassword() {
        // Given
        Map<String, String> request = new HashMap<>();
        request.put("username", "testuser");
        request.put("password", "   ");

        // When & Then
        BusinessException exception = assertThrows(BusinessException.class, () -> {
            authController.login(request, httpServletRequest);
        });

        assertEquals("VALIDATION_ERROR", exception.getErrorCode());
        assertTrue(exception.getMessage().contains("密码不能为空"));
    }

    @Test
    @DisplayName("测试错误凭证处理")
    void testLoginWithBadCredentials() throws Exception {
        // Given
        doThrow(new BadCredentialsException("Bad credentials"))
            .when(authenticationManager)
            .authenticate(any());

        // When
        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        // Then
        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        assertEquals("用户名或密码错误", response.getBody());
        verify(SecurityAuditConfig).logAuthenticationFailure(eq("testuser"), eq("密码错误"), any());
    }

    @Test
    @DisplayName("测试禁用账户处理")
    void testLoginWithDisabledAccount() throws Exception {
        // Given
        doThrow(new DisabledException("Account disabled"))
            .when(authenticationManager)
            .authenticate(any());

        // When
        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        // Then
        assertEquals(HttpStatus.FORBIDDEN, response.getStatusCode());
        assertEquals("账户已被禁用", response.getBody());
        verify(SecurityAuditConfig).logAuthenticationFailure(eq("testuser"), eq("账户已禁用"), any());
    }

    @Test
    @DisplayName("测试锁定账户处理")
    void testLoginWithLockedAccount() throws Exception {
        // Given
        doThrow(new LockedException("Account locked"))
            .when(authenticationManager)
            .authenticate(any());

        // When
        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        // Then
        assertEquals(HttpStatus.FORBIDDEN, response.getStatusCode());
        assertEquals("账户已被锁定", response.getBody());
        verify(SecurityAuditConfig).logAuthenticationFailure(eq("testuser"), eq("账户已锁定"), any());
    }

    @Test
    @DisplayName("测试用户不存在处理")
    void testLoginWithNonExistentUser() throws Exception {
        // Given
        doThrow(new UsernameNotFoundException("User not found"))
            .when(authenticationManager)
            .authenticate(any());

        // When
        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        // Then
        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        assertEquals("用户名或密码错误", response.getBody());
        verify(SecurityAuditConfig).logAuthenticationFailure(eq("testuser"), eq("用户不存在"), any());
    }

    @Test
    @DisplayName("测试成功登录")
    void testSuccessfulLogin() throws Exception {
        // Given
        doNothing().when(authenticationManager).authenticate(any());

        User userDetails = new User("testuser", "password",
            java.util.Collections.emptyList());
        when(userDetailsService.loadUserByUsername("testuser")).thenReturn(userDetails);
        when(jwtUtil.generateToken(userDetails)).thenReturn("test-token");

        // When
        ResponseEntity<?> response = authController.login(validRequest, httpServletRequest);

        // Then
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        verify(SecurityAuditConfig).logAuthenticationSuccess(eq("testuser"), any());
    }
}
