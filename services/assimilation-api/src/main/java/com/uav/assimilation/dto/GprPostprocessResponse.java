package com.uav.assimilation.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * GPR 后处理响应
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GprPostprocessResponse {

    /**
     * 任务ID（异步模式下使用）
     */
    private Long taskId;

    /**
     * 均值场
     */
    private List<List<Double>> meanField;

    /**
     * 方差场
     */
    private List<List<Double>> varianceField;

    /**
     * 标准差场
     */
    private List<List<Double>> stdField;

    /**
     * 置信区间下界
     */
    private List<List<Double>> confidenceLower;

    /**
     * 置信区间上界
     */
    private List<List<Double>> confidenceUpper;

    /**
     * 置信水平
     */
    private Double confidenceLevel;

    /**
     * 使用的核函数类型
     */
    private String kernelType;

    /**
     * GPR 参数摘要
     */
    private Map<String, Object> parameterSummary;
}
