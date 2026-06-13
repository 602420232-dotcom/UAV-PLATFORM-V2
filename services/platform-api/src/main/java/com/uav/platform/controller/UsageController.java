package com.uav.platform.controller;

import com.uav.common.core.result.Result;
import com.uav.platform.service.UsageService;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/usage")
@RequiredArgsConstructor
@Validated
public class UsageController {

    private final UsageService usageService;

    @GetMapping("/daily")
    public Result<List<Map<String, Object>>> dailyAggregation(
            @RequestParam @NotNull Long tenantId,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {
        return Result.success(usageService.getDailyAggregation(tenantId, startDate, endDate));
    }

    @GetMapping("/api-path")
    public Result<List<Map<String, Object>>> apiPathAggregation(
            @RequestParam @NotNull Long tenantId,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {
        return Result.success(usageService.getApiPathAggregation(tenantId, startDate, endDate));
    }
}
