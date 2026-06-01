package com.bayesian.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Component
public class PythonServiceClient {

    private static final Logger log = LoggerFactory.getLogger(PythonServiceClient.class);
    private final RestTemplate restTemplate;

    public PythonServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public String executeAssimilation(String pythonServiceUrl, Object request) {
        log.info("调用 Python 同化服务: {}", pythonServiceUrl);
        try {
            return restTemplate.postForObject(pythonServiceUrl + "/assimilate", request, String.class);
        } catch (Exception e) {
            log.error("调用 Python 服务失败: {}", e.getMessage());
            return "{\"status\":\"error\",\"message\":\"" + e.getMessage() + "\"}";
        }
    }
}
