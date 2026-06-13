package com.uav.risk.entity;

import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 适航评估结果
 */
@Data
public class AirworthinessAssessment implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    /** 无人机型号 */
    private String uavModel;

    /** 综合适航评分 */
    private Integer overallScore;

    /**
     * 各维度评分 JSON
     * 包含: 气象适航、结构适航、动力适航、通信适航、任务适航
     */
    private String dimensionScoresJson;

    /** 评估状态: PASS / FAIL / WARNING */
    private String status;

    /** 改进建议 JSON */
    private String recommendationsJson;

    /** 租户ID */
    private Long tenantId;

    /** 创建时间 */
    private LocalDateTime createdAt;
}
