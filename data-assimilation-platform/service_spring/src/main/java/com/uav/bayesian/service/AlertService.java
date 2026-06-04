package com.uav.bayesian.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class AlertService {

    public void sendAlert(String severity, String message) {
        log.warn("警报 [{}]: {}", severity, message);
    }

    public void notifyDegradedMode(String serviceName) {
        sendAlert("WARNING", "服务 " + serviceName + " 已进入降级模式");
    }

    public void notifyRecovery(String serviceName) {
        sendAlert("INFO", "服务 " + serviceName + " 已恢复");
    }
}
