package com.uav.platform.dto.experiment;

import lombok.Data;

/**
 * 实验查询请求
 */
@Data
public class ExperimentQueryRequest {

    /**
     * 算法名称（模糊匹配）
     */
    private String algorithmName;

    /**
     * 实验状态
     */
    private String status;

    /**
     * 开始时间（yyyy-MM-dd HH:mm:ss）
     */
    private String startDate;

    /**
     * 结束时间（yyyy-MM-dd HH:mm:ss）
     */
    private String endDate;

    /**
     * 当前页码
     */
    private Integer current = 1;

    /**
     * 每页大小
     */
    private Integer size = 10;
}
