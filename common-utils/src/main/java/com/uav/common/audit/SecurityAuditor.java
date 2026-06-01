package com.uav.common.audit;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class SecurityAuditor {

    private static final Logger AUDIT_LOG = LoggerFactory.getLogger(SecurityAuditor.class);
    private static final List<AuditEntry> auditEntries = new ArrayList<>();
    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final int MAX_ENTRIES = 10000;

    public static String getCurrentUsername() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.isAuthenticated() && !"anonymousUser".equals(auth.getPrincipal())) {
            return auth.getName();
        }
        return "anonymous";
    }

    public static String getClientIp(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        if (forwarded != null && !forwarded.isEmpty()) {
            return forwarded.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }

    public static void logActivity(String username, String operation, String details) {
        AuditEntry entry = new AuditEntry();
        entry.setTimestamp(LocalDateTime.now().format(FORMATTER));
        entry.setUsername(username);
        entry.setOperation(operation);
        entry.setDetails(details);
        entry.setStatus("success");
        addEntry(entry);
        AUDIT_LOG.info("[AUDIT] {} | {} | {} | {}", entry.getTimestamp(), username, operation, details);
    }

    public static void logWarning(String username, String operation, String warning) {
        AuditEntry entry = new AuditEntry();
        entry.setTimestamp(LocalDateTime.now().format(FORMATTER));
        entry.setUsername(username);
        entry.setOperation(operation);
        entry.setDetails(warning);
        entry.setStatus("warning");
        addEntry(entry);
        AUDIT_LOG.warn("[WARNING] {} | {} | {} | {}", entry.getTimestamp(), username, operation, warning);
    }

    public static void logAuthenticationSuccess(String username, HttpServletRequest request) {
        String ip = getClientIp(request);
        AuditEntry entry = new AuditEntry();
        entry.setTimestamp(LocalDateTime.now().format(FORMATTER));
        entry.setUsername(username);
        entry.setOperation("LOGIN_SUCCESS");
        entry.setDetails("ip=" + ip);
        entry.setStatus("success");
        addEntry(entry);
        AUDIT_LOG.info("[AUTH] {} | {} logged in from {}", entry.getTimestamp(), username, ip);
    }

    public static void logAuthenticationFailure(String username, String reason, HttpServletRequest request) {
        String ip = getClientIp(request);
        AuditEntry entry = new AuditEntry();
        entry.setTimestamp(LocalDateTime.now().format(FORMATTER));
        entry.setUsername(username);
        entry.setOperation("LOGIN_FAILURE");
        entry.setDetails("ip=" + ip + ", reason=" + reason);
        entry.setStatus("failure");
        addEntry(entry);
        AUDIT_LOG.warn("[AUTH] {} | {} failed login from {}: {}", entry.getTimestamp(), username, ip, reason);
    }

    public static void logAuthorizationDenied(String username, String resource, HttpServletRequest request) {
        String ip = getClientIp(request);
        AuditEntry entry = new AuditEntry();
        entry.setTimestamp(LocalDateTime.now().format(FORMATTER));
        entry.setUsername(username);
        entry.setOperation("ACCESS_DENIED");
        entry.setDetails("resource=" + resource + ", ip=" + ip);
        entry.setStatus("denied");
        addEntry(entry);
        AUDIT_LOG.warn("[AUTH] {} | {} denied access to {} from {}", entry.getTimestamp(), username, resource, ip);
    }

    public static List<AuditEntry> getAuditEntries() {
        synchronized (auditEntries) {
            return Collections.unmodifiableList(new ArrayList<>(auditEntries));
        }
    }

    public static void clear() {
        synchronized (auditEntries) {
            auditEntries.clear();
        }
    }

    private static void addEntry(AuditEntry entry) {
        synchronized (auditEntries) {
            auditEntries.add(entry);
            while (auditEntries.size() > MAX_ENTRIES) {
                auditEntries.remove(0);
            }
        }
    }

    public static class AuditEntry {
        private String timestamp;
        private String username;
        private String operation;
        private String details;
        private String status;

        public String getTimestamp() { return timestamp; }
        public void setTimestamp(String timestamp) { this.timestamp = timestamp; }
        public String getUsername() { return username; }
        public void setUsername(String username) { this.username = username; }
        public String getOperation() { return operation; }
        public void setOperation(String operation) { this.operation = operation; }
        public String getDetails() { return details; }
        public void setDetails(String details) { this.details = details; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }

        @Override
        public String toString() {
            return timestamp + " | " + username + " | " + operation + " | " + details + " | " + status;
        }
    }
}
