package com.uav.platform.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("sys_api_key")
public class ApiKey {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("tenant_id")
    private Long tenantId;

    @TableField("key_value")
    private String keyValue;

    private String secret;

    private String name;

    private Integer status;

    @TableField("rate_limit")
    private Integer rateLimit;

    @TableField("created_at")
    private LocalDateTime createdAt;

    @TableField("expires_at")
    private LocalDateTime expiresAt;
}
