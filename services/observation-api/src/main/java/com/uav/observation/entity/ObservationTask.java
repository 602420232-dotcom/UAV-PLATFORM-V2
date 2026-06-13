package com.uav.observation.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 观测任务实体
 */
@Data
@TableName("observation_task")
public class ObservationTask implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 任务类型: ADAPTIVE(自适应), PLANNED(计划), EMERGENCY(应急)
     */
    @TableField("type")
    private String type;

    /**
     * 任务状态
     */
    private String status;

    /**
     * 传感器配置 JSON
     */
    private String sensorConfigJson;

    /**
     * 规划路径 JSON
     */
    private String plannedPathJson;

    /**
     * 实际路径 JSON
     */
    private String actualPathJson;

    /**
     * 数据质量评分 (0-100)
     */
    private Double dataQuality;

    /**
     * 同化反馈 JSON
     */
    private String assimilationFeedbackJson;

    /**
     * 租户ID
     */
    private String tenantId;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
