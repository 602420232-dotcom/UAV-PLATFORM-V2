package com.uav.bayesian.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * Python 服务配置属性
 */
@Configuration
@ConfigurationProperties(prefix = "python")
public class PythonProperties {

    private Service service = new Service();

    public Service getService() {
        return service;
    }

    public void setService(Service service) {
        this.service = service;
    }

    public static class Service {
        private String url = "http://localhost:8000";
        private int timeout = 30000;

        public String getUrl() {
            return url;
        }

        public void setUrl(String url) {
            this.url = url;
        }

        public int getTimeout() {
            return timeout;
        }

        public void setTimeout(int timeout) {
            this.timeout = timeout;
        }
    }
}
