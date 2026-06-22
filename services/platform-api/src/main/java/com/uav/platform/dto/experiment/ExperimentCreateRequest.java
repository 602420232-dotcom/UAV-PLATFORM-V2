package com.uav.platform.dto.experiment;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 创建实验请求
 */
@Data
public class ExperimentCreateRequest {

    /**
     * 实验名称
     */
    @NotBlank(message = "实验名称不能为空")
    private String experimentName;

    /**
     * 算法名称
     */
    @NotBlank(message = "算法名称不能为空")
    private String algorithmName;

    /**
     * 算法分类
     */
    private String algorithmCategory;

    /**
     * 算法参数JSON
     */
    private String configJson;

    /**
     * 气象上下文JSON
     */
    private String weatherContext;
}
