package com.uav.platform.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("sys_usage_record")
public class UsageRecord {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("tenant_id")
    private Long tenantId;

    @TableField("api_key")
    private String apiKey;

    @TableField("api_path")
    private String apiPath;

    @TableField("request_count")
    private Long requestCount;

    @TableField("response_time_ms")
    private Long responseTimeMs;

    private Integer status;

    @TableField("created_at")
    private LocalDateTime createdAt;
}
