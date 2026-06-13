package com.uav.risk.controller;

import com.uav.common.core.result.Result;
import com.uav.risk.dto.AirworthinessRequest;
import com.uav.risk.entity.AirworthinessAssessment;
import com.uav.risk.service.AirworthinessService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * 适航评估控制器
 */
@RestController
@RequestMapping("/api/v1/airworthiness")
@RequiredArgsConstructor
public class AirworthinessController {

    private final AirworthinessService airworthinessService;

    /**
     * 全维度适航评估
     */
    @PostMapping("/assess")
    public Result<AirworthinessAssessment> assess(@Valid @RequestBody AirworthinessRequest request) {
        AirworthinessAssessment assessment = airworthinessService.assessAirworthiness(request);
        return Result.success(assessment);
    }

    /**
     * 获取适航标准
     */
    @GetMapping("/standards/{uavModel}")
    public Result<Map<String, Object>> standards(@PathVariable String uavModel) {
        Map<String, Object> standard = airworthinessService.getAirworthinessStandard(uavModel);
        return Result.success(standard);
    }
}
