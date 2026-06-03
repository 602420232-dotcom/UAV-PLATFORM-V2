package com.uav.assimilation.service.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 数据同化服务配置属性
 */
@Configuration
@ConfigurationProperties(prefix = "assimilation")
public class AssimilationProperties {

    private String pythonScript = "data_assimilation.py";

    public String getPythonScript() {
        return pythonScript;
    }

    public void setPythonScript(String pythonScript) {
        this.pythonScript = pythonScript;
    }
}
