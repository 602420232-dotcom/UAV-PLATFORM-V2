package com.uav.meteor.forecast.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 气象预报服务配置属性
 */
@Configuration
@ConfigurationProperties(prefix = "forecast")
public class ForecastProperties {

    private String pythonScript = "meteor_forecast.py";

    public String getPythonScript() {
        return pythonScript;
    }

    public void setPythonScript(String pythonScript) {
        this.pythonScript = pythonScript;
    }
}
