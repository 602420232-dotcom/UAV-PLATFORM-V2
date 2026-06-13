package com.uav.assimilation.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * GPR 不确定性查询响应
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GprUncertaintyResponse {

    /**
     * 查询的区域
     */
    private String region;

    /**
     * 查询的时间
     */
    private String time;

    /**
     * 不确定性分布数据（均值）
     */
    private List<List<Double>> meanField;

    /**
     * 不确定性分布数据（方差）
     */
    private List<List<Double>> varianceField;

    /**
     * 不确定性分布数据（标准差）
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
     * 置信度统计信息
     */
    private ConfidenceStatistics confidenceStatistics;

    /**
     * 置信度统计
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ConfidenceStatistics {

        /**
         * 平均不确定性
         */
        private Double meanUncertainty;

        /**
         * 最大不确定性
         */
        private Double maxUncertainty;

        /**
         * 最小不确定性
         */
        private Double minUncertainty;

        /**
         * 不确定性标准差
         */
        private Double uncertaintyStd;

        /**
         * 高置信区域占比 (0-1)
         */
        private Double highConfidenceRatio;

        /**
         * 低置信区域占比 (0-1)
         */
        private Double lowConfidenceRatio;
    }
}
