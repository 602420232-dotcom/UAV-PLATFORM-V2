package com.uav.risk.entity;

import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 风险评估结果
 */
@Data
public class RiskAssessment implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    /** 风险类型: WEATHER / TERRAIN / AIRSPACE / EQUIPMENT / COMPOSITE */
    private String type;

    /** 风险等级 1-5 */
    private Integer level;

    /** 风险评分 0-100 */
    private Integer score;

    /** 风险因子 JSON */
    private String factorsJson;

    /** 位置信息 JSON */
    private String locationJson;

    /** 租户ID */
    private Long tenantId;

    /** 创建时间 */
    private LocalDateTime createdAt;
}
