package com.uav.assimilation.service.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "assimilation")
public class AssimilationProperties {

    private String pythonScript;
    private int timeout = 60000;
    private Algorithm algorithm = new Algorithm();

    public String getPythonScript() {
        return pythonScript;
    }

    public void setPythonScript(String pythonScript) {
        this.pythonScript = pythonScript;
    }

    public int getTimeout() {
        return timeout;
    }

    public void setTimeout(int timeout) {
        this.timeout = timeout;
    }

    public Algorithm getAlgorithm() {
        return algorithm;
    }

    public void setAlgorithm(Algorithm algorithm) {
        this.algorithm = algorithm;
    }

    public static class Algorithm {
        private double backgroundError = 0.1;
        private double observationError = 0.05;
        private int maxIterations = 100;

        public double getBackgroundError() {
            return backgroundError;
        }

        public void setBackgroundError(double backgroundError) {
            this.backgroundError = backgroundError;
        }

        public double getObservationError() {
            return observationError;
        }

        public void setObservationError(double observationError) {
            this.observationError = observationError;
        }

        public int getMaxIterations() {
            return maxIterations;
        }

        public void setMaxIterations(int maxIterations) {
            this.maxIterations = maxIterations;
        }
    }
}