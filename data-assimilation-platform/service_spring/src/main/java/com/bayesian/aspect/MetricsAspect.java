package com.bayesian.aspect;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class MetricsAspect {

    private final MeterRegistry meterRegistry;

    public MetricsAspect(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    @Around("execution(* com.bayesian.service.AssimilationService.*(..))")
    public Object measureAssimilation(ProceedingJoinPoint joinPoint) throws Throwable {
        Timer.Sample sample = Timer.start(meterRegistry);
        Object result = joinPoint.proceed();
        sample.stop(Timer.builder("assimilation.execution")
                .tag("method", joinPoint.getSignature().getName())
                .register(meterRegistry));
        return result;
    }
}
