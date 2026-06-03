package com.uav.common.health;

import com.uav.common.script.PythonScriptInvoker;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

/**
 * Python 运行环境健康检查
 * 
 * 验证 Python3 解释器和关键脚本的可用性。
 * 用于 K8s readiness probe，当 Python 不可用时标记服务为未就绪。
 */
@Component
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
