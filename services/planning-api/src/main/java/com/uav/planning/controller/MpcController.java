package com.uav.planning.controller;

import com.uav.common.core.result.Result;
import com.uav.planning.dto.MpcPlanRequest;
import com.uav.planning.dto.MpcPositionUpdate;
import com.uav.planning.dto.MpcResult;
import com.uav.planning.dto.MpcUpdateResponse;
import com.uav.planning.entity.PlanningTask;
import com.uav.planning.service.MpcService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

/**
 * MPC 实时滚动规划控制器
 */
@RestController
@RequestMapping("/api/v1/planning/mpc")
@RequiredArgsConstructor
@Validated
public class MpcController {

    private final MpcService mpcService;

    /**
     * 提交 MPC 滚动规划任务
     */
    @PostMapping("/submit")
    public Result<String> submitMpcPlanning(@Valid @RequestBody MpcPlanRequest request) {
        String taskId = mpcService.submitMpcPlanning(request);
        return Result.success(taskId);
    }

    /**
     * 获取 MPC 规划状态
     */
    @GetMapping("/tasks/{taskId}")
    public Result<PlanningTask> getMpcStatus(@PathVariable String taskId) {
        PlanningTask task = mpcService.getMpcStatus(taskId);
        if (task == null) {
            return Result.error(404, "MPC task not found");
        }
        return Result.success(task);
    }

    /**
     * 获取 MPC 规划结果（最新航段）
     */
    @GetMapping("/tasks/{taskId}/result")
    public Result<MpcResult> getMpcResult(@PathVariable String taskId) {
        MpcResult result = mpcService.getMpcResult(taskId);
        if (result == null) {
            return Result.error(404, "MPC result not found");
        }
        return Result.success(result);
    }

    /**
     * 更新实时位置（触发重规划）
     */
    @PostMapping("/update-position")
    public Result<MpcUpdateResponse> updatePosition(@Valid @RequestBody MpcPositionUpdate request) {
        MpcUpdateResponse response = mpcService.updatePosition(request);
        return Result.success(response);
    }

    /**
     * 取消 MPC 任务
     */
    @PostMapping("/tasks/{taskId}/cancel")
    public Result<Void> cancelMpc(@PathVariable String taskId) {
        boolean cancelled = mpcService.cancelMpc(taskId);
        if (!cancelled) {
            return Result.error(404, "MPC task not found or already completed");
        }
        return Result.success();
    }
}
