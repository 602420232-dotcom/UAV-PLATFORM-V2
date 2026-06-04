package com.uav.bayesian.controller;
import com.uav.bayesian.service.AlertService;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/resilience")
public class ResilienceController {

    private final AlertService alertService;

    public ResilienceController(AlertService alertService) {
        this.alertService = alertService;
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, String>> status() {
        return ResponseEntity.ok(Map.of("circuitBreaker", "closed", "status", "healthy"));
    }

    @PostMapping("/test-degraded")
    public ResponseEntity<Map<String, String>> testDegraded() {
        alertService.notifyDegradedMode("test-service");
        return ResponseEntity.ok(Map.of("message", "降级测试完成"));
    }
}
