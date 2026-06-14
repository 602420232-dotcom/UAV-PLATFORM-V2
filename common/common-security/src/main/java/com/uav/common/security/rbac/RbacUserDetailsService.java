package com.uav.common.security.rbac;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * RBAC 用户详情服务
 * <p>
 * 实现 Spring Security 的 {@link UserDetailsService}，从数据库加载用户信息、
 * 角色和权限，构建 {@link RbacUserDetails} 供认证授权使用。
 */
@Slf4j
@Service
@RequiredArgsConstructor
@ConditionalOnBean(RbacUserRepository.class)
public class RbacUserDetailsService implements UserDetailsService {

    private final RbacUserRepository rbacUserRepository;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        RbacUser user = rbacUserRepository.findByUsernameWithRolesAndPermissions(username);

        if (user == null) {
            log.warn("用户不存在 - username: {}", username);
            throw new UsernameNotFoundException("用户不存在: " + username);
        }

        if (user.getStatus() != null && user.getStatus() != 1) {
            log.warn("用户已被禁用 - username: {}", username);
            throw new UsernameNotFoundException("用户已被禁用: " + username);
        }

        // 收集所有权限（从角色关联中提取）
        List<RbacPermission> permissions = new ArrayList<>();
        for (RbacRole role : user.getRoles()) {
            if (role.getPermissions() != null) {
                permissions.addAll(role.getPermissions());
            }
        }

        return RbacUserDetails.builder()
                .id(user.getId())
                .username(user.getUsername())
                .password(user.getPasswordHash())
                .email(user.getEmail())
                .phone(user.getPhone())
                .status(user.getStatus())
                .roles(new ArrayList<>(user.getRoles()))
                .permissions(permissions)
                .enabled(user.getStatus() == 1)
                .build();
    }
}
