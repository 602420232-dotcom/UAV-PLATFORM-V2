package com.uav.platform.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 实验管理实体
 * 用于存储和管理算法实验记录、指标、快照等信息
 */
@Data
@TableName("sys_experiment")
public class Experiment {

    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 实验名称
     */
    @TableField("experiment_name")
    private String experimentName;

    /**
     * 算法名称
     */
    @TableField("algorithm_name")
    private String algorithmName;

    /**
     * 算法分类
     */
    @TableField("algorithm_category")
    private String algorithmCategory;

    /**
     * 状态：RUNNING / COMPLETED / FAILED / CANCELLED
     */
    private String status;

    /**
     * 算法参数JSON
     */
    @TableField("config_json")
    private String configJson;

    /**
     * 结果JSON
     */
    @TableField("result_json")
    private String resultJson;

    /**
     * 指标JSON（RMSE/执行时间/收敛性等）
     */
    @TableField("metrics_json")
    private String metricsJson;

    /**
     * 快照SHA256哈希
     */
    @TableField("snapshot_hash")
    private String snapshotHash;

    /**
     * 快照数据JSON
     */
    @TableField("snapshot_data")
    private String snapshotData;

    /**
     * 气象上下文JSON
     */
    @TableField("weather_context")
    private String weatherContext;

    /**
     * 执行耗时（毫秒）
     */
    @TableField("duration_ms")
    private Long durationMs;

    /**
     * 创建者
     */
    @TableField("created_by")
    private String createdBy;

    /**
     * 租户ID
     */
    @TableField("tenant_id")
    private Long tenantId;

    /**
     * 创建时间
     */
    @TableField("created_at")
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    @TableField("updated_at")
    private LocalDateTime updatedAt;
}
