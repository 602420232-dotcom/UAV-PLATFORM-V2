package com.uav.utm.controller;

import com.uav.common.core.result.Result;
import com.uav.utm.dto.ConflictCheckRequest;
import com.uav.utm.dto.UavPositionReport;
import com.uav.utm.entity.ConflictAlert;
import com.uav.utm.entity.UavPosition;
import com.uav.utm.service.UavTrackingService;
import com.uav.utm.ws.SubscriptionManager;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Set;

@RestController
@RequestMapping("/api/v1/tracking")
public class UavTrackingController {

    private final UavTrackingService uavTrackingService;
    private final SubscriptionManager subscriptionManager;

    public UavTrackingController(UavTrackingService uavTrackingService, SubscriptionManager subscriptionManager) {
        this.uavTrackingService = uavTrackingService;
        this.subscriptionManager = subscriptionManager;
    }

    @PostMapping("/positions")
    public Result<UavPosition> reportPosition(@Valid @RequestBody UavPositionReport report) {
        return Result.success(uavTrackingService.reportPosition(report));
    }

    @GetMapping("/uavs/{uavId}/position")
    public Result<UavPosition> getCurrentPosition(@PathVariable String uavId) {
        return uavTrackingService.getCurrentPosition(uavId)
                .map(Result::success)
                .orElse(Result.error(404, "Position not found"));
    }

    @GetMapping("/uavs/{uavId}/history")
    public Result<List<UavPosition>> getTrackHistory(@PathVariable String uavId) {
        return Result.success(uavTrackingService.getTrackHistory(uavId));
    }

    @PostMapping("/conflicts/check")
    public Result<List<ConflictAlert>> checkConflicts(@Valid @RequestBody ConflictCheckRequest request) {
        return Result.success(uavTrackingService.checkConflicts(request.getUavId()));
    }

    // ===== WebSocket 订阅查询 =====

    /**
     * 查询指定 session 的订阅频道
     *
     * @param sessionId WebSocket 会话ID
     * @return 订阅的频道集合
     */
    @GetMapping("/ws/subscriptions")
    public Result<Set<String>> getSubscriptions(@RequestParam String sessionId) {
        Set<String> subscriptions = subscriptionManager.getSubscriptionsById(sessionId);
        return Result.success(subscriptions);
    }
}
