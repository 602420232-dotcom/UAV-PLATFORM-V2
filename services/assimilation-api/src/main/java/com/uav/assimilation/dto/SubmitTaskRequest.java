package com.uav.assimilation.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.Map;

/**
 * 提交同化任务请求
 */
@Data
public class SubmitTaskRequest {

    @NotBlank(message = "算法类型不能为空")
    private String algorithmType;

    /**
     * 算法参数
     */
    private Map<String, Object> params;

    @NotNull(message = "租户ID不能为空")
    private Long tenantId;
}
