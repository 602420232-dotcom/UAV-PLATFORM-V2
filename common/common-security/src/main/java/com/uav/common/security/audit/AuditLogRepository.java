package com.uav.common.security.audit;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 审计日志 Repository
 * <p>
 * 提供 Spring Data JPA 数据访问能力，支持按用户、操作类型、时间范围查询。
 */
@Repository
public interface AuditLogRepository extends JpaRepository<AuditLog, Long> {

    /**
     * 根据用户ID查询审计日志
     *
     * @param userId   用户ID
     * @param pageable 分页参数
     * @return 审计日志分页列表
     */
    Page<AuditLog> findByUserId(Long userId, Pageable pageable);

    /**
     * 根据操作类型查询审计日志
     *
     * @param action   操作名称
     * @param pageable 分页参数
     * @return 审计日志分页列表
     */
    Page<AuditLog> findByAction(String action, Pageable pageable);

    /**
     * 根据资源类型查询审计日志
     *
     * @param resource 资源类型
     * @param pageable 分页参数
     * @return 审计日志分页列表
     */
    Page<AuditLog> findByResource(String resource, Pageable pageable);

    /**
     * 根据时间范围查询审计日志
     *
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @param pageable  分页参数
     * @return 审计日志分页列表
     */
    Page<AuditLog> findByCreatedAtBetween(LocalDateTime startTime, LocalDateTime endTime, Pageable pageable);

    /**
     * 根据用户ID和操作类型查询审计日志
     *
     * @param userId 用户ID
     * @param action 操作名称
     * @param pageable 分页参数
     * @return 审计日志分页列表
     */
    Page<AuditLog> findByUserIdAndAction(Long userId, String action, Pageable pageable);

    /**
     * 根据IP地址查询审计日志
     *
     * @param ipAddress IP地址
     * @param pageable  分页参数
     * @return 审计日志分页列表
     */
    Page<AuditLog> findByIpAddress(String ipAddress, Pageable pageable);
}
