package com.uav.common.security.rbac;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.stereotype.Component;

import java.io.Serializable;
import java.util.Collection;
import java.util.List;

/**
 * RBAC 权限评估器
 * <p>
 * 支持 SpEL 表达式中的自定义权限检查方法，可在 {@code @PreAuthorize} 中使用：
 * <ul>
 *     <li>{@code @PreAuthorize("hasPermission('api:v1:planning:POST:path', 'API')")}</li>
 *     <li>{@code @PreAuthorize("hasRole('ADMIN')")}</li>
 *     <li>{@code @PreAuthorize("hasAnyPermission({'api:v1:planning:GET:tasks', 'api:v1:planning:POST:path'}, 'API')")}</li>
 * </ul>
 */
@Slf4j
@Component("rbacPermissionEvaluator")
@ConditionalOnBean(RbacUserRepository.class)
public class RbacPermissionEvaluator implements org.springframework.security.access.PermissionEvaluator {

    @Override
    public boolean hasPermission(Authentication authentication,
                                Object targetDomainObject,
                                Object permission) {
        if (authentication == null || !authentication.isAuthenticated()) {
            return false;
        }

        Collection<? extends GrantedAuthority> authorities = authentication.getAuthorities();

        // 权限格式：resourceType:resourceKey
        String requiredAuthority = permission + ":" + targetDomainObject;

        return authorities.stream()
                .anyMatch(auth -> auth.getAuthority().equals(requiredAuthority));
    }

    @Override
    public boolean hasPermission(Authentication authentication,
                                Serializable targetId,
                                String targetType,
                                Object permission) {
        if (authentication == null || !authentication.isAuthenticated()) {
            return false;
        }

        Collection<? extends GrantedAuthority> authorities = authentication.getAuthorities();

        // 权限格式：resourceType:resourceKey
        String requiredAuthority = targetType + ":" + permission;

        return authorities.stream()
                .anyMatch(auth -> auth.getAuthority().equals(requiredAuthority));
    }

    /**
     * 检查是否拥有任意一个指定权限
     *
     * @param authentication 当前认证信息
     * @param permissions    权限列表（格式：resourceType:resourceKey）
     * @return 是否拥有任意一个权限
     */
    public boolean hasAnyPermission(Authentication authentication, List<String> permissions) {
        if (authentication == null || !authentication.isAuthenticated()) {
            return false;
        }

        Collection<? extends GrantedAuthority> authorities = authentication.getAuthorities();
        return permissions.stream()
                .anyMatch(perm -> authorities.stream()
                        .anyMatch(auth -> auth.getAuthority().equals(perm)));
    }
}
