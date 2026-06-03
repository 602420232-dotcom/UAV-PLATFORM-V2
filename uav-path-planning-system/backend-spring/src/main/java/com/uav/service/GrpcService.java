package com.uav.service;

import com.uav.utils.GrpcClientUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.CompletableFuture;

@Slf4j
@Service
public class GrpcService {

    private final GrpcClientUtil grpcClientUtil;

    public GrpcService(GrpcClientUtil grpcClientUtil) {
        this.grpcClientUtil = grpcClientUtil;
    }

    /**
     * 检查 gRPC 连接是否可用
     */
    public boolean isGrpcAvailable() {
        if (!grpcClientUtil.isChannelAvailable()) {
            log.warn("gRPC channel is not available, attempting to reinitialize");
            grpcClientUtil.reinitialize();
            if (!grpcClientUtil.isChannelAvailable()) {
                return false;
            }
        }

        try {
            // 通过通道连通性验证服务可用性
            boolean available = grpcClientUtil.isChannelAvailable();
            log.info("gRPC service available: {}", available);
            return available;
        } catch (Exception e) {
            log.error("gRPC service is not available: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 通过 gRPC 调用数据同化服务
     *
     * @param params 同化请求参数
     * @return 同化结果 Map
     */
    public Map<String, Object> performAssimilation(Map<String, Object> params) {
        log.info("Performing assimilation via gRPC with params keys: {}", params.keySet());

        if (!grpcClientUtil.isChannelAvailable()) {
            log.warn("gRPC channel unavailable, attempting reinitialize before assimilation call");
            grpcClientUtil.reinitialize();
        }

        return grpcClientUtil.callAssimilationService(params);
    }

    /**
     * 异步检查 gRPC 连接健康状态
     * <p>
     * 在后台线程中执行健康检查，不阻塞调用方。
     * 检查结果将通过日志输出。
     */
    public void checkConnectionAsync() {
        CompletableFuture.runAsync(() -> {
            log.info("Starting async gRPC connection health check");
            long startTime = System.currentTimeMillis();

            try {
                boolean available = isGrpcAvailable();
                long elapsed = System.currentTimeMillis() - startTime;

                if (available) {
                    log.info("Async gRPC health check passed in {}ms", elapsed);
                } else {
                    log.warn("Async gRPC health check failed in {}ms", elapsed);
                }
            } catch (Exception e) {
                log.error("Async gRPC health check encountered an error", e);
            }
        }).exceptionally(throwable -> {
            log.error("Async gRPC health check failed with unhandled exception", throwable);
            return null;
        });

        log.debug("Async gRPC health check task submitted");
    }
}
