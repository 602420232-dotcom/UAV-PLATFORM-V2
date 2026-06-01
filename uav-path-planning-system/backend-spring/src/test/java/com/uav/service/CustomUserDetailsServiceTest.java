package com.uav.service;

import com.uav.model.Role;
import com.uav.model.User;
import com.uav.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;

import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

/**
 * CustomUserDetailsService单元测试
 */
@ExtendWith(MockitoExtension.class)
class CustomUserDetailsServiceTest {

    @Mock
    private UserRepository userRepository;

    private CustomUserDetailsService service;

    @BeforeEach
    void setUp() {
        service = new CustomUserDetailsService(userRepository);
    }

    @Test
    @DisplayName("加载用户成功 - 包含角色")
    void loadUserByUsername_Success() {
        Role role = new Role();
        role.setId(1L);
        role.setName("ADMIN");
        role.setDescription("管理员");

        Set<Role> roles = new HashSet<>();
        roles.add(role);

        User user = new User();
        user.setId(1L);
        user.setUsername("testuser");
        user.setPassword("encodedPassword");
        user.setEmail("test@example.com");
        user.setFullName("Test User");
        user.setEnabled(true);
        user.setAccountNonExpired(true);
        user.setAccountNonLocked(true);
        user.setCredentialsNonExpired(true);
        user.setRoles(roles);

        when(userRepository.findByUsername("testuser")).thenReturn(Optional.of(user));

        UserDetails result = service.loadUserByUsername("testuser");

        assertNotNull(result);
        assertEquals("testuser", result.getUsername());
        assertEquals("encodedPassword", result.getPassword());
        assertTrue(result.isEnabled());
        assertTrue(result.isAccountNonExpired());
        assertTrue(result.isAccountNonLocked());
        assertTrue(result.isCredentialsNonExpired());

        var authorities = result.getAuthorities();
        assertTrue(authorities.contains(new SimpleGrantedAuthority("ROLE_ADMIN")));
    }

    @Test
    @DisplayName("用户不存在时抛出异常")
    void loadUserByUsername_UserNotFound() {
        when(userRepository.findByUsername(anyString())).thenReturn(Optional.empty());

        assertThrows(UsernameNotFoundException.class, () ->
            service.loadUserByUsername("nonexistent"));
    }

    @Test
    @DisplayName("禁用账户加载为disabled状态")
    void loadUserByUsername_DisabledAccount() {
        Role role = new Role();
        role.setId(1L);
        role.setName("USER");
        role.setDescription("普通用户");

        Set<Role> roles = new HashSet<>();
        roles.add(role);

        User user = new User();
        user.setId(1L);
        user.setUsername("disableduser");
        user.setPassword("encodedPassword");
        user.setEnabled(false);
        user.setRoles(roles);

        when(userRepository.findByUsername("disableduser")).thenReturn(Optional.of(user));

        UserDetails result = service.loadUserByUsername("disableduser");

        assertNotNull(result);
        assertFalse(result.isEnabled());
    }
}
