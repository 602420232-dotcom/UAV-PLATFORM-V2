package com.uav.planning.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 规划任务实体
 */
@Data
@TableName("planning_task")
public class PlanningTask {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 任务唯一标识 */
    @TableField("task_id")
    private String taskId;

    /** 算法类型: VRPTW, DERRTSTAR, DWA, MPC, A_STAR, DIJKSTRA, RRTSTAR */
    private String algorithmType;

    /** 任务状态: QUEUED, RUNNING, SUCCESS, FAILED, TIMEOUT, CANCELLED */
    private String status;

    /** 算法参数 JSON */
    private String paramsJson;

    /** 结果数据 JSON */
    private String resultJson;

    /** 进度百分比 0-100 */
    private Integer progress;

    /** 错误信息 */
    private String errorMsg;

    /** 租户ID */
    private String tenantId;

    /** 创建时间 */
    private LocalDateTime createdAt;

    /** 开始执行时间 */
    private LocalDateTime startedAt;

    /** 完成时间 */
    private LocalDateTime completedAt;
}
