package com.uav.platform.dto.experiment;

import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 实验对比结果
 */
@Data
public class ExperimentCompareResult {

    /**
     * 参与对比的实验列表
     */
    private List<Map<String, Object>> experiments;

    /**
     * 各指标对比数据
     * 每个指标包含 name, key, values 列表
     */
    private List<Map<String, Object>> metrics;
}
