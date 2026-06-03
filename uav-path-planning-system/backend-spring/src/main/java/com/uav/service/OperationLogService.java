package com.uav.service;

import com.uav.model.OperationLog;
import com.uav.repository.OperationLogRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class OperationLogService {

    private final OperationLogRepository operationLogRepository;

    public OperationLogService(OperationLogRepository operationLogRepository) {
        this.operationLogRepository = operationLogRepository;
    }

    public List<OperationLog> findAll() {
        return operationLogRepository.findAllByOrderByCreatedAtDesc();
    }

    public OperationLog findById(Long id) {
        return operationLogRepository.findById(id).orElse(null);
    }

    public List<OperationLog> findByUsername(String username) {
        return operationLogRepository.findByUsername(username);
    }

    public List<OperationLog> findByOperation(String operation) {
        return operationLogRepository.findByOperation(operation);
    }

    public OperationLog create(OperationLog log) {
        return operationLogRepository.save(log);
    }

    public void clear() {
        operationLogRepository.deleteAll();
    }

    public List<OperationLog> getRecentLogs(int limit) {
        List<OperationLog> allLogs = operationLogRepository.findAllByOrderByCreatedAtDesc();
        return allLogs.subList(0, Math.min(limit, allLogs.size()));
    }
}
