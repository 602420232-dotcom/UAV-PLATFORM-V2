package com.uav.common.resilience;

import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 熔断器监控REST接口
 * 提供熔断器状态查询和手动控制
 * 
 * 安全说明:
 * - 查询端点 (/status, /details): 需要 ADMIN 或 OPERATOR 角色
 * - 管理端点 (/trip, /reset, /half-open): 仅限 ADMIN 角色
 * - 健康检查 (/health): 公开访问
 */
@RestController
@RequestMapping("/api/admin/circuit-breaker")
public class CircuitBreakerController {

    private final CircuitBreakerRegistry circuitBreakerRegistry;
    private final CircuitBreakerService circuitBreakerService;

    public CircuitBreakerController(CircuitBreakerRegistry circuitBreakerRegistry,
                                    CircuitBreakerService circuitBreakerService) {
        this.circuitBreakerRegistry = circuitBreakerRegistry;
        this.circuitBreakerService = circuitBreakerService;
    }
    
    /**
     * 获取所有熔断器状态
     * 权限: ADMIN 或 OPERATOR
     */
    @GetMapping("/status")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
    public ResponseEntity<Map<String, Object>> getAllCircuitBreakerStatus() {
        Map<String, Object> response = new HashMap<>();
        List<Map<String, Object>> breakers = new ArrayList<>();
        
        circuitBreakerRegistry.getAllCircuitBreakers().forEach(cb -> {
            Map<String, Object> breakerInfo = new HashMap<>();
            breakerInfo.put("name", cb.getName());
            breakerInfo.put("state", cb.getState().name());
            breakerInfo.put("failureRate", cb.getMetrics().getFailureRate());
            breakerInfo.put("successfulCalls", cb.getMetrics().getNumberOfSuccessfulCalls());
            breakerInfo.put("failedCalls", cb.getMetrics().getNumberOfFailedCalls());
            breakerInfo.put("notPermittedCalls", cb.getMetrics().getNumberOfNotPermittedCalls());
            breakerInfo.put("bufferedCalls", cb.getMetrics().getNumberOfBufferedCalls());
            breakerInfo.put("threshold", cb.getCircuitBreakerConfig().getFailureRateThreshold());
            
            breakers.add(breakerInfo);
        });
        
        response.put("totalBreakers", breakers.size());
        response.put("breakers", breakers);
        response.put("timestamp", System.currentTimeMillis());
        
        return ResponseEntity.ok(response);
    }
    
    /**
     * 获取指定熔断器状态
     * 权限: ADMIN 或 OPERATOR
     */
    @GetMapping("/status/{serviceName}")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
    public ResponseEntity<CircuitBreakerService.CircuitBreakerStatus> getCircuitBreakerStatus(
            @PathVariable String serviceName) {
        try {
            CircuitBreakerService.CircuitBreakerStatus status = 
                    circuitBreakerService.getCircuitBreakerStatus(serviceName);
            return ResponseEntity.ok(status);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 获取熔断器详细信息
     * 权限: ADMIN 或 OPERATOR
     */
    @GetMapping("/details/{serviceName}")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
    public ResponseEntity<Map<String, Object>> getCircuitBreakerDetails(
            @PathVariable String serviceName) {
        
        CircuitBreaker circuitBreaker = circuitBreakerRegistry.circuitBreaker(serviceName);
        CircuitBreakerConfig config = circuitBreaker.getCircuitBreakerConfig();
        CircuitBreaker.Metrics metrics = circuitBreaker.getMetrics();
        
        Map<String, Object> details = new HashMap<>();
        details.put("name", circuitBreaker.getName());
        details.put("state", circuitBreaker.getState().name());
        
        // 配置信息
        Map<String, Object> configInfo = new HashMap<>();
        configInfo.put("failureRateThreshold", config.getFailureRateThreshold());
        configInfo.put("slidingWindowSize", config.getSlidingWindowSize());
        configInfo.put("minimumNumberOfCalls", config.getMinimumNumberOfCalls());
        configInfo.put("waitDurationInOpenState", config.getSlidingWindowSize() + " calls");
        configInfo.put("permittedNumberOfCallsInHalfOpenState", 
                      config.getPermittedNumberOfCallsInHalfOpenState());
        configInfo.put("automaticTransitionFromOpenToHalfOpenEnabled", 
                      config.isAutomaticTransitionFromOpenToHalfOpenEnabled());
        details.put("config", configInfo);
        
        // 指标信息
        Map<String, Object> metricsInfo = new HashMap<>();
        metricsInfo.put("failureRate", metrics.getFailureRate());
        metricsInfo.put("successfulCalls", metrics.getNumberOfSuccessfulCalls());
        metricsInfo.put("failedCalls", metrics.getNumberOfFailedCalls());
        metricsInfo.put("notPermittedCalls", metrics.getNumberOfNotPermittedCalls());
        metricsInfo.put("bufferedCalls", metrics.getNumberOfBufferedCalls());
        metricsInfo.put("slowCalls", metrics.getNumberOfSlowCalls());
        metricsInfo.put("slowCallRate", metrics.getSlowCallRate());
        details.put("metrics", metricsInfo);
        
        return ResponseEntity.ok(details);
    }
    
    /**
     * 手动触发熔断（强制打开）
     * 权限: 仅限 ADMIN
     */
    @PostMapping("/trip/{serviceName}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> tripCircuitBreaker(
            @PathVariable String serviceName) {
        
        try {
            CircuitBreaker circuitBreaker = circuitBreakerRegistry.circuitBreaker(serviceName);
            circuitBreaker.transitionToOpenState();
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Circuit breaker for " + serviceName + " has been tripped (opened)");
            response.put("newState", circuitBreaker.getState().name());
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 手动恢复熔断（强制关闭）
     * 权限: 仅限 ADMIN
     */
    @PostMapping("/reset/{serviceName}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> resetCircuitBreaker(
            @PathVariable String serviceName) {
        
        try {
            CircuitBreaker circuitBreaker = circuitBreakerRegistry.circuitBreaker(serviceName);
            circuitBreaker.transitionToClosedState();
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Circuit breaker for " + serviceName + " has been reset (closed)");
            response.put("newState", circuitBreaker.getState().name());
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 强制转换到半开状态
     * 权限: 仅限 ADMIN
     */
    @PostMapping("/half-open/{serviceName}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> halfOpenCircuitBreaker(
            @PathVariable String serviceName) {
        
        try {
            CircuitBreaker circuitBreaker = circuitBreakerRegistry.circuitBreaker(serviceName);
            circuitBreaker.transitionToHalfOpenState();
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Circuit breaker for " + serviceName + " is now in half-open state");
            response.put("newState", circuitBreaker.getState().name());
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 健康检查端点
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        Map<String, Object> health = new HashMap<>();
        List<Map<String, Object>> unhealthy = new ArrayList<>();
        
        circuitBreakerRegistry.getAllCircuitBreakers().forEach(cb -> {
            if (cb.getState() == CircuitBreaker.State.OPEN || 
                cb.getState() == CircuitBreaker.State.FORCED_OPEN) {
                Map<String, Object> info = new HashMap<>();
                info.put("name", cb.getName());
                info.put("state", cb.getState().name());
                info.put("failureRate", cb.getMetrics().getFailureRate());
                unhealthy.add(info);
            }
        });
        
        health.put("status", unhealthy.isEmpty() ? "UP" : "DEGRADED");
        health.put("totalBreakers", circuitBreakerRegistry.getAllCircuitBreakers().size());
        health.put("openBreakers", unhealthy.size());
        health.put("unhealthyServices", unhealthy);
        health.put("timestamp", System.currentTimeMillis());
        
        return unhealthy.isEmpty() ? 
                ResponseEntity.ok(health) : 
                ResponseEntity.status(503).body(health);
    }
}
