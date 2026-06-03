package com.uav.path.planning.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 路径规划服务 UAV 配置属性
 */
@Configuration
@ConfigurationProperties(prefix = "uav")
public class UavProperties {

    private Python python = new Python();

    public Python getPython() {
        return python;
    }

    public void setPython(Python python) {
        this.python = python;
    }

    public static class Python {
        private String scriptPath = "/app/python";
        private int timeout = 60000;

        public String getScriptPath() {
            return scriptPath;
        }

        public void setScriptPath(String scriptPath) {
            this.scriptPath = scriptPath;
        }

        public int getTimeout() {
            return timeout;
        }

        public void setTimeout(int timeout) {
            this.timeout = timeout;
        }
    }
}
