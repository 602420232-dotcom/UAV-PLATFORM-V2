package com.uav.common.health;

import com.uav.common.script.PythonScriptInvoker;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/**
 * Python 运行环境健康检查
 * 
 * 验证 Python3 解释器和关键脚本的可用性。
 * 默认禁用 — 仅当显式设置 uav.python.health.enabled=true 时启用。
 */
@Component
@ConditionalOnProperty(name = "uav.python.health.enabled", havingValue = "true")
public class PythonHealthIndicator implements HealthIndicator {

    private final PythonScriptInvoker pythonScriptInvoker;

    public PythonHealthIndicator(PythonScriptInvoker pythonScriptInvoker) {
        this.pythonScriptInvoker = pythonScriptInvoker;
    }

    @Override
    public Health health() {
        try {
            boolean available = pythonScriptInvoker.isPythonAvailable();
            if (available) {
                return Health.up()
                    .withDetail("python", "available")
                    .withDetail("allowedScripts", pythonScriptInvoker.getAllowedScripts().size())
                    .build();
            } else {
                return Health.down()
                    .withDetail("python", "not found")
                    .withDetail("suggestion", "Install python3 and ensure it is in PATH")
                    .build();
            }
        } catch (Exception e) {
            return Health.down()
                .withDetail("python", "error")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}
