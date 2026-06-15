package com.uav.assimilation.controller;

import com.uav.assimilation.dto.SubmitTaskRequest;
import com.uav.assimilation.dto.TaskQueryRequest;
import com.uav.assimilation.entity.AssimilationResult;
import com.uav.assimilation.entity.AssimilationTask;
import com.uav.assimilation.service.AssimilationService;
import com.uav.common.core.annotation.Idempotent;
import com.uav.common.core.result.Result;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

/**
 * 数据同化控制器
 */
@RestController
@RequestMapping("/api/v1/assimilation")
@RequiredArgsConstructor
public class AssimilationController {

    private final AssimilationService assimilationService;

    /**
     * 提交同化任务
     */
    @Idempotent
    @PostMapping("/tasks")
    public Result<Long> submitTask(@Valid @RequestBody SubmitTaskRequest request) {
        return assimilationService.submitTask(request);
    }

    /**
     * 查询任务状态
     */
    @GetMapping("/tasks/{id}")
    @PreAuthorize("hasAuthority('assimilation:read')")
    public Result<AssimilationTask> getTaskStatus(@PathVariable("id") Long id) {
        return assimilationService.getTaskStatus(id);
    }

    /**
     * 查询任务结果
     */
    @GetMapping("/tasks/{id}/result")
    @PreAuthorize("hasAuthority('assimilation:read')")
    public Result<AssimilationResult> getTaskResult(@PathVariable("id") Long id) {
        return assimilationService.getTaskResult(id);
    }

    /**
     * 查询任务列表
     */
    @GetMapping("/tasks")
    @PreAuthorize("hasAuthority('assimilation:read')")
    public Result<?> listTasks(TaskQueryRequest request) {
        return assimilationService.listTasks(request);
    }

    /**
     * 取消任务
     */
    @PostMapping("/tasks/{id}/cancel")
    @PreAuthorize("hasAuthority('assimilation:write')")
    public Result<Void> cancelTask(@PathVariable("id") Long id) {
        return assimilationService.cancelTask(id);
    }
}
