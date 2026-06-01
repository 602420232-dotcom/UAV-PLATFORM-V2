package com.uav.common.resilience;

import io.github.resilience4j.circuitbreaker.*;
import io.github.resilience4j.circuitbreaker.event.*;
import io.github.resilience4j.retry.Retry;
import io.github.resilience4j.retry.RetryConfig;
import io.github.resilience4j.retry.RetryRegistry;
import io.github.resilience4j.timelimiter.TimeLimiter;
import io.github.resilience4j.timelimiter.TimeLimiterConfig;
import io.github.resilience4j.timelimiter.TimeLimiterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.TimeoutException;

/**
 * Resilience4j 熔断器配置类
 * 为微服务间调用提供熔断、重试、限流保护
 */
@Configuration
@EnableConfigurationProperties
public class ResilienceConfig {
    
    private static final Logger log = LoggerFactory.getLogger(ResilienceConfig.class);
    
    @Value("${spring.application.name:unknown}")
    private String applicationName;
    
    @Value("${resilience4j.circuitbreaker.configs.default.failureRateThreshold:50}")
    private float failureRateThreshold;
    
    @Value("${resilience4j.circuitbreaker.configs.default.waitDurationInOpenState:10s}")
    private Duration waitDurationInOpenState;
    
    @Value("${resilience4j.circuitbreaker.configs.default.slidingWindowSize:10}")
    private int slidingWindowSize;
    
    /**
     * 配置 CircuitBreakerRegistry
     */
    @Bean
    public CircuitBreakerRegistry circuitBreakerRegistry() {
        CircuitBreakerConfig defaultConfig = CircuitBreakerConfig.custom()
                .failureRateThreshold(failureRateThreshold)
                .waitDurationInOpenState(waitDurationInOpenState)
                .slidingWindowSize(slidingWindowSize)
                .slidingWindowType(CircuitBreakerConfig.SlidingWindowType.COUNT_BASED)
                .minimumNumberOfCalls(5)
                .permittedNumberOfCallsInHalfOpenState(3)
                .automaticTransitionFromOpenToHalfOpenEnabled(true)
                .build();
        
        CircuitBreakerRegistry registry = CircuitBreakerRegistry.of(defaultConfig);

        return registry;
    }
    
    /**
     * 为气象预报服务创建熔断器
     */
    @Bean("meteorForecastCircuitBreaker")
    public CircuitBreaker meteorForecastCircuitBreaker(CircuitBreakerRegistry registry) {
        CircuitBreaker circuitBreaker = registry.circuitBreaker("meteor-forecast-service");
        
        // 添加事件监听
        circuitBreaker.getEventPublisher()
                .onStateTransition(event -> 
                    log.warn("Meteor Forecast Circuit Breaker state changed: {} -> {}", 
                            event.getStateTransition().getFromState(),
                            event.getStateTransition().getToState()))
                .onError(event ->
                    log.error("Meteor Forecast Circuit Breaker error: {}", event.getThrowable().getMessage()))
                .onSuccess(event ->
                    log.debug("Meteor Forecast Circuit Breaker success"));
        
        return circuitBreaker;
    }
    
    /**
     * 为路径规划服务创建熔断器
     */
    @Bean("pathPlanningCircuitBreaker")
    public CircuitBreaker pathPlanningCircuitBreaker(CircuitBreakerRegistry registry) {
        CircuitBreaker circuitBreaker = registry.circuitBreaker("path-planning-service");
        
        circuitBreaker.getEventPublisher()
                .onStateTransition(event -> 
                    log.warn("Path Planning Circuit Breaker state changed: {} -> {}", 
                            event.getStateTransition().getFromState(),
                            event.getStateTransition().getToState()))
                .onError(event ->
                    log.error("Path Planning Circuit Breaker error: {}", event.getThrowable().getMessage()));
        
        return circuitBreaker;
    }
    
    /**
     * 为数据同化服务创建熔断器
     */
    @Bean("dataAssimilationCircuitBreaker")
    public CircuitBreaker dataAssimilationCircuitBreaker(CircuitBreakerRegistry registry) {
        CircuitBreaker circuitBreaker = registry.circuitBreaker("data-assimilation-service");
        
        circuitBreaker.getEventPublisher()
                .onStateTransition(event -> 
                    log.warn("Data Assimilation Circuit Breaker state changed: {} -> {}", 
                            event.getStateTransition().getFromState(),
                            event.getStateTransition().getToState()))
                .onError(event ->
                    log.error("Data Assimilation Circuit Breaker error: {}", event.getThrowable().getMessage()));
        
        return circuitBreaker;
    }
    
    /**
     * 配置 RetryRegistry
     */
    @Bean
    public RetryRegistry retryRegistry() {
        RetryConfig defaultConfig = RetryConfig.custom()
                .maxAttempts(3)
                .waitDuration(Duration.ofMillis(500))
                .retryExceptions(IOException.class, TimeoutException.class)
                .build();
        
        return RetryRegistry.of(defaultConfig);
    }
    
    /**
     * 为气象预报服务创建重试器
     */
    @Bean("meteorForecastRetry")
    public Retry meteorForecastRetry(RetryRegistry registry) {
        Retry retry = registry.retry("meteor-forecast-service");
        
        retry.getEventPublisher()
                .onRetry(event ->
                    log.warn("Retrying Meteor Forecast call, attempt: {}", event.getNumberOfRetryAttempts()));
        
        return retry;
    }
    
    /**
     * 为路径规划服务创建重试器
     */
    @Bean("pathPlanningRetry")
    public Retry pathPlanningRetry(RetryRegistry registry) {
        Retry retry = registry.retry("path-planning-service");
        
        retry.getEventPublisher()
                .onRetry(event ->
                    log.warn("Retrying Path Planning call, attempt: {}", event.getNumberOfRetryAttempts()));
        
        return retry;
    }
    
    /**
     * 为数据同化服务创建重试器
     */
    @Bean("dataAssimilationRetry")
    public Retry dataAssimilationRetry(RetryRegistry registry) {
        Retry retry = registry.retry("data-assimilation-service");
        
        retry.getEventPublisher()
                .onRetry(event ->
                    log.warn("Retrying Data Assimilation call, attempt: {}", event.getNumberOfRetryAttempts()));
        
        return retry;
    }
    
    /**
     * 配置 TimeLimiterRegistry
     */
    @Bean
    public TimeLimiterRegistry timeLimiterRegistry() {
        TimeLimiterConfig defaultConfig = TimeLimiterConfig.custom()
                .timeoutDuration(Duration.ofSeconds(5))
                .cancelRunningFuture(true)
                .build();
        
        return TimeLimiterRegistry.of(defaultConfig);
    }
    
    /**
     * 创建带有超时和重试的 RestTemplate
     */
    @Bean
    public RestTemplate resilientRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);    // 连接超时 5秒
        factory.setReadTimeout(10000);     // 读取超时 10秒
        
        return new RestTemplate(factory);
    }
    
    /**
     * 初始化日志
     */
    @PostConstruct
    public void init() {
        log.info("========================================");
        log.info("Resilience4j Circuit Breaker 配置已加载");
        log.info("应用名称: {}", applicationName);
        log.info("失败率阈值: {}%", failureRateThreshold);
        log.info("熔断器等待时间: {}", waitDurationInOpenState);
        log.info("滑动窗口大小: {}", slidingWindowSize);
        log.info("========================================");
    }
}
