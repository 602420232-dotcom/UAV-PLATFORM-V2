package com.uav.observation.controller;

import com.uav.common.core.result.Result;
import com.uav.common.core.result.ResultCode;
import com.uav.observation.dto.ObservationDecisionRequest;
import com.uav.observation.entity.ObservationDecision;
import com.uav.observation.service.ObservationDecisionService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 观测决策接口
 */
@RestController
@RequestMapping("/api/v1/observation/decisions")
@RequiredArgsConstructor
@Validated
public class ObservationDecisionController {

    private final ObservationDecisionService observationDecisionService;

    /**
     * 做出观测决策
     */
    @PostMapping
    public Result<ObservationDecision> makeDecision(@Valid @RequestBody ObservationDecisionRequest request) {
        return Result.success(observationDecisionService.makeDecision(request));
    }

    /**
     * 根据ID获取决策
     */
    @GetMapping("/{id}")
    public Result<ObservationDecision> getDecision(@PathVariable Long id) {
        ObservationDecision decision = observationDecisionService.getDecision(id);
        if (decision == null) {
            return Result.error(ResultCode.NOT_FOUND);
        }
        return Result.success(decision);
    }

    /**
     * 获取决策历史
     */
    @GetMapping
    public Result<List<ObservationDecision>> getDecisionHistory() {
        return Result.success(observationDecisionService.getDecisionHistory());
    }
}
