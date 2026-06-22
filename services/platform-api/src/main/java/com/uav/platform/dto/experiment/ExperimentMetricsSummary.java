package com.uav.platform.dto.experiment;

import lombok.Data;

import java.util.Map;

/**
 * 算法指标汇总统计
 */
@Data
public class ExperimentMetricsSummary {

    /**
     * 算法名称
     */
    private String algorithmName;

    /**
     * 实验总数
     */
    private Long totalExperiments;

    /**
     * 成功实验数
     */
    private Long completedCount;

    /**
     * 失败实验数
     */
    private Long failedCount;

    /**
     * 平均执行耗时（毫秒）
     */
    private Double avgDurationMs;

    /**
     * 各指标平均值
     */
    private Map<String, Double> avgMetrics;

    /**
     * 各指标最佳值
     */
    private Map<String, Double> bestMetrics;
}
