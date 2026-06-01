package com.uav.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "uav.demo")
public class DemoProperties {

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
