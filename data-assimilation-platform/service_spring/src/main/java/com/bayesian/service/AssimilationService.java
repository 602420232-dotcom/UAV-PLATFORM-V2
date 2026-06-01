package com.bayesian.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class AssimilationService {

    private static final Logger log = LoggerFactory.getLogger(AssimilationService.class);
    private final Map<String, Object> jobStore = new ConcurrentHashMap<>();
    private final PythonService pythonService;

    public AssimilationService(PythonService pythonService) {
        this.pythonService = pythonService;
    }

    public Map<String, Object> executeAssimilation(Map<String, Object> request) {
        String jobId = UUID.randomUUID().toString();
        log.info("开始同化任务: {}", jobId);
        jobStore.put(jobId, Map.of("status", "running", "algorithm", request.get("algorithm")));
        try {
            String result = pythonService.executeAssimilation(request);
            jobStore.put(jobId, Map.of("status", "completed", "result", result));
            return Map.of("jobId", jobId, "status", "completed", "result", result);
        } catch (Exception e) {
            log.error("同化任务失败: jobId={}", jobId, e);
            jobStore.put(jobId, Map.of("status", "failed", "error", "同化处理失败"));
            return Map.of("jobId", jobId, "status", "failed", "error", "同化处理失败");
        }
    }

    public Object getJobStatus(String jobId) {
        return jobStore.getOrDefault(jobId, Map.of("status", "not_found"));
    }
}
