package com.uav.utils;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.util.concurrent.TimeUnit;

@Slf4j
@Component
public class GrpcClientUtil {
    
    @Value("${uav.grpc.host}")
    private String grpcHost;
    
    @Value("${uav.grpc.port}")
    private int grpcPort;
    
    private ManagedChannel channel;
    
    @PostConstruct
    public void init() {
        try {
            // 创建gRPC通道
            channel = ManagedChannelBuilder.forAddress(grpcHost, grpcPort)
                    .usePlaintext() // 生产环境应使用TLS
                    .build();
            log.info("gRPC通道初始化成功: {}:{}", grpcHost, grpcPort);
        } catch (Exception e) {
            log.error("gRPC通道初始化失败", e);
        }
    }
    
    /**
     * 获取gRPC通道
     * @return gRPC通道
     */
    public ManagedChannel getChannel() {
        return channel;
    }
    
    /**
     * 关闭gRPC通道
     */
    @PreDestroy
    public void shutdown() {
        if (channel != null) {
            try {
                channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
                log.info("gRPC通道已关闭");
            } catch (InterruptedException e) {
                log.error("关闭gRPC通道时发生错误", e);
                Thread.currentThread().interrupt();
            }
        }
    }
}