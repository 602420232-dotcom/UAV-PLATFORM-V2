package com.uav.controller;
import com.uav.model.OperationLog;
import com.uav.service.OperationLogService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/admin/logs")
public class OperationLogController {

    private final OperationLogService operationLogService;

    public OperationLogController(OperationLogService operationLogService) {
        this.operationLogService = operationLogService;
    }

    @GetMapping
    public List<OperationLog> getAllLogs() {
        return operationLogService.findAll();
    }

    @GetMapping("/{id}")
    public ResponseEntity<OperationLog> getLogById(@PathVariable Long id) {
        OperationLog log = operationLogService.findById(id);
        if (log == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(log);
    }

    @GetMapping("/user/{username}")
    public List<OperationLog> getLogsByUsername(@PathVariable String username) {
        return operationLogService.findByUsername(username);
    }

    @GetMapping("/operation/{operation}")
    public List<OperationLog> getLogsByOperation(@PathVariable String operation) {
        return operationLogService.findByOperation(operation);
    }

    @DeleteMapping
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void clearAllLogs() {
        operationLogService.clear();
    }

    @GetMapping("/recent")
    public List<OperationLog> getRecentLogs() {
        return operationLogService.getRecentLogs(50);
    }
}
