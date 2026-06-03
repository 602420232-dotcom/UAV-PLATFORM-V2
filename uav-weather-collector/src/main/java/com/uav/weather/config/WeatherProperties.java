package com.uav.weather.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 天气采集服务配置属性
 */
@Configuration
@ConfigurationProperties(prefix = "weather")
public class WeatherProperties {

    private Collection collection = new Collection();

    public Collection getCollection() {
        return collection;
    }

    public void setCollection(Collection collection) {
        this.collection = collection;
    }

    public static class Collection {
        private long wrfInterval = 1800000;
        private long groundInterval = 300000;
        private long fusionInterval = 900000;
        private long riskInterval = 600000;

        public long getWrfInterval() {
            return wrfInterval;
        }

        public void setWrfInterval(long wrfInterval) {
            this.wrfInterval = wrfInterval;
        }

        public long getGroundInterval() {
            return groundInterval;
        }

        public void setGroundInterval(long groundInterval) {
            this.groundInterval = groundInterval;
        }

        public long getFusionInterval() {
            return fusionInterval;
        }

        public void setFusionInterval(long fusionInterval) {
            this.fusionInterval = fusionInterval;
        }

        public long getRiskInterval() {
            return riskInterval;
        }

        public void setRiskInterval(long riskInterval) {
            this.riskInterval = riskInterval;
        }
    }
}
