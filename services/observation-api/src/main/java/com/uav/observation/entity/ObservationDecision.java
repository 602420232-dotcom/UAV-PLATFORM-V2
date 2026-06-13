package com.uav.observation.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 观测决策实体
 */
@Data
@TableName("observation_decision")
public class ObservationDecision implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 关联任务ID
     */
    private Long taskId;

    /**
     * 决策类型
     */
    private String decisionType;

    /**
     * 目标区域 JSON
     */
    private String targetAreaJson;

    /**
     * 优先级 (1-10)
     */
    private Integer priority;

    /**
     * 预期信息增益
     */
    private Double expectedInfoGain;

    /**
     * 执行时间
     */
    private LocalDateTime executedAt;
}
