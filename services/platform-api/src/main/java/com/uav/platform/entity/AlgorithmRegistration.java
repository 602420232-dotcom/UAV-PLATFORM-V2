package com.uav.platform.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 算法注册实体
 * 用于存储和管理已注册到平台的算法信息
 */
@Data
@TableName("sys_algorithm_registration")
public class AlgorithmRegistration {

    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 算法名称
     */
    private String name;

    /**
     * 算法类型（如：planning, observation, assimilation, risk）
     */
    private String type;

    /**
     * 算法版本号（语义化版本，如：1.0.0）
     */
    private String version;

    /**
     * 算法服务访问端点
     */
    private String endpoint;

    /**
     * 参数 JSON Schema 定义
     */
    @TableField("param_schema")
    private String paramSchema;

    /**
     * 状态：1-启用，0-禁用，2-维护中
     */
    private Integer status;

    /**
     * 算法描述
     */
    private String description;

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
