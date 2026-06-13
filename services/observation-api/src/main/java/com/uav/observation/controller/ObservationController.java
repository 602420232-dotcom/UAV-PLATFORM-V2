package com.uav.observation.controller;

import com.uav.common.core.result.Result;
import com.uav.common.core.result.ResultCode;
import com.uav.observation.dto.CreateObservationRequest;
import com.uav.observation.entity.ObservationTask;
import com.uav.observation.service.ObservationService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 观测任务接口
 */
@RestController
@RequestMapping("/api/v1/observation/tasks")
@RequiredArgsConstructor
@Validated
public class ObservationController {

    private final ObservationService observationService;

    /**
     * 创建观测任务
     */
    @PostMapping
    public Result<ObservationTask> createTask(@Valid @RequestBody CreateObservationRequest request) {
        return Result.success(observationService.createTask(request));
    }

    /**
     * 根据ID获取观测任务
     */
    @GetMapping("/{id}")
    public Result<ObservationTask> getTask(@PathVariable Long id) {
        ObservationTask task = observationService.getTask(id);
        if (task == null) {
            return Result.error(ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(task);
    }

    /**
     * 列出所有观测任务
     */
    @GetMapping
    public Result<List<ObservationTask>> listTasks() {
        return Result.success(observationService.listTasks());
    }

    /**
     * 更新任务状态
     */
    @PostMapping("/{id}/status")
    public Result<ObservationTask> updateTaskStatus(
            @PathVariable Long id,
            @RequestParam String status) {
        ObservationTask task = observationService.updateTaskStatus(id, status);
        if (task == null) {
            return Result.error(ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(task);
    }
}
