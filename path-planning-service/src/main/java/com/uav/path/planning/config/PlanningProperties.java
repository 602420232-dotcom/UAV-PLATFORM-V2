package com.uav.path.planning.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 路径规划服务配置属性
 */
@Configuration
@ConfigurationProperties(prefix = "planning")
public class PlanningProperties {

    private String pythonScript = "three_layer_planner.py";

    public String getPythonScript() {
        return pythonScript;
    }

    public void setPythonScript(String pythonScript) {
        this.pythonScript = pythonScript;
    }
}
