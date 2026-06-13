package com.uav.risk.controller;

import com.uav.common.core.result.Result;
import com.uav.risk.dto.RiskQueryRequest;
import com.uav.risk.entity.RiskAssessment;
import com.uav.risk.service.RiskService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 风险感知与评估控制器
 */
@RestController
@RequestMapping("/api/v1/risk")
@RequiredArgsConstructor
public class RiskController {

    private final RiskService riskService;

    /**
     * 综合风险评估
     */
    @PostMapping("/assess")
    public Result<RiskAssessment> assess(@Valid @RequestBody RiskQueryRequest request) {
        RiskAssessment assessment = riskService.assessRisk(request);
        return Result.success(assessment);
    }

    /**
     * 生成区域风险栅格地图
     */
    @GetMapping("/map")
    public Result<List<RiskAssessment>> map(
            @RequestParam double minLon,
            @RequestParam double minLat,
            @RequestParam double maxLon,
            @RequestParam double maxLat,
            @RequestParam(defaultValue = "0.01") double resolution) {
        List<RiskAssessment> grid = riskService.generateRiskMap(minLon, minLat, maxLon, maxLat, resolution);
        return Result.success(grid);
    }

    /**
     * 获取历史风险评估记录
     */
    @GetMapping("/history")
    public Result<List<RiskAssessment>> history(
            @RequestParam(required = false) Long tenantId,
            @RequestParam(required = false) String type,
            @RequestParam(defaultValue = "10") int limit) {
        List<RiskAssessment> records = riskService.getRiskHistory(tenantId, type, limit);
        return Result.success(records);
    }
}
