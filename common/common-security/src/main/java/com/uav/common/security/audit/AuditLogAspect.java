package com.uav.common.security.audit;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.security.rbac.RbacUserDetails;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.core.annotation.Order;
import org.springframework.expression.EvaluationContext;
import org.springframework.expression.Expression;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.expression.spel.support.StandardEvaluationContext;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 审计日志 AOP 切面
 * <p>
 * 自动拦截标记了 {@link Auditable} 注解的方法，记录操作日志到数据库。
 * 支持从 SpEL 表达式中提取操作详情，自动获取当前用户和请求 IP。
 * <p>
 * 切面优先级较高（Order=10），确保在业务逻辑前后正确记录。
 */
@Slf4j
@Aspect
@Component
@Order(10)
@RequiredArgsConstructor
public class AuditLogAspect {

    private final AuditLogService auditLogService;
    private final ObjectMapper objectMapper;
    private final SpelExpressionParser spelParser = new SpelExpressionParser();

    /**
     * 环绕通知：拦截 @Auditable 标记的方法
     */
    @Around("@annotation(auditable)")
    public Object around(ProceedingJoinPoint joinPoint, Auditable auditable) throws Throwable {
        // 构建审计日志
        AuditLog.AuditLogBuilder logBuilder = AuditLog.builder();

        // 提取当前用户信息
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof RbacUserDetails userDetails) {
            logBuilder.userId(userDetails.getId());
        }

        // 提取请求 IP
        String ipAddress = getClientIpAddress();
        logBuilder.ipAddress(ipAddress);

        // 设置操作基本信息
        logBuilder.action(auditable.action());
        logBuilder.resource(auditable.resource());
        logBuilder.createdAt(LocalDateTime.now());

        // 解析 SpEL 表达式获取详情
        String detail = resolveSpelDetail(auditable.detail(), joinPoint);
        logBuilder.detail(detail);

        // 构建操作详情 JSON（包含参数信息）
        if (auditable.recordParams()) {
            String paramsJson = buildParamsJson(joinPoint);
            if (detail == null || detail.isBlank()) {
                logBuilder.detail(paramsJson);
            } else {
                logBuilder.detail(detail + " | params: " + paramsJson);
            }
        }

        Object result;
        try {
            // 执行目标方法
            result = joinPoint.proceed();

            // 记录返回结果（如果配置）
            if (auditable.recordResult() && result != null) {
                String resultJson = toJsonSafe(result);
                String currentDetail = logBuilder.build().getDetail();
                logBuilder.detail(currentDetail + " | result: " + resultJson);
            }

            // 保存审计日志
            auditLogService.save(logBuilder.build());

        } catch (Throwable e) {
            // 异常时也记录审计日志
            if (auditable.recordOnFailure()) {
                String currentDetail = logBuilder.build().getDetail();
                logBuilder.detail(currentDetail + " | error: " + e.getMessage());
                auditLogService.save(logBuilder.build());
            }
            throw e;
        }

        return result;
    }

    /**
     * 解析 SpEL 表达式获取操作详情
     *
     * @param spelExpression SpEL 表达式
     * @param joinPoint      切点信息
     * @return 解析后的字符串
     */
    private String resolveSpelDetail(String spelExpression, ProceedingJoinPoint joinPoint) {
        if (spelExpression == null || spelExpression.isBlank()) {
            return null;
        }

        try {
            MethodSignature signature = (MethodSignature) joinPoint.getSignature();
            String[] paramNames = signature.getParameterNames();
            Object[] args = joinPoint.getArgs();

            EvaluationContext context = new StandardEvaluationContext();
            if (paramNames != null) {
                for (int i = 0; i < paramNames.length; i++) {
                    context.setVariable(paramNames[i], args[i]);
                }
            }

            Expression expression = spelParser.parseExpression(spelExpression);
            Object value = expression.getValue(context);
            return value != null ? value.toString() : null;
        } catch (Exception e) {
            log.warn("解析审计日志 SpEL 表达式失败: {}", spelExpression, e);
            return null;
        }
    }

    /**
     * 构建方法参数的 JSON 字符串
     */
    private String buildParamsJson(ProceedingJoinPoint joinPoint) {
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        String[] paramNames = signature.getParameterNames();
        Object[] args = joinPoint.getArgs();

        if (paramNames == null || paramNames.length == 0) {
            return "{}";
        }

        Map<String, Object> params = new HashMap<>();
        for (int i = 0; i < paramNames.length; i++) {
            params.put(paramNames[i], args[i]);
        }

        return toJsonSafe(params);
    }

    /**
     * 安全地将对象转换为 JSON 字符串
     */
    private String toJsonSafe(Object obj) {
        try {
            return objectMapper.writeValueAsString(obj);
        } catch (JsonProcessingException e) {
            log.warn("序列化审计日志参数失败", e);
            return obj != null ? obj.toString() : "null";
        }
    }

    /**
     * 获取客户端 IP 地址
     */
    private String getClientIpAddress() {
        ServletRequestAttributes attributes =
                (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attributes == null) {
            return null;
        }

        HttpServletRequest request = attributes.getRequest();
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isBlank() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isBlank() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddr();
        }
        // 多级代理时取第一个 IP
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        return ip;
    }
}
