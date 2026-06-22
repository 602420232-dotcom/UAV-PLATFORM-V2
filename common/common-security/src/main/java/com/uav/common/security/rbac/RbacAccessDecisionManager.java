package com.uav.common.security.rbac;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

import jakarta.servlet.http.HttpServletRequest;

/**
 * RBAC 权限检查工具类
 * <p>
 * 提供静态方法用于权限校验，供 {@link RbacPermissionEvaluator} 和其他组件调用。
 * <p>
 * 当前实现采用 AFFIRMATIVE 模式，即用户拥有所需任一角色或权限即可访问。
 * <p>
 * 通过配置属性 {@code security.rbac.enabled=true} 激活。
 */
@Slf4j
@Component
@ConditionalOnBean(RbacUserRepository.class)
public class RbacAccessDecisionManager {

    /**
     * 检查认证用户是否拥有指定权限
     *
     * @param authentication       当前认证信息
     * @param requiredPermission   所需权限字符串
     * @param requestUri           请求URI（用于日志记录）
     * @return 是否授权通过
     */
    public static boolean checkPermission(Authentication authentication, String requiredPermission, String requestUri) {
        if (authentication == null || !authentication.isAuthenticated()) {
            log.warn("未认证用户尝试访问受保护资源: {}", requestUri);
            return false;
        }

        if (requiredPermission == null || requiredPermission.isEmpty()) {
            log.debug("无权限要求，直接放行: {}", requestUri);
            return true;
        }

        boolean hasPermission = authentication.getAuthorities().stream()
                .anyMatch(authority -> {
                    String grantedAuthority = authority.getAuthority();

                    // 精确匹配
                    if (grantedAuthority.equals(requiredPermission)) {
                        return true;
                    }

                    // 超级管理员角色匹配所有权限
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
        } else {
            log.warn("权限校验失败 - user: {}, required: {}", authentication.getName(), requiredPermission);
        }

        return hasPermission;
    }

    /**
     * 检查认证用户是否拥有指定权限（基于 HttpServletRequest）
     *
     * @param authentication 当前认证信息
     * @param request        HTTP 请求
     * @return 是否授权通过
     */
    public static boolean checkPermission(Authentication authentication, HttpServletRequest request) {
        Object requiredAttr = request.getAttribute("required_permission");
        String requiredPermission = requiredAttr != null ? requiredAttr.toString() : null;
        return checkPermission(authentication, requiredPermission, request.getRequestURI());
    }
}
