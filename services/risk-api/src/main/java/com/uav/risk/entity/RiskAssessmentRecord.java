package com.uav.risk.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 风险评估记录实体（数据库持久化）
 * 对应 init-db.sql 中的 risk_assessment_history 表
 */
@Data
@TableName("risk_assessment_history")
public class RiskAssessmentRecord {

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    /** 评估类型: WEATHER / TERRAIN / AIRSPACE / EQUIPMENT / COMPOSITE */
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
    private String tenantId;

    /** 创建时间 */
    private LocalDateTime createdAt;
}
