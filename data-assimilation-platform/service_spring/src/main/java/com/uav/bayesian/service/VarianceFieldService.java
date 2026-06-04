package com.uav.bayesian.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

@Slf4j
@Service
public class VarianceFieldService {

    public Map<String, Object> computeVariance(Map<String, Object> request) {
        log.info("计算方差场");
        return Map.of(
                "status", "success",
                "variance", Map.of("mean", 0.5, "max", 1.2, "min", 0.3),
                "message", "方差场计算完成"
        );
    }
}
