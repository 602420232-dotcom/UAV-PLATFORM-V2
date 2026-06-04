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
    private Cma cma = new Cma();
    private Owm owm = new Owm();
    private Ecmwf ecmwf = new Ecmwf();

    public Collection getCollection() {
        return collection;
    }

    public void setCollection(Collection collection) {
        this.collection = collection;
    }

    public Cma getCma() {
        return cma;
    }

    public void setCma(Cma cma) {
        this.cma = cma;
    }

    public Owm getOwm() {
        return owm;
    }

    public void setOwm(Owm owm) {
        this.owm = owm;
    }

    public Ecmwf getEcmwf() {
        return ecmwf;
    }

    public void setEcmwf(Ecmwf ecmwf) {
        this.ecmwf = ecmwf;
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

    public static class Cma {
        private String apiKey = "";
        private String baseUrl = "https://api.weather.cma.cn/api";

        public String getApiKey() {
            return apiKey;
        }

        public void setApiKey(String apiKey) {
            this.apiKey = apiKey;
        }

        public String getBaseUrl() {
            return baseUrl;
        }

        public void setBaseUrl(String baseUrl) {
            this.baseUrl = baseUrl;
        }
    }

    public static class Owm {
        private String apiKey = "";
        private String baseUrl = "https://api.openweathermap.org/data/2.5";

        public String getApiKey() {
            return apiKey;
        }

        public void setApiKey(String apiKey) {
            this.apiKey = apiKey;
        }

        public String getBaseUrl() {
            return baseUrl;
        }

        public void setBaseUrl(String baseUrl) {
            this.baseUrl = baseUrl;
        }
    }

    public static class Ecmwf {
        private String apiKey = "";
        private String baseUrl = "https://api.ecmwf.int/v1";

        public String getApiKey() {
            return apiKey;
        }

        public void setApiKey(String apiKey) {
            this.apiKey = apiKey;
        }

        public String getBaseUrl() {
            return baseUrl;
        }

        public void setBaseUrl(String baseUrl) {
            this.baseUrl = baseUrl;
        }
    }
}
