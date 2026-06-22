package com.uav.platform.dto.experiment;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 实验视图对象
 */
@Data
public class ExperimentVO {

    private Long id;

    private String experimentName;

    private String algorithmName;

    private String algorithmCategory;

    private String status;

    private String configJson;

    private String resultJson;

    private String metricsJson;

    private String snapshotHash;

    private String snapshotData;

    private String weatherContext;

    private Long durationMs;

    private String createdBy;

    private Long tenantId;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
