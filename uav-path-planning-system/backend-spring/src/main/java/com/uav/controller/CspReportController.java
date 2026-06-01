package com.uav.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

/**
 * CSP (Content Security Policy) 违规报告接收端点
 *
 * 接收浏览器上报的 CSP 违规报告，记录到日志用于安全分析。
 * 配合 nginx 的 Content-Security-Policy-Report-Only 头部使用。
 *
 * 使用方法：
 * 1. 浏览器自动 POST JSON 到 /api/csp-violation-report
 * 2. 报告格式遵循 CSP Level 2/3 标准
 * 3. 日志记录后可接入告警或 SIEM 系统
 */
@Slf4j
@RestController
public class CspReportController {

    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final String CSP_REPORT_LOG = "[CSP_VIOLATION]";
    private final ObjectMapper objectMapper;

    public CspReportController(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    /**
     * 接收 CSP 违规报告 (CSP Level 2 格式)
     * Content-Type: application/csp-report
     */
    @PostMapping(
        value = "/api/csp-violation-report",
        consumes = {"application/csp-report", MediaType.APPLICATION_JSON_VALUE}
    )
    public ResponseEntity<Map<String, String>> receiveCspReport(
            @RequestBody(required = false) Map<String, Object> body,
            HttpServletRequest request) {
        
        try {
            if (body == null || body.isEmpty()) {
                log.warn("{} 收到空报告，来源: {}", CSP_REPORT_LOG, request.getRemoteAddr());
                return ResponseEntity.ok(Map.of("status", "received"));
            }

            log.warn("========================================");
            log.warn("{} CSP 违规报告", CSP_REPORT_LOG);
            log.warn("时间: {}", LocalDateTime.now().format(FORMATTER));
            log.warn("来源IP: {}", request.getRemoteAddr());

            Object cspReport = body.get("csp-report");
            if (cspReport instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> report = (Map<String, Object>) cspReport;
                logCspReport(report);
            } else {
                log.warn("{} 报告体: {}", CSP_REPORT_LOG, objectMapper.writeValueAsString(body));
            }

            log.warn("========================================");

            return ResponseEntity.ok(Map.of("status", "received"));

        } catch (Exception e) {
            log.error("{} 处理CSP报告失败", CSP_REPORT_LOG, e);
            return ResponseEntity.ok(Map.of("status", "received"));
        }
    }

    private void logCspReport(Map<String, Object> report) {
        String documentUri = safeStr(report.get("document-uri"));
        String blockedUri = safeStr(report.get("blocked-uri"));
        String violatedDirective = safeStr(report.get("violated-directive"));
        String effectiveDirective = safeStr(report.get("effective-directive"));
        String originalPolicy = safeStr(report.get("original-policy"));
        String disposition = safeStr(report.get("disposition"));
        String scriptSample = safeStr(report.get("script-sample"));
        String statusCode = safeStr(report.get("status-code"));
        String sourceFile = safeStr(report.get("source-file"));
        String lineNumber = safeStr(report.get("line-number"));
        String columnNumber = safeStr(report.get("column-number"));

        log.warn("{} 违规指令: {}", CSP_REPORT_LOG, violatedDirective);
        log.warn("{} 来源文档: {}", CSP_REPORT_LOG, documentUri);
        log.warn("{} 被拦截资源: {}", CSP_REPORT_LOG, blockedUri);
        log.warn("{} 生效指令: {}", CSP_REPORT_LOG, effectiveDirective);
        if (scriptSample != null && !scriptSample.isEmpty()) {
            log.warn("{} 脚本样本: {}", CSP_REPORT_LOG, scriptSample);
        }
        if (sourceFile != null && !sourceFile.isEmpty()) {
            log.warn("{} 源文件: {} ({}:{})", CSP_REPORT_LOG, sourceFile, lineNumber, columnNumber);
        }
        log.warn("{} 原始策略: {}", CSP_REPORT_LOG, originalPolicy);
        log.warn("{} 处置方式: {}", CSP_REPORT_LOG, disposition);
        log.warn("{} HTTP状态码: {}", CSP_REPORT_LOG, statusCode);

        // 严重级别分类
        String severity = classifySeverity(violatedDirective, blockedUri);
        log.warn("{} 严重级别: {}", CSP_REPORT_LOG, severity);
    }

    /**
     * 根据违规类型分类严重级别
     */
    private String classifySeverity(String violatedDirective, String blockedUri) {
        if (violatedDirective == null) return "INFO";

        if (violatedDirective.contains("script-src")) {
            if (blockedUri != null && blockedUri.startsWith("data:")) {
                return "HIGH - 内联脚本执行";
            }
            return "MEDIUM - 脚本资源";
        }
        if (violatedDirective.contains("frame-ancestors")) {
            return "HIGH - 点击劫持";
        }
        if (violatedDirective.contains("connect-src")) {
            return "MEDIUM - 外部连接";
        }
        if (violatedDirective.contains("base-uri")) {
            return "HIGH - base URI 篡改";
        }
        if (violatedDirective.contains("form-action")) {
            return "MEDIUM - 表单提交";
        }
        return "LOW - " + violatedDirective;
    }

    private String safeStr(Object value) {
        return value != null ? value.toString() : null;
    }
}
