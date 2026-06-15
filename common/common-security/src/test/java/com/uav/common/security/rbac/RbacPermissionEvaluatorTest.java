package com.uav.common.security.rbac;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * RBAC 权限评估器单元测试
 */
@DisplayName("RbacPermissionEvaluator 权限评估测试")
@ExtendWith(MockitoExtension.class)
class RbacPermissionEvaluatorTest {

    private RbacPermissionEvaluator evaluator;

    @Mock
    private Authentication authentication;

    @BeforeEach
    void setUp() {
        evaluator = new RbacPermissionEvaluator();
    }

    @SuppressWarnings("unchecked")
    private void mockAuthorities(String... authorityStrings) {
        List<GrantedAuthority> list = new ArrayList<>();
        for (String auth : authorityStrings) {
            list.add(new SimpleGrantedAuthority(auth));
        }
        doReturn(list).when(authentication).getAuthorities();
    }

    @Test
    @DisplayName("hasPermission 应返回 true 当用户拥有匹配权限")
    void hasPermissionShouldReturnTrueWhenAuthorityMatches() {
        when(authentication.isAuthenticated()).thenReturn(true);
        mockAuthorities("API:api:v1:planning:POST:path");

        boolean result = evaluator.hasPermission(authentication, "api:v1:planning:POST:path", "API");

        assertTrue(result);
        verify(authentication).getAuthorities();
    }

    @Test
    @DisplayName("hasPermission 应返回 false 当用户权限不匹配")
    void hasPermissionShouldReturnFalseWhenAuthorityDoesNotMatch() {
        when(authentication.isAuthenticated()).thenReturn(true);
        mockAuthorities("API:api:v1:weather:GET:data");

        boolean result = evaluator.hasPermission(authentication, "api:v1:planning:POST:path", "API");

        assertFalse(result);
    }

    @Test
    @DisplayName("hasPermission 应返回 false 当 authentication 为 null")
    void hasPermissionShouldReturnFalseWhenAuthenticationIsNull() {
        boolean result = evaluator.hasPermission(null, "resource", "API");

        assertFalse(result);
    }

    @Test
    @DisplayName("hasPermission 应返回 false 当用户未认证")
    void hasPermissionShouldReturnFalseWhenNotAuthenticated() {
        when(authentication.isAuthenticated()).thenReturn(false);

        boolean result = evaluator.hasPermission(authentication, "resource", "API");

        assertFalse(result);
        verify(authentication, never()).getAuthorities();
    }

    @Test
    @DisplayName("hasPermission 四参数版本应返回 true 当权限匹配")
    void hasPermissionFourArgsShouldReturnTrueWhenMatches() {
        when(authentication.isAuthenticated()).thenReturn(true);
        mockAuthorities("RESOURCE:READ");

        boolean result = evaluator.hasPermission(authentication, (Serializable) 1L, "RESOURCE", "READ");

        assertTrue(result);
    }

    @Test
    @DisplayName("hasPermission 四参数版本应返回 false 当权限不匹配")
    void hasPermissionFourArgsShouldReturnFalseWhenNotMatches() {
        when(authentication.isAuthenticated()).thenReturn(true);
        mockAuthorities("RESOURCE:WRITE");

        boolean result = evaluator.hasPermission(authentication, (Serializable) 1L, "RESOURCE", "READ");

        assertFalse(result);
    }

    @Test
    @DisplayName("hasAnyPermission 应返回 true 当拥有任意一个权限")
    void hasAnyPermissionShouldReturnTrueWhenAnyMatches() {
        when(authentication.isAuthenticated()).thenReturn(true);
        mockAuthorities("API:read", "API:write");

        List<String> permissions = List.of("API:delete", "API:write", "API:admin");
        boolean result = evaluator.hasAnyPermission(authentication, permissions);

        assertTrue(result);
    }

    @Test
    @DisplayName("hasAnyPermission 应返回 false 当没有任何权限匹配")
    void hasAnyPermissionShouldReturnFalseWhenNoneMatches() {
        when(authentication.isAuthenticated()).thenReturn(true);
        mockAuthorities("API:read");

        List<String> permissions = List.of("API:delete", "API:admin");
        boolean result = evaluator.hasAnyPermission(authentication, permissions);

        assertFalse(result);
    }

    @Test
    @DisplayName("hasAnyPermission 应返回 false 当权限列表为空")
    void hasAnyPermissionShouldReturnFalseWhenPermissionListIsEmpty() {
        when(authentication.isAuthenticated()).thenReturn(true);
        mockAuthorities("API:read");

        boolean result = evaluator.hasAnyPermission(authentication, Collections.emptyList());

        assertFalse(result);
    }

    @Test
    @DisplayName("hasAnyPermission 应返回 false 当 authentication 为 null")
    void hasAnyPermissionShouldReturnFalseWhenAuthenticationIsNull() {
        List<String> permissions = List.of("API:read");
        boolean result = evaluator.hasAnyPermission(null, permissions);

        assertFalse(result);
    }

    @Test
    @DisplayName("未知资源类型权限检查应返回 false")
    void unknownResourceTypeShouldReturnFalse() {
        when(authentication.isAuthenticated()).thenReturn(true);
        mockAuthorities("UNKNOWN:some:resource");

        boolean result = evaluator.hasPermission(authentication, "other:resource", "API");

        assertFalse(result);
    }
}
