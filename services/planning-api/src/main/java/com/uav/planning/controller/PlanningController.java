package com.uav.planning.controller;

import com.uav.common.core.annotation.Idempotent;
import com.uav.common.core.result.Result;
import com.uav.planning.dto.PlanMissionRequest;
import com.uav.planning.dto.PlanPathRequest;
import com.uav.planning.entity.MissionPlan;
import com.uav.planning.entity.PathResult;
import com.uav.planning.entity.PlanningTask;
import com.uav.planning.service.PlanningService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 规划服务接口
 */
@RestController
@RequestMapping("/api/v1/planning")
@RequiredArgsConstructor
@Validated
public class PlanningController {

    private final PlanningService planningService;

    /**
     * 提交路径规划任务
     */
    @Idempotent
    @PostMapping("/path")
    public Result<PlanningTask> planPath(@Valid @RequestBody PlanPathRequest request) {
        return Result.success(planningService.submitPathPlanning(request));
    }

    /**
     * 提交任务规划
     */
    @PostMapping("/mission")
    public Result<PlanningTask> planMission(@Valid @RequestBody PlanMissionRequest request) {
        return Result.success(planningService.submitMissionPlanning(request));
    }

    /**
     * 获取任务状态
     */
    @GetMapping("/tasks/{id}")
    public Result<PlanningTask> getTask(@PathVariable Long id) {
        PlanningTask task = planningService.getTaskStatus(id);
        if (task == null) {
            return Result.error(com.uav.common.core.result.ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(task);
    }

    /**
     * 获取路径规划结果
     */
    @GetMapping("/tasks/{id}/result")
    public Result<PathResult> getPathResult(@PathVariable Long id) {
        PathResult result = planningService.getPathResult(id);
        if (result == null) {
            return Result.error(com.uav.common.core.result.ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(result);
    }

    /**
     * 获取任务规划结果
     */
    @GetMapping("/tasks/{id}/mission")
    public Result<MissionPlan> getMissionPlan(@PathVariable Long id) {
        MissionPlan plan = planningService.getMissionPlan(id);
        if (plan == null) {
            return Result.error(com.uav.common.core.result.ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(plan);
    }

    /**
     * 列出所有任务
     */
    @GetMapping("/tasks")
    public Result<List<PlanningTask>> listTasks() {
        return Result.success(planningService.listTasks());
    }

    /**
     * 取消任务
     */
    @PostMapping("/tasks/{id}/cancel")
    public Result<Void> cancelTask(@PathVariable Long id) {
        boolean cancelled = planningService.cancelTask(id);
        if (!cancelled) {
            return Result.error(com.uav.common.core.result.ResultCode.TASK_NOT_FOUND);
        }
        return Result.success();
    }
}
