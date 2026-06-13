package com.uav.platform.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("sys_tenant")
public class Tenant {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    @TableField("schema_name")
    private String schemaName;

    private Integer status;

    @TableField("quota_config")
    private String quotaConfig;

    @TableField("created_at")
    private LocalDateTime createdAt;

    @TableField("updated_at")
    private LocalDateTime updatedAt;
}
