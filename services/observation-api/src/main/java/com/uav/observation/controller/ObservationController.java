package com.uav.observation.controller;

import com.uav.common.core.result.Result;
import com.uav.common.core.result.ResultCode;
import com.uav.observation.dto.CreateObservationRequest;
import com.uav.observation.entity.ObservationTask;
import com.uav.observation.service.ObservationService;
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
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 观测任务接口
 */
@Tag(name = "观测决策", description = "观测任务的创建、查询、状态更新及列表管理")
@RestController
@RequestMapping("/api/v1/observation/tasks")
@RequiredArgsConstructor
@Validated
public class ObservationController {

    private final ObservationService observationService;

    /**
     * 创建观测任务
     */
    @Operation(
        summary = "创建观测任务",
        description = "创建新的观测任务，支持自适应观测、计划观测和紧急观测三种类型。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "创建成功",
            content = @Content(schema = @Schema(implementation = ObservationTask.class))),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @PostMapping
    @PreAuthorize("hasAuthority('observation:write')")
    public Result<ObservationTask> createTask(@Valid @RequestBody CreateObservationRequest request) {
        return Result.success(observationService.createTask(request));
    }

    /**
     * 根据ID获取观测任务
     */
    @Operation(
        summary = "获取观测任务详情",
        description = "根据任务 ID 获取观测任务的详细信息，包括传感器配置、规划路径、数据质量评分等。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功",
            content = @Content(schema = @Schema(implementation = ObservationTask.class))),
        @ApiResponse(responseCode = "404", description = "任务不存在"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('observation:read')")
    public Result<ObservationTask> getTask(
            @Parameter(description = "观测任务 ID", required = true, example = "1")
            @PathVariable Long id) {
        ObservationTask task = observationService.getTask(id);
        if (task == null) {
            return Result.error(ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(task);
    }

    /**
     * 列出所有观测任务
     */
    @Operation(
        summary = "列出所有观测任务",
        description = "获取当前租户下所有观测任务列表，按创建时间倒序排列。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @GetMapping
    @PreAuthorize("hasAuthority('observation:read')")
    public Result<List<ObservationTask>> listTasks() {
        return Result.success(observationService.listTasks());
    }

    /**
     * 更新任务状态
     */
    @Operation(
        summary = "更新观测任务状态",
        description = "更新指定观测任务的状态。支持的状态转换：QUEUED -> RUNNING -> SUCCESS/FAILED/CANCELLED。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "更新成功",
            content = @Content(schema = @Schema(implementation = ObservationTask.class))),
        @ApiResponse(responseCode = "400", description = "无效的状态转换"),
        @ApiResponse(responseCode = "404", description = "任务不存在"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @PostMapping("/{id}/status")
    @PreAuthorize("hasAuthority('observation:write')")
    public Result<ObservationTask> updateTaskStatus(
            @Parameter(description = "观测任务 ID", required = true, example = "1")
            @PathVariable Long id,
            @Parameter(description = "目标状态", required = true, example = "RUNNING",
                schema = @Schema(allowableValues = {"QUEUED", "RUNNING", "SUCCESS", "FAILED", "CANCELLED"}))
            @RequestParam String status) {
        ObservationTask task = observationService.updateTaskStatus(id, status);
        if (task == null) {
            return Result.error(ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(task);
    }
}
