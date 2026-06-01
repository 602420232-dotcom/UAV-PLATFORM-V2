package com.bayesian.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class AlertService {

    private static final Logger log = LoggerFactory.getLogger(AlertService.class);

    public void sendAlert(String severity, String message) {
        log.warn("告警 [{}]: {}", severity, message);
    }

    public void notifyDegradedMode(String serviceName) {
        sendAlert("WARNING", "服务 " + serviceName + " 已进入降级模式");
    }

    public void notifyRecovery(String serviceName) {
        sendAlert("INFO", "服务 " + serviceName + " 已恢复");
    }
}
