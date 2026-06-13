package com.uav.assimilation.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.util.Map;

/**
 * GPR 后处理请求
 */
@Data
public class GprPostprocessRequest {

    /**
     * 同化结果数据（分析场）
     */
    @NotBlank(message = "分析场数据不能为空")
    private String analysisFieldJson;

    /**
     * GPR 核函数类型: rbf, matern32, matern52, rational_quadratic
     */
    private String kernelType = "rbf";

    /**
     * 长度尺度参数
     */
    private Double lengthScale = 1.0;

    /**
     * 采样点数量
     */
    private Integer nSamples = 100;

    /**
     * 信号方差
     */
    private Double signalVariance = 1.0;

    /**
     * 噪声方差
     */
    private Double noiseVariance = 0.1;

    /**
     * 置信水平 (0-1)
     */
    private Double confidenceLevel = 0.95;

    /**
     * 租户ID
     */
    private Long tenantId;
}
