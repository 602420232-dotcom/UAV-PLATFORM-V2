package com.uav.common.resilience;

import com.uav.common.exception.ServiceUnavailableException;
import io.github.resilience4j.circuitbreaker.CallNotPermittedException;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.retry.Retry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import jakarta.annotation.Resource;
import java.util.function.Supplier;

/**
 * 熔断器服务调用封装
 * 提供对各微服务的熔断保护调用
 */
@Service
public class CircuitBreakerService {
    
    private static final Logger log = LoggerFactory.getLogger(CircuitBreakerService.class);
    
    @Autowired
    @Qualifier("resilientRestTemplate")
    private RestTemplate restTemplate;
    
    @Resource
    @Qualifier("meteorForecastCircuitBreaker")
    private CircuitBreaker meteorForecastCircuitBreaker;
    
    @Resource
    @Qualifier("pathPlanningCircuitBreaker")
    private CircuitBreaker pathPlanningCircuitBreaker;
    
    @Resource
    @Qualifier("dataAssimilationCircuitBreaker")
    private CircuitBreaker dataAssimilationCircuitBreaker;
    
    @Resource
    @Qualifier("meteorForecastRetry")
    private Retry meteorForecastRetry;
    
    @Resource
    @Qualifier("pathPlanningRetry")
    private Retry pathPlanningRetry;
    
    @Resource
    @Qualifier("dataAssimilationRetry")
    private Retry dataAssimilationRetry;
    
    /**
     * 调用气象预报服务（带熔断和重试）
     */
    public <T> ResponseEntity<T> callMeteorForecast(String url, Class<T> responseType) {
        Supplier<ResponseEntity<T>> supplier = () -> {
            log.debug("Calling Meteor Forecast Service: {}", url);
            return restTemplate.getForEntity(url, responseType);
        };
        
        // 使用熔断器包装
        Supplier<ResponseEntity<T>> decoratedSupplier = CircuitBreaker
                .decorateSupplier(meteorForecastCircuitBreaker, supplier);
        
        // 使用重试器包装
        decoratedSupplier = Retry.decorateSupplier(meteorForecastRetry, decoratedSupplier);
        
        try {
            return decoratedSupplier.get();
        } catch (CallNotPermittedException e) {
            log.error("Meteor Forecast Circuit Breaker is OPEN, call rejected");
            throw ServiceUnavailableException.circuitBreakerOpen("meteor-forecast-service");
        } catch (Exception e) {
            log.error("Meteor Forecast Service call failed: {}", e.getMessage());
            throw ServiceUnavailableException.serviceDown("meteor-forecast-service", e.getMessage());
        }
    }
    
    /**
     * 调用路径规划服务（带熔断和重试）
     */
    public <T> ResponseEntity<T> callPathPlanning(String url, Class<T> responseType) {
        Supplier<ResponseEntity<T>> supplier = () -> {
            log.debug("Calling Path Planning Service: {}", url);
            return restTemplate.getForEntity(url, responseType);
        };
        
        Supplier<ResponseEntity<T>> decoratedSupplier = CircuitBreaker
                .decorateSupplier(pathPlanningCircuitBreaker, supplier);
        
        decoratedSupplier = Retry.decorateSupplier(pathPlanningRetry, decoratedSupplier);
        
        try {
            return decoratedSupplier.get();
        } catch (CallNotPermittedException e) {
            log.error("Path Planning Circuit Breaker is OPEN, call rejected");
            throw ServiceUnavailableException.circuitBreakerOpen("path-planning-service");
        } catch (Exception e) {
            log.error("Path Planning Service call failed: {}", e.getMessage());
            throw ServiceUnavailableException.serviceDown("path-planning-service", e.getMessage());
        }
    }
    
    /**
     * 调用数据同化服务（带熔断和重试）
     */
    public <T> ResponseEntity<T> callDataAssimilation(String url, Class<T> responseType) {
        Supplier<ResponseEntity<T>> supplier = () -> {
            log.debug("Calling Data Assimilation Service: {}", url);
            return restTemplate.getForEntity(url, responseType);
        };
        
        Supplier<ResponseEntity<T>> decoratedSupplier = CircuitBreaker
                .decorateSupplier(dataAssimilationCircuitBreaker, supplier);
        
        decoratedSupplier = Retry.decorateSupplier(dataAssimilationRetry, decoratedSupplier);
        
        try {
            return decoratedSupplier.get();
        } catch (CallNotPermittedException e) {
            log.error("Data Assimilation Circuit Breaker is OPEN, call rejected");
            throw ServiceUnavailableException.circuitBreakerOpen("data-assimilation-service");
        } catch (Exception e) {
            log.error("Data Assimilation Service call failed: {}", e.getMessage());
            throw ServiceUnavailableException.serviceDown("data-assimilation-service", e.getMessage());
        }
    }
    
    /**
     * 获取熔断器状态
     */
    public CircuitBreakerStatus getCircuitBreakerStatus(String serviceName) {
        CircuitBreaker circuitBreaker = getCircuitBreaker(serviceName);
        
        CircuitBreaker.State state = circuitBreaker.getState();
        CircuitBreaker.Metrics metrics = circuitBreaker.getMetrics();
        
        return new CircuitBreakerStatus(
                serviceName,
                state.name(),
                metrics.getFailureRate(),
                metrics.getNumberOfSuccessfulCalls(),
                metrics.getNumberOfFailedCalls(),
                metrics.getNumberOfNotPermittedCalls()
        );
    }
    
    private CircuitBreaker getCircuitBreaker(String serviceName) {
        switch (serviceName) {
            case "meteor-forecast-service":
                return meteorForecastCircuitBreaker;
            case "path-planning-service":
                return pathPlanningCircuitBreaker;
            case "data-assimilation-service":
                return dataAssimilationCircuitBreaker;
            default:
                throw new IllegalArgumentException("Unknown service: " + serviceName);
        }
    }
    
    /**
     * 熔断器状态DTO
     */
    public static class CircuitBreakerStatus {
        private final String serviceName;
        private final String state;
        private final float failureRate;
        private final long successfulCalls;
        private final long failedCalls;
        private final long notPermittedCalls;
        
        public CircuitBreakerStatus(String serviceName, String state, float failureRate,
                                    long successfulCalls, long failedCalls, long notPermittedCalls) {
            this.serviceName = serviceName;
            this.state = state;
            this.failureRate = failureRate;
            this.successfulCalls = successfulCalls;
            this.failedCalls = failedCalls;
            this.notPermittedCalls = notPermittedCalls;
        }
        
        public String getServiceName() { return serviceName; }
        public String getState() { return state; }
        public float getFailureRate() { return failureRate; }
        public long getSuccessfulCalls() { return successfulCalls; }
        public long getFailedCalls() { return failedCalls; }
        public long getNotPermittedCalls() { return notPermittedCalls; }
    }
}
