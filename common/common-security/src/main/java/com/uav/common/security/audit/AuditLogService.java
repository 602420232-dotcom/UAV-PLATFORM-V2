package com.uav.common.security.audit;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import jakarta.annotation.Nullable;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

/**
 * 审计日志服务
 * <p>
 * 提供审计日志的保存和查询功能，保存操作异步执行以避免影响主业务流程。
 * <p>
 * 当 AuditLogRepository 不可用时（如未配置 Spring Data JPA），服务仍可正常加载，
 * 但保存操作会被静默跳过并记录 warn 日志。
 */
@Slf4j
@Service
public class AuditLogService {

    @Autowired(required = false)
    @Nullable
    private AuditLogRepository auditLogRepository;

    /**
     * 异步保存审计日志
     * <p>
     * 使用 {@link Async} 注解确保日志写入不阻塞业务线程。
     * 需要在配置类上启用 @EnableAsync。
     *
     * @param auditLog 审计日志实体
     */
    @Async
    public void save(AuditLog auditLog) {
        doSave(auditLog);
    }

    /**
     * 同步保存审计日志（用于需要立即确认的场景）
     *
     * @param auditLog 审计日志实体
     */
    public void saveSync(AuditLog auditLog) {
        doSave(auditLog);
    }

    private void doSave(AuditLog auditLog) {
        if (auditLogRepository == null) {
            log.warn("AuditLogRepository 不可用，跳过审计日志保存 - action: {}, resource: {}",
                    auditLog.getAction(), auditLog.getResource());
            return;
        }
        try {
            auditLogRepository.save(auditLog);
            log.debug("审计日志已保存 - action: {}, resource: {}, user: {}",
                    auditLog.getAction(), auditLog.getResource(), auditLog.getUserId());
        } catch (Exception e) {
            log.error("保存审计日志失败 - action: {}, resource: {}",
                    auditLog.getAction(), auditLog.getResource(), e);
        }
    }
}
