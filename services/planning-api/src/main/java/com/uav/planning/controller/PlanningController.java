package com.uav.planning.controller;

import com.uav.common.core.annotation.Idempotent;
import com.uav.common.core.result.Result;
import com.uav.planning.dto.PlanMissionRequest;
import com.uav.planning.dto.PlanPathRequest;
import com.uav.planning.entity.MissionPlan;
import com.uav.planning.entity.PathResult;
import com.uav.planning.entity.PlanningTask;
import com.uav.planning.service.PlanningService;
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
 * 规划服务接口
 */
@Tag(name = "航迹规划", description = "路径规划任务提交、任务规划、任务状态查询及取消")
@RestController
@RequestMapping("/api/v1/planning")
@RequiredArgsConstructor
@Validated
public class PlanningController {

    private final PlanningService planningService;

    /**
     * 提交路径规划任务
     */
    @Operation(
        summary = "提交路径规划任务",
        description = "提交基于指定算法（A*、Dijkstra、RRT* 等）的路径规划任务，返回任务信息供后续查询。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "任务提交成功",
            content = @Content(schema = @Schema(implementation = PlanningTask.class))),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
        @ApiResponse(responseCode = "429", description = "请求过于频繁（幂等控制）"),
    })
    @Idempotent
    @PostMapping("/path")
    @PreAuthorize("hasAuthority('planning:write')")
    public Result<PlanningTask> planPath(@Valid @RequestBody PlanPathRequest request) {
        return Result.success(planningService.submitPathPlanning(request));
    }

    /**
     * 提交任务规划
     */
    @Operation(
        summary = "提交任务规划",
        description = "提交多无人机任务规划请求，包括无人机分配、任务调度和航线规划。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "任务规划提交成功",
            content = @Content(schema = @Schema(implementation = PlanningTask.class))),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @PostMapping("/mission")
    @PreAuthorize("hasAuthority('planning:write')")
    public Result<PlanningTask> planMission(@Valid @RequestBody PlanMissionRequest request) {
        return Result.success(planningService.submitMissionPlanning(request));
    }

    /**
     * 获取任务状态
     */
    @Operation(
        summary = "获取任务状态",
        description = "根据任务 ID 查询规划任务的当前状态，包括进度、创建时间、开始/完成时间等。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功",
            content = @Content(schema = @Schema(implementation = PlanningTask.class))),
        @ApiResponse(responseCode = "404", description = "任务不存在"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @GetMapping("/tasks/{id}")
    @PreAuthorize("hasAuthority('planning:read')")
    public Result<PlanningTask> getTask(
            @Parameter(description = "任务 ID", required = true, example = "1")
            @PathVariable Long id) {
        PlanningTask task = planningService.getTaskStatus(id);
        if (task == null) {
            return Result.error(com.uav.common.core.result.ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(task);
    }

    /**
     * 获取路径规划结果
     */
    @Operation(
        summary = "获取路径规划结果",
        description = "根据任务 ID 获取路径规划的最终结果，包括航点列表、总距离、预计时间、风险评分和能耗。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功",
            content = @Content(schema = @Schema(implementation = PathResult.class))),
        @ApiResponse(responseCode = "404", description = "任务不存在或结果未就绪"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @GetMapping("/tasks/{id}/result")
    @PreAuthorize("hasAuthority('planning:read')")
    public Result<PathResult> getPathResult(
            @Parameter(description = "任务 ID", required = true, example = "1")
            @PathVariable Long id) {
        PathResult result = planningService.getPathResult(id);
        if (result == null) {
            return Result.error(com.uav.common.core.result.ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(result);
    }

    /**
     * 获取任务规划结果
     */
    @Operation(
        summary = "获取任务规划结果",
        description = "根据任务 ID 获取多无人机任务规划的最终结果，包括无人机分配、任务分配和调度方案。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功",
            content = @Content(schema = @Schema(implementation = MissionPlan.class))),
        @ApiResponse(responseCode = "404", description = "任务不存在或结果未就绪"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @GetMapping("/tasks/{id}/mission")
    @PreAuthorize("hasAuthority('planning:read')")
    public Result<MissionPlan> getMissionPlan(
            @Parameter(description = "任务 ID", required = true, example = "1")
            @PathVariable Long id) {
        MissionPlan plan = planningService.getMissionPlan(id);
        if (plan == null) {
            return Result.error(com.uav.common.core.result.ResultCode.TASK_NOT_FOUND);
        }
        return Result.success(plan);
    }

    /**
     * 列出所有任务
     */
    @Operation(
        summary = "列出所有规划任务",
        description = "获取当前租户下所有路径规划和任务规划的任务列表，按创建时间倒序排列。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @GetMapping("/tasks")
    @PreAuthorize("hasAuthority('planning:read')")
    public Result<List<PlanningTask>> listTasks() {
        return Result.success(planningService.listTasks());
    }

    /**
     * 取消任务
     */
    @Operation(
        summary = "取消规划任务",
        description = "取消指定 ID 的规划任务。仅可取消 QUEUED 或 RUNNING 状态的任务。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "取消成功"),
        @ApiResponse(responseCode = "404", description = "任务不存在"),
        @ApiResponse(responseCode = "409", description = "任务状态不允许取消"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @PostMapping("/tasks/{id}/cancel")
    @PreAuthorize("hasAuthority('planning:write')")
    public Result<Void> cancelTask(
            @Parameter(description = "任务 ID", required = true, example = "1")
            @PathVariable Long id) {
        boolean cancelled = planningService.cancelTask(id);
        if (!cancelled) {
            return Result.error(com.uav.common.core.result.ResultCode.TASK_NOT_FOUND);
        }
        return Result.success();
    }
}
