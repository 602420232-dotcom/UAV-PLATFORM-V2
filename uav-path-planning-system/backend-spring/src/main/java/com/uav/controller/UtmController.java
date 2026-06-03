package com.uav.controller;

import com.uav.common.integration.UtmService;
import com.uav.common.integration.UtmService.EmergencyType;
import com.uav.common.integration.dto.AirspaceStatus;
import com.uav.common.integration.dto.DroneInfo;
import com.uav.common.integration.dto.EmergencyResponse;
import com.uav.common.integration.dto.FlightApproval;
import com.uav.common.integration.dto.FlightPlan;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/dispatcher/utm")
@Tag(name = "UTM Integration", description = "无人机交通管理系统集成接口")
public class UtmController {

    private final UtmService utmService;

    public UtmController(UtmService utmService) {
        this.utmService = utmService;
    }

    @PostMapping("/register-drone")
    @Operation(summary = "注册无人机", description = "在UTM系统中注册无人机信息")
    public ResponseEntity<Map<String, String>> registerDrone(@Valid @RequestBody DroneInfo droneInfo) {
        String registrationId = utmService.registerDrone(droneInfo);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(Map.of("registrationId", registrationId));
    }

    @PostMapping("/flight-plan")
    @Operation(summary = "提交飞行计划", description = "向UTM系统提交飞行计划并等待审批")
    public ResponseEntity<Map<String, Object>> submitFlightPlan(@Valid @RequestBody FlightPlan plan) {
        boolean approved = utmService.submitFlightPlan(plan);
        return ResponseEntity.ok(Map.of(
                "planId", plan.getPlanId(),
                "approved", approved
        ));
    }

    @GetMapping("/approval/{planId}")
    @Operation(summary = "查询审批状态", description = "查询飞行计划在UTM系统中的审批状态")
    public ResponseEntity<FlightApproval> getFlightApproval(@PathVariable String planId) {
        FlightApproval approval = utmService.getFlightApproval(planId);
        return ResponseEntity.ok(approval);
    }

    @GetMapping("/airspace")
    @Operation(summary = "查询空域状态", description = "查询指定位置和半径范围内的空域状态")
    public ResponseEntity<AirspaceStatus> queryAirspace(
            @RequestParam double lat,
            @RequestParam double lon,
            @RequestParam double radius) {
        AirspaceStatus status = utmService.queryAirspace(lat, lon, radius);
        return ResponseEntity.ok(status);
    }

    @PostMapping("/emergency")
    @Operation(summary = "发送紧急警报", description = "向UTM系统发送无人机紧急情况警报")
    public ResponseEntity<EmergencyResponse> sendEmergencyAlert(
            @RequestBody Map<String, String> request) {
        String droneId = request.get("droneId");
        String typeStr = request.get("type");

        if (droneId == null || droneId.isBlank()) {
            return ResponseEntity.badRequest().build();
        }

        EmergencyType type = EmergencyType.OTHER;
        if (typeStr != null && !typeStr.isBlank()) {
            try {
                type = EmergencyType.valueOf(typeStr.toUpperCase());
            } catch (IllegalArgumentException e) {
                type = EmergencyType.OTHER;
            }
        }

        EmergencyResponse response = utmService.sendEmergencyAlert(droneId, type);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
