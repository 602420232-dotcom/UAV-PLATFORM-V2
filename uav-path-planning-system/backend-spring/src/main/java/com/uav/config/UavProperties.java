package com.uav.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "uav")
public class UavProperties {

    private Python python = new Python();
    private Wrf wrf = new Wrf();
    private PathPlanning pathPlanning = new PathPlanning();
    private Grpc grpc = new Grpc();

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

    public static class Python {
        private static final String USER_DIR = System.getProperty("user.dir");
        private String scriptPath = USER_DIR + "/algorithm-core";
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
        private static final String USER_DIR = System.getProperty("user.dir");
        private String dataPath = USER_DIR + "/data/wrf";
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
}