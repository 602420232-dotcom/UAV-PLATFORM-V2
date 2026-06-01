package com.uav.controller;
import com.uav.config.SecurityAuditConfig;
import com.uav.service.RealDataSourceService;
import org.springframework.http.ResponseEntity;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/real-data")
public class RealDataSourceController {

    private final RealDataSourceService realDataSourceService;

    public RealDataSourceController(RealDataSourceService realDataSourceService) {
        this.realDataSourceService = realDataSourceService;
    }

    @GetMapping("/ground-station")
    public ResponseEntity<Map<String, Object>> getGroundStationData() {
        String username = SecurityAuditConfig.getCurrentUsername();
        List<Map<String, Object>> data = realDataSourceService.getGroundStationData();
        SecurityAuditConfig.logUserActivity(username, "获取地面站数据", "成功获取地面站数据");
        return ResponseEntity.ok(Map.of("code", 200, "message", "获取地面站数据成功", "data", data));
    }

    @GetMapping("/buoy")
    public ResponseEntity<Map<String, Object>> getBuoyData() {
        String username = SecurityAuditConfig.getCurrentUsername();
        List<Map<String, Object>> data = realDataSourceService.getBuoyData();
        SecurityAuditConfig.logUserActivity(username, "获取浮标数据", "成功获取浮标数据");
        return ResponseEntity.ok(Map.of("code", 200, "message", "获取浮标数据成功", "data", data));
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getDataSourceStatus() {
        String username = SecurityAuditConfig.getCurrentUsername();
        Map<String, Object> status = realDataSourceService.getDataSourceStatus();
        SecurityAuditConfig.logUserActivity(username, "获取数据源状态", "成功获取数据源状态");
        return ResponseEntity.ok(Map.of("code", 200, "message", "获取数据源状态成功", "data", status));
    }
}
