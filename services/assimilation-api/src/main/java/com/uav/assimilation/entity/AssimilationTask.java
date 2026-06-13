package com.uav.assimilation.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 数据同化任务实体
 */
@Data
@TableName("assimilation_task")
public class AssimilationTask {

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 算法类型: 3DVAR, 4DVAR, 5DVAR, ENKF, HYBRID, ENHANCED_BAYESIAN
     */
    private String algorithmType;

    /**
     * 任务状态: QUEUED, RUNNING, SUCCESS, FAILED, TIMEOUT, CANCELLED
     */
    private String status;

    /**
     * 算法参数 JSON
     */
    private String paramsJson;

    /**
     * 结果数据 JSON
     */
    private String resultJson;

    /**
     * 进度 0-100
     */
    private Integer progress;

    /**
     * 错误信息
     */
    private String errorMsg;

    /**
     * 租户ID
     */
    private Long tenantId;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 开始执行时间
     */
    private LocalDateTime startedAt;

    /**
     * 完成时间
     */
    private LocalDateTime completedAt;
}
