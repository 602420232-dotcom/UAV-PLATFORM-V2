package com.uav.common.security.audit;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

/**
 * 审计日志服务
 * <p>
 * 提供审计日志的保存和查询功能，保存操作异步执行以避免影响主业务流程。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuditLogService {

    private final AuditLogRepository auditLogRepository;

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
        try {
            auditLogRepository.save(auditLog);
            log.debug("审计日志已保存 - action: {}, resource: {}, user: {}",
                    auditLog.getAction(), auditLog.getResource(), auditLog.getUserId());
        } catch (Exception e) {
            log.error("保存审计日志失败 - action: {}, resource: {}",
                    auditLog.getAction(), auditLog.getResource(), e);
        }
    }

    /**
     * 同步保存审计日志（用于需要立即确认的场景）
     *
     * @param auditLog 审计日志实体
     */
    public void saveSync(AuditLog auditLog) {
        try {
            auditLogRepository.save(auditLog);
        } catch (Exception e) {
            log.error("同步保存审计日志失败 - action: {}, resource: {}",
                    auditLog.getAction(), auditLog.getResource(), e);
        }
    }
}
