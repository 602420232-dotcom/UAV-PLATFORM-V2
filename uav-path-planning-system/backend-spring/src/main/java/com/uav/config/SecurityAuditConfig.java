package com.uav.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.logout.LogoutHandler;
import org.springframework.security.web.authentication.logout.LogoutSuccessHandler;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Configuration
@EnableMethodSecurity
public class SecurityAuditConfig {

    private static final Logger logger = LoggerFactory.getLogger(SecurityAuditConfig.class);

    @Bean
    public LogoutHandler securityAuditLogoutHandler() {
        return (request, response, authentication) -> {
            if (authentication != null) {
                String username = authentication.getName();
                logger.info("用户登出: " + username + "，IP: " + request.getRemoteAddr());
            }
        };
    }

    @Bean
    public LogoutSuccessHandler securityAuditLogoutSuccessHandler() {
        return (request, response, authentication) -> {
            if (authentication != null) {
                String username = authentication.getName();
                logger.info("用户登出成功: " + username);
            }
            response.sendRedirect("/login");
        };
    }

    public static void logAuthenticationSuccess(String username, HttpServletRequest request) {
        logger.info("用户登录成功: " + username + "，IP: " + request.getRemoteAddr());
    }

    public static void logAuthenticationFailure(String username, String error, HttpServletRequest request) {
        logger.warn("用户登录失败: " + username + "，错误: " + error + "，IP: " + request.getRemoteAddr());
    }

    public static void logAuthorizationDenied(String username, String resource, HttpServletRequest request) {
        logger.warn("用户访问被拒绝: " + username + "，资源: " + resource + "，IP: " + request.getRemoteAddr());
    }

    public static void logUserActivity(String username, String activity, String details) {
        logger.info("用户活动: " + username + "，操作: " + activity + "，详情: " + details);
    }

    public static String getCurrentUsername() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.isAuthenticated()) {
            return authentication.getName();
        }
        return "anonymous";
    }
}
