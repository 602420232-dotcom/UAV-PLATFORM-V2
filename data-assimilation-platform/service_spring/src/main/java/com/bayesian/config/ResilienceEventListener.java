package com.bayesian.config;

import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.core.EventPublisher;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class ResilienceEventListener {

    private static final Logger log = LoggerFactory.getLogger(ResilienceEventListener.class);
    private final CircuitBreakerRegistry circuitBreakerRegistry;

    public ResilienceEventListener(CircuitBreakerRegistry circuitBreakerRegistry) {
        this.circuitBreakerRegistry = circuitBreakerRegistry;
    }

    @PostConstruct
    public void registerListeners() {
        circuitBreakerRegistry.getAllCircuitBreakers().forEach(cb -> {
            cb.getEventPublisher().onStateTransition(event ->
                    log.warn("CircuitBreaker '{}' 状态变更: {} -> {}",
                            event.getCircuitBreakerName(),
                            event.getStateTransition().getFromState(),
                            event.getStateTransition().getToState()));
        });
    }
}
