package com.uav.weather.resilience;

import com.uav.common.exception.ServiceUnavailableException;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import jakarta.annotation.PostConstruct;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

/**
 * Weather Collector 熔断器服务
 * 
 * 提供对外部气象数据源的熔断保护
 */
@Service
public class WeatherCollectorCircuitBreakerService {
    
    private static final Logger log = LoggerFactory.getLogger(WeatherCollectorCircuitBreakerService.class);
    
    private final RestTemplate restTemplate;
    
    // 熔断器注册表
    private CircuitBreakerRegistry registry;
    
    // 各数据源熔断器
    private CircuitBreaker wrfCircuitBreaker;
    private CircuitBreaker satelliteCircuitBreaker;
    private CircuitBreaker groundStationCircuitBreaker;
    private CircuitBreaker buoyCircuitBreaker;
    
    // 配置
    @Value("${weather.circuit-breaker.failure-rate-threshold:60}")
    private double failureRateThreshold;
    
    @Value("${weather.circuit-breaker.wait-duration-in-open-state:30s}")
    private String waitDurationInOpenState;
    
    @Value("${weather.circuit-breaker.sliding-window-size:20}")
    private int slidingWindowSize;
    
    public WeatherCollectorCircuitBreakerService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    @PostConstruct
    public void init() {
        // 创建熔断器配置
        CircuitBreakerConfig config = CircuitBreakerConfig.custom()
                .failureRateThreshold((float) failureRateThreshold)
                .slowCallRateThreshold(80)
                .waitDurationInOpenState(Duration.parse("PT" + waitDurationInOpenState.replace("s", "")))
                .slidingWindowSize(slidingWindowSize)
                .slidingWindowType(CircuitBreakerConfig.SlidingWindowType.COUNT_BASED)
                .minimumNumberOfCalls(5)
                .build();
        
        // 创建熔断器注册表
        registry = CircuitBreakerRegistry.of(config);
        
        // 为各数据源创建熔断器
        wrfCircuitBreaker = registry.circuitBreaker("wrf-weather");
        satelliteCircuitBreaker = registry.circuitBreaker("satellite-weather");
        groundStationCircuitBreaker = registry.circuitBreaker("ground-station-weather");
        buoyCircuitBreaker = registry.circuitBreaker("buoy-weather");
        
        // 注册事件监听器
        registerEventListeners();
        
        log.info("Weather Collector Circuit Breaker initialized: failureRateThreshold={}, waitDuration={}", 
                failureRateThreshold, waitDurationInOpenState);
    }
    
    private void registerEventListeners() {
        // WRF熔断器监听
        wrfCircuitBreaker.getEventPublisher()
                .onStateTransition(event -> 
                    log.warn("WRF Circuit Breaker state transition: {} -> {}", 
                            event.getStateTransition().getFromState(),
                            event.getStateTransition().getToState()));
        
        // 卫星熔断器监听
        satelliteCircuitBreaker.getEventPublisher()
                .onStateTransition(event -> 
                    log.warn("Satellite Circuit Breaker state transition: {} -> {}",
                            event.getStateTransition().getFromState(),
                            event.getStateTransition().getToState()));
        
        // 地面站熔断器监听
        groundStationCircuitBreaker.getEventPublisher()
                .onStateTransition(event -> 
                    log.warn("Ground Station Circuit Breaker state transition: {} -> {}",
                            event.getStateTransition().getFromState(),
                            event.getStateTransition().getToState()));
        
        // 浮标熔断器监听
        buoyCircuitBreaker.getEventPublisher()
                .onStateTransition(event -> 
                    log.warn("Buoy Circuit Breaker state transition: {} -> {}",
                            event.getStateTransition().getFromState(),
                            event.getStateTransition().getToState()));
    }
    
    /**
     * 调用WRF气象模型（带熔断保护）
     */
    public ResponseEntity<Map> callWRFModel(String url, Class<Map> responseType) {
        try {
            return wrfCircuitBreaker.executeSupplier(() -> {
                log.debug("Calling WRF model: {}", url);
                ResponseEntity<Map> response = restTemplate.getForEntity(url, responseType);
                
                // 检查响应是否成功
                if (!response.getStatusCode().is2xxSuccessful()) {
                    throw new RuntimeException("WRF model returned error: " + response.getStatusCode());
                }
                
                return response;
            });
        } catch (Exception e) {
            log.error("WRF model call failed, circuit breaker opened", e);
            throw ServiceUnavailableException.serviceDown("wrf-weather", "WRF气象模型暂时不可用");
        }
    }
    
    /**
     * 调用卫星气象数据（带熔断保护）
     */
    public ResponseEntity<Map> callSatellite(String url, Class<Map> responseType) {
        try {
            return satelliteCircuitBreaker.executeSupplier(() -> {
                log.debug("Calling satellite: {}", url);
                ResponseEntity<Map> response = restTemplate.getForEntity(url, responseType);
                
                if (!response.getStatusCode().is2xxSuccessful()) {
                    throw new RuntimeException("Satellite returned error: " + response.getStatusCode());
                }
                
                return response;
            });
        } catch (Exception e) {
            log.error("Satellite call failed, circuit breaker opened", e);
            throw ServiceUnavailableException.serviceDown("satellite-weather", "卫星气象数据暂时不可用");
        }
    }
    
    /**
     * 调用地面气象站（带熔断保护）
     */
    public ResponseEntity<Map> callGroundStation(String url, Class<Map> responseType) {
        try {
            return groundStationCircuitBreaker.executeSupplier(() -> {
                log.debug("Calling ground station: {}", url);
                ResponseEntity<Map> response = restTemplate.getForEntity(url, responseType);
                
                if (!response.getStatusCode().is2xxSuccessful()) {
                    throw new RuntimeException("Ground station returned error: " + response.getStatusCode());
                }
                
                return response;
            });
        } catch (Exception e) {
            log.error("Ground station call failed, circuit breaker opened", e);
            throw ServiceUnavailableException.serviceDown("ground-station-weather", "地面气象站暂时不可用");
        }
    }
    
    /**
     * 调用浮标气象站（带熔断保护）
     */
    public ResponseEntity<Map> callBuoy(String url, Class<Map> responseType) {
        try {
            return buoyCircuitBreaker.executeSupplier(() -> {
                log.debug("Calling buoy: {}", url);
                ResponseEntity<Map> response = restTemplate.getForEntity(url, responseType);
                
                if (!response.getStatusCode().is2xxSuccessful()) {
                    throw new RuntimeException("Buoy returned error: " + response.getStatusCode());
                }
                
                return response;
            });
        } catch (Exception e) {
            log.error("Buoy call failed, circuit breaker opened", e);
            throw ServiceUnavailableException.serviceDown("buoy-weather", "浮标气象站暂时不可用");
        }
    }
    
    /**
     * 获取所有熔断器状态
     */
    public Map<String, Object> getCircuitBreakerStatus() {
        Map<String, Object> status = new HashMap<>();
        
        status.put("wrf-weather", getBreakerStatus(wrfCircuitBreaker));
        status.put("satellite-weather", getBreakerStatus(satelliteCircuitBreaker));
        status.put("ground-station-weather", getBreakerStatus(groundStationCircuitBreaker));
        status.put("buoy-weather", getBreakerStatus(buoyCircuitBreaker));
        
        return status;
    }
    
    private Map<String, Object> getBreakerStatus(CircuitBreaker breaker) {
        Map<String, Object> status = new HashMap<>();
        status.put("name", breaker.getName());
        status.put("state", breaker.getState());
        status.put("failureRate", breaker.getMetrics().getFailureRate());
        status.put("slowCallRate", breaker.getMetrics().getSlowCallRate());
        status.put("successfulCalls", breaker.getMetrics().getNumberOfSuccessfulCalls());
        status.put("failedCalls", breaker.getMetrics().getNumberOfFailedCalls());
        status.put("notPermittedCalls", breaker.getMetrics().getNumberOfNotPermittedCalls());
        return status;
    }
    
    /**
     * 手动触发熔断
     */
    public void tripCircuitBreaker(String name) {
        CircuitBreaker breaker = registry.circuitBreaker(name);
        breaker.transitionToOpenState();
        log.warn("Circuit breaker {} manually tripped", name);
    }
    
    /**
     * 手动重置熔断器
     */
    public void resetCircuitBreaker(String name) {
        CircuitBreaker breaker = registry.circuitBreaker(name);
        breaker.transitionToClosedState();
        log.info("Circuit breaker {} manually reset", name);
    }
}
