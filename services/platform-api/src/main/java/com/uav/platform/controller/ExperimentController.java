package com.uav.platform.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.uav.common.core.result.Result;
import com.uav.platform.dto.experiment.ExperimentCompareResult;
import com.uav.platform.dto.experiment.ExperimentCreateRequest;
import com.uav.platform.dto.experiment.ExperimentMetricsSummary;
import com.uav.platform.dto.experiment.ExperimentQueryRequest;
import com.uav.platform.dto.experiment.ExperimentVO;
import com.uav.platform.service.ExperimentService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;

/**
 * 实验管理控制器
 * 提供实验创建、查询、快照管理、对比分析、报告生成等功能
 */
@RestController
@RequestMapping("/api/v1/experiments")
@RequiredArgsConstructor
@Validated
public class ExperimentController {

    private final ExperimentService experimentService;

    /**
     * 分页查询实验列表
     * GET /api/v1/experiments
     * 支持按 algorithm_name, status, date_range 筛选
     */
    @GetMapping
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<Page<ExperimentVO>> list(ExperimentQueryRequest request) {
        Page<ExperimentVO> page = experimentService.listExperiments(request);
        return Result.success(page);
    }

    /**
     * 获取实验详情（含metrics和快照信息）
     * GET /api/v1/experiments/{id}
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<ExperimentVO> getById(@PathVariable Long id) {
        try {
            ExperimentVO vo = experimentService.getExperimentById(id);
            return Result.success(vo);
        } catch (IllegalArgumentException e) {
            return Result.error(404, e.getMessage());
        }
    }

    /**
     * 创建实验记录
     * POST /api/v1/experiments
     */
    @PostMapping
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<ExperimentVO> create(@Valid @RequestBody ExperimentCreateRequest request) {
        ExperimentVO vo = experimentService.createExperiment(request);
        return Result.success(vo);
    }

    /**
     * 删除实验记录
     * DELETE /api/v1/experiments/{id}
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<Void> delete(@PathVariable Long id) {
        try {
            experimentService.deleteExperiment(id);
            return Result.success();
        } catch (IllegalArgumentException e) {
            return Result.error(404, e.getMessage());
        }
    }

    /**
     * 创建实验快照（保存当前状态哈希）
     * POST /api/v1/experiments/{id}/snapshot
     */
    @PostMapping("/{id}/snapshot")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<ExperimentVO> createSnapshot(@PathVariable Long id) {
        try {
            ExperimentVO vo = experimentService.createSnapshot(id);
            return Result.success(vo);
        } catch (IllegalArgumentException e) {
            return Result.error(404, e.getMessage());
        }
    }

    /**
     * 获取实验快照
     * GET /api/v1/experiments/{id}/snapshot
     */
    @GetMapping("/{id}/snapshot")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<Map<String, Object>> getSnapshot(@PathVariable Long id) {
        try {
            Map<String, Object> snapshot = experimentService.getSnapshot(id);
            return Result.success(snapshot);
        } catch (IllegalArgumentException e) {
            return Result.error(404, e.getMessage());
        } catch (IllegalStateException e) {
            return Result.error(400, e.getMessage());
        }
    }

    /**
     * 从快照恢复实验
     * POST /api/v1/experiments/{id}/restore
     */
    @PostMapping("/{id}/restore")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<Map<String, Object>> restoreFromSnapshot(@PathVariable Long id) {
        try {
            Map<String, Object> result = experimentService.restoreFromSnapshot(id);
            return Result.success(result);
        } catch (IllegalArgumentException e) {
            return Result.error(404, e.getMessage());
        } catch (IllegalStateException e) {
            return Result.error(400, e.getMessage());
        }
    }

    /**
     * 对比多个实验（传入experiment_ids列表）
     * POST /api/v1/experiments/compare
     * 请求体: { "ids": [1, 2, 3] }
     */
    @PostMapping("/compare")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<ExperimentCompareResult> compare(@RequestBody Map<String, Object> body) {
        try {
            Object idsObj = body.get("ids");
            if (idsObj == null) {
                return Result.error(400, "缺少 ids 参数");
            }
            if (!(idsObj instanceof List)) {
                return Result.error(400, "ids 参数必须为数组");
            }
            List<?> rawIds = (List<?>) idsObj;
            List<Long> ids = rawIds.stream()
                    .map(item -> {
                        if (item instanceof Number) {
                            return ((Number) item).longValue();
                        }
                        return Long.parseLong(item.toString());
                    })
                    .collect(java.util.stream.Collectors.toList());
            ExperimentCompareResult result = experimentService.compareExperiments(ids);
            return Result.success(result);
        } catch (IllegalArgumentException e) {
            return Result.error(400, e.getMessage());
        } catch (Exception e) {
            return Result.error(400, "对比请求处理失败: " + e.getMessage());
        }
    }

    /**
     * 生成实验报告（返回CSV/LaTeX格式数据）
     * GET /api/v1/experiments/{id}/report
     */
    @GetMapping("/{id}/report")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<Map<String, Object>> generateReport(
            @PathVariable Long id,
            @RequestParam(defaultValue = "json") String format) {
        try {
            Map<String, Object> report = experimentService.generateReport(id, format);
            return Result.success(report);
        } catch (IllegalArgumentException e) {
            return Result.error(404, e.getMessage());
        }
    }

    /**
     * 获取算法指标汇总统计
     * GET /api/v1/experiments/metrics/summary
     */
    @GetMapping("/metrics/summary")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<ExperimentMetricsSummary> getMetricsSummary(
            @RequestParam(required = false) String algorithmName) {
        ExperimentMetricsSummary summary = experimentService.getMetricsSummary(algorithmName);
        return Result.success(summary);
    }
}
