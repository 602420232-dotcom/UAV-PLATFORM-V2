package com.uav.config;

import com.uav.common.audit.SecurityAuditor;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Component;

@Component
public class SecurityAuditConfig {

    public static String getCurrentUsername() {
        return SecurityAuditor.getCurrentUsername();
    }

    public static void logUserActivity(String username, String operation, String details) {
        SecurityAuditor.logActivity(username, operation, details);
    }

    public static void logSecurityWarning(String username, String operation, String warning) {
        SecurityAuditor.logWarning(username, operation, warning);
    }

    public static void logAuthenticationSuccess(String username, HttpServletRequest request) {
        SecurityAuditor.logAuthenticationSuccess(username, request);
    }

    public static void logAuthenticationFailure(String username, String reason, HttpServletRequest request) {
        SecurityAuditor.logAuthenticationFailure(username, reason, request);
    }
}
