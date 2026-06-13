package com.uav.planning.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 路径规划结果实体
 */
@Data
@TableName("path_result")
public class PathResult {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 关联任务ID */
    @TableField("task_id")
    private String taskId;

    /** 航点列表 JSON: [{lon, lat, alt, speed, time}] */
    private String waypointsJson;

    /** 总距离(m) */
    private Double totalDistance;

    /** 预计耗时(s) */
    private Integer estimatedTime;

    /** 风险评分 0-100 */
    private Double riskScore;

    /** 能耗估算(Wh) */
    private Double energyConsumption;

    /** 创建时间 */
    private LocalDateTime createdAt;
}
