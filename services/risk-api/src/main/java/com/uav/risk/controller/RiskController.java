package com.uav.risk.controller;

import com.uav.common.core.result.Result;
import com.uav.risk.dto.RiskQueryRequest;
import com.uav.risk.entity.RiskAssessment;
import com.uav.risk.service.RiskService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
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
@Tag(name = "风险评估", description = "综合风险评估、区域风险栅格地图生成及历史评估记录查询")
@RestController
@RequestMapping("/api/v1/risk")
@RequiredArgsConstructor
public class RiskController {

    private final RiskService riskService;

    /**
     * 综合风险评估
     */
    @Operation(
        summary = "综合风险评估",
        description = "对指定位置进行综合风险评估，综合考虑气象风险、地形风险、空域风险等多维度因素，输出风险等级和评分。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "评估成功",
            content = @Content(schema = @Schema(implementation = RiskAssessment.class))),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @PostMapping("/assess")
    @PreAuthorize("hasAuthority('risk:write')")
    public Result<RiskAssessment> assess(@Valid @RequestBody RiskQueryRequest request) {
        RiskAssessment assessment = riskService.assessRisk(request);
        return Result.success(assessment);
    }

    /**
     * 生成区域风险栅格地图
     */
    @Operation(
        summary = "生成区域风险栅格地图",
        description = "在指定经纬度矩形区域内按分辨率生成风险栅格地图，每个栅格点包含综合风险评分。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "生成成功"),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
    })
    @GetMapping("/map")
    public Result<List<RiskAssessment>> map(
            @Parameter(description = "最小经度", required = true, example = "116.0")
            @RequestParam double minLon,
            @Parameter(description = "最小纬度", required = true, example = "39.0")
            @RequestParam double minLat,
            @Parameter(description = "最大经度", required = true, example = "117.0")
            @RequestParam double maxLon,
            @Parameter(description = "最大纬度", required = true, example = "40.0")
            @RequestParam double maxLat,
            @Parameter(description = "栅格分辨率（度）", example = "0.01")
            @RequestParam(defaultValue = "0.01") double resolution) {
        List<RiskAssessment> grid = riskService.generateRiskMap(minLon, minLat, maxLon, maxLat, resolution);
        return Result.success(grid);
    }

    /**
     * 获取历史风险评估记录
     */
    @Operation(
        summary = "获取历史风险评估记录",
        description = "查询历史风险评估记录，支持按租户 ID 和评估类型筛选，返回最近 N 条记录。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @GetMapping("/history")
    @PreAuthorize("hasAuthority('risk:read')")
    public Result<List<RiskAssessment>> history(
            @Parameter(description = "租户 ID", example = "1")
            @RequestParam(required = false) Long tenantId,
            @Parameter(description = "评估类型筛选", example = "WEATHER")
            @RequestParam(required = false) String type,
            @Parameter(description = "返回记录数量上限", example = "10")
            @RequestParam(defaultValue = "10") int limit) {
        List<RiskAssessment> records = riskService.getRiskHistory(tenantId, type, limit);
        return Result.success(records);
    }
}
