package com.uav.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 路径规划系统专用配置属性
 * 
 * 注意：JWT 配置已移至 common-utils 模块的 UavConfigProperties
 */
@Configuration
@ConfigurationProperties(prefix = "uav")
public class UavProperties {

    private Python python = new Python();
    private Wrf wrf = new Wrf();
    private PathPlanning pathPlanning = new PathPlanning();
    private Grpc grpc = new Grpc();
    private Demo demo = new Demo();

    public Python getPython() {
        return python;
    }

    public void setPython(Python python) {
        this.python = python;
    }

    public Wrf getWrf() {
        return wrf;
    }

    public void setWrf(Wrf wrf) {
        this.wrf = wrf;
    }

    public PathPlanning getPathPlanning() {
        return pathPlanning;
    }

    public void setPathPlanning(PathPlanning pathPlanning) {
        this.pathPlanning = pathPlanning;
    }

    public Grpc getGrpc() {
        return grpc;
    }

    public void setGrpc(Grpc grpc) {
        this.grpc = grpc;
    }

    public Demo getDemo() {
        return demo;
    }

    public void setDemo(Demo demo) {
        this.demo = demo;
    }

    public static class Python {
        private String scriptPath;
        private int timeout = 30000;

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

    public static class Wrf {
        private String dataPath;
        private int updateInterval = 300;

        public String getDataPath() {
            return dataPath;
        }

        public void setDataPath(String dataPath) {
            this.dataPath = dataPath;
        }

        public int getUpdateInterval() {
            return updateInterval;
        }

        public void setUpdateInterval(int updateInterval) {
            this.updateInterval = updateInterval;
        }
    }

    public static class PathPlanning {
        private int maxTasks = 200;
        private int maxDrones = 10;
        private double replanningThreshold = 3.0;

        public int getMaxTasks() {
            return maxTasks;
        }

        public void setMaxTasks(int maxTasks) {
            this.maxTasks = maxTasks;
        }

        public int getMaxDrones() {
            return maxDrones;
        }

        public void setMaxDrones(int maxDrones) {
            this.maxDrones = maxDrones;
        }

        public double getReplanningThreshold() {
            return replanningThreshold;
        }

        public void setReplanningThreshold(double replanningThreshold) {
            this.replanningThreshold = replanningThreshold;
        }
    }

    public static class Grpc {
        private String host = "localhost";
        private int port = 50051;

        public String getHost() {
            return host;
        }

        public void setHost(String host) {
            this.host = host;
        }

        public int getPort() {
            return port;
        }

        public void setPort(int port) {
            this.port = port;
        }
    }

    public static class Demo {
        private boolean enabled = false;
        private int maxConcurrentSessions = 100;
        private int apiRateLimit = 100;
        private int sessionDuration = 3600;
        private boolean dataIsolation = true;

        public boolean isEnabled() {
            return enabled;
        }

        public void setEnabled(boolean enabled) {
            this.enabled = enabled;
        }

        public int getMaxConcurrentSessions() {
            return maxConcurrentSessions;
        }

        public void setMaxConcurrentSessions(int maxConcurrentSessions) {
            this.maxConcurrentSessions = maxConcurrentSessions;
        }

        public int getApiRateLimit() {
            return apiRateLimit;
        }

        public void setApiRateLimit(int apiRateLimit) {
            this.apiRateLimit = apiRateLimit;
        }

        public int getSessionDuration() {
            return sessionDuration;
        }

        public void setSessionDuration(int sessionDuration) {
            this.sessionDuration = sessionDuration;
        }

        public boolean isDataIsolation() {
            return dataIsolation;
        }

        public void setDataIsolation(boolean dataIsolation) {
            this.dataIsolation = dataIsolation;
        }
    }
}
