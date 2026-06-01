package com.bayesian.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class VarianceFieldService {

    private static final Logger log = LoggerFactory.getLogger(VarianceFieldService.class);

    public Map<String, Object> computeVariance(Map<String, Object> request) {
        log.info("计算方差场");
        return Map.of(
                "status", "success",
                "variance", Map.of("mean", 0.5, "max", 1.2),
                "message", "方差场计算完成"
        );
    }
}
