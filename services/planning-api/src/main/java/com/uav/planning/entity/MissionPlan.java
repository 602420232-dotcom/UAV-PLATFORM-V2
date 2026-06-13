package com.uav.planning.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 任务规划结果实体
 */
@Data
@TableName("mission_plan")
public class MissionPlan {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 关联任务ID */
    @TableField("task_id")
    private String taskId;

    /** 无人机列表 JSON */
    private String uavsJson;

    /** 任务列表 JSON */
    private String tasksJson;

    /** 调度方案 JSON */
    private String scheduleJson;

    /** 整体评分 */
    private Double overallScore;

    /** 租户ID */
    private String tenantId;

    /** 创建时间 */
    private LocalDateTime createdAt;
}
