package com.uav.common.security.rbac;

import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.AccessDecisionManager;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.access.ConfigAttribute;
import org.springframework.security.authentication.InsufficientAuthenticationException;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

import java.util.Collection;

/**
 * RBAC 访问决策管理器
 * <p>
 * 在 FilterSecurityInterceptor 中使用，对受保护的资源进行权限校验。
 * 支持三种决策模式：
 * <ul>
 *     <li>AFFIRMATIVE：只要有一个投票者通过即放行（默认）</li>
 *     <li>UNANIMOUS：所有投票者一致通过才放行</li>
 *     <li>MAJORITY：多数投票者通过才放行</li>
 * </ul>
 * <p>
 * 当前实现采用 AFFIRMATIVE 模式，即用户拥有所需任一角色或权限即可访问。
 */
@Slf4j
@Component
public class RbacAccessDecisionManager implements AccessDecisionManager {

    @Override
    public void decide(Authentication authentication,
                       Object object,
                       Collection<ConfigAttribute> configAttributes)
            throws AccessDeniedException, InsufficientAuthenticationException {

        // 无需权限校验的资源配置，直接放行
        if (configAttributes == null || configAttributes.isEmpty()) {
            log.debug("无权限要求，直接放行");
            return;
        }

        // 未认证用户拒绝访问
        if (authentication == null || !authentication.isAuthenticated()) {
            log.warn("未认证用户尝试访问受保护资源");
            throw new InsufficientAuthenticationException("用户未认证");
        }

        for (ConfigAttribute configAttribute : configAttributes) {
            String requiredPermission = configAttribute.getAttribute();

            // 检查用户是否拥有所需权限
            boolean hasPermission = authentication.getAuthorities().stream()
                    .anyMatch(authority -> {
                        String grantedAuthority = authority.getAuthority();

                        // 角色匹配：ROLE_ADMIN
                        if (grantedAuthority.equals(requiredPermission)) {
                            return true;
                        }

                        // 通配符匹配：ROLE_ADMIN 可匹配所有权限
                        if ("ROLE_ADMIN".equals(grantedAuthority)) {
                            return true;
                        }

                        // 权限前缀匹配：API:* 匹配所有 API 权限
                        if (requiredPermission.endsWith(":*")) {
                            String prefix = requiredPermission.substring(0, requiredPermission.length() - 1);
                            return grantedAuthority.startsWith(prefix);
                        }

                        return false;
                    });

            if (hasPermission) {
                log.debug("权限校验通过 - required: {}, user: {}", requiredPermission, authentication.getName());
                return;
            }
        }

        log.warn("权限校验失败 - user: {}, required: {}", authentication.getName(), configAttributes);
        throw new AccessDeniedException("权限不足，无法访问该资源");
    }

    @Override
    public boolean supports(ConfigAttribute attribute) {
        return true;
    }

    @Override
    public boolean supports(Class<?> clazz) {
        return true;
    }
}
