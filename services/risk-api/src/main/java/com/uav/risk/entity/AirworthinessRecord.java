package com.uav.risk.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 适航评估记录实体（数据库持久化）
 * 对应 init-db.sql 中的 airworthiness_history 表
 */
@Data
@TableName("airworthiness_history")
public class AirworthinessRecord {

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    /** 无人机型号 */
    private String uavModel;

    /** 综合适航评分 */
    private Double overallScore;

    /** 各维度评分 JSON */
    private String dimensionScoresJson;

    /** 适航状态: PASS / WARNING / FAIL */
    private String status;

    /** 建议 JSON */
    private String recommendationsJson;

    /** 租户ID */
    private String tenantId;

    /** 创建时间 */
    private LocalDateTime createdAt;
}
