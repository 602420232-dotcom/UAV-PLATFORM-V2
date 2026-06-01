package com.bayesian.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class MultiProtocolClient {

    private static final Logger log = LoggerFactory.getLogger(MultiProtocolClient.class);

    public String sendViaHttp(String url, String payload) {
        log.info("HTTP 发送请求至: {}", url);
        return "{\"status\":\"sent\",\"protocol\":\"http\"}";
    }

    public String sendViaGrpc(String serviceName, Object request) {
        log.info("gRPC 发送请求至: {}", serviceName);
        return "{\"status\":\"sent\",\"protocol\":\"grpc\"}";
    }
}
