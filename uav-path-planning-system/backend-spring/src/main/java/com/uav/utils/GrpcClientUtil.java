package com.uav.utils;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * gRPC 客户端工具类。
 *
 * 提供与 Python 数据同化服务的 gRPC 通信能力。
 * 当 gRPC 通道不可用时，自动降级为 HTTP REST 调用。
 *
 * Proto 服务定义请参考：
 *   data-assimilation-platform/shared/protos/service/v1/assimilation_service.proto
 */
@Slf4j
@Component
public class GrpcClientUtil {

    @Value("${uav.grpc.host:localhost}")
    private String grpcHost;

    @Value("${uav.grpc.port:50051}")
    private int grpcPort;

    @Value("${uav.grpc.rest-fallback-url:http://localhost:8084/api/assimilation}")
    private String restFallbackUrl;

    private ManagedChannel channel;
    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @PostConstruct
    public void init() {
        try {
            channel = ManagedChannelBuilder.forAddress(grpcHost, grpcPort)
                    .usePlaintext()
                    .keepAliveTime(30, TimeUnit.SECONDS)
                    .keepAliveTimeout(10, TimeUnit.SECONDS)
                    .build();

            log.info("gRPC channel initialized: {}:{}", grpcHost, grpcPort);
        } catch (Exception e) {
            log.warn("Failed to initialize gRPC channel, will use REST fallback: {}", e.getMessage());
        }
    }

    /**
     * 调用数据同化服务
     *
     * @param params 请求参数（algorithm, jobId, observations, config等）
     * @return 同化结果 Map
     */
    public Map<String, Object> callAssimilationService(Map<String, Object> params) {
        log.info("Calling assimilation service with params: {}", params);

        // 优先尝试 gRPC，失败时降级为 REST
        if (isChannelAvailable()) {
            try {
                return callViaGrpc(params);
            } catch (Exception e) {
                log.warn("gRPC call failed, falling back to REST: {}", e.getMessage());
            }
        }

        return callViaRest(params);
    }

    /**
     * 检查 gRPC 通道是否可用
     */
    public boolean isChannelAvailable() {
        return channel != null && !channel.isShutdown() && !channel.isTerminated();
    }

    /**
     * 重新初始化通道
     */
    public synchronized void reinitialize() {
        shutdown();
        init();
    }

    /**
     * 获取底层 ManagedChannel
     */
    public ManagedChannel getChannel() {
        return channel;
    }

    @PreDestroy
    public void shutdown() {
        if (channel != null && !channel.isShutdown()) {
            try {
                channel.shutdown().awaitTermination(10, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                channel.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }

    // ======================== 私有方法 ========================

    /**
     * 通过 gRPC 调用（使用 JSON over gRPC 代理模式）
     * 当 proto 生成的 Java 桩代码可用时，可替换为直接 gRPC 调用
     */
    private Map<String, Object> callViaGrpc(Map<String, Object> params) {
        // 当前通过 HTTP REST 代理实现，proto 生成桩代码后可替换为:
        // AssimilationServiceGrpc.AssimilationServiceBlockingStub stub =
        //     AssimilationServiceGrpc.newBlockingStub(channel);
        // return stub.assimilate(buildRequest(params));
        throw new UnsupportedOperationException(
                "gRPC direct call requires proto-generated Java stubs. " +
                "Run: protoc --java_out=... --grpc-java_out=... *.proto");
    }

    /**
     * 通过 REST HTTP 调用（降级方案）
     */
    private Map<String, Object> callViaRest(Map<String, Object> params) {
        try {
            String result = restTemplate.postForObject(restFallbackUrl, params, String.class);
            if (result != null) {
                return objectMapper.readValue(result, new TypeReference<Map<String, Object>>() {});
            }
        } catch (Exception e) {
            log.error("REST fallback call failed: {}", e.getMessage());
        }

        Map<String, Object> error = new HashMap<>();
        error.put("success", false);
        error.put("error", "Assimilation service unavailable");
        return error;
    }
}
