package com.uav.common.config;

import com.alibaba.cloud.nacos.NacosConfigManager;
import com.alibaba.nacos.api.config.listener.Listener;
import com.alibaba.nacos.api.exception.NacosException;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

@Component
@ConditionalOnClass(NacosConfigManager.class)
@RefreshScope
public class NacosConfigRefresher {

    private static final Logger log = LoggerFactory.getLogger(NacosConfigRefresher.class);

    private final Map<String, Consumer<String>> listeners = new ConcurrentHashMap<>();
    private final Executor executor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "nacos-config-listener");
        t.setDaemon(true);
        return t;
    });

    @Nullable
    private final NacosConfigManager nacosConfigManager;

    @Value("${spring.cloud.nacos.config.group:DEFAULT_GROUP}")
    private String group;

    @Value("${spring.cloud.nacos.config.namespace:}")
    private String namespace;

    public NacosConfigRefresher(@Nullable NacosConfigManager nacosConfigManager) {
        this.nacosConfigManager = nacosConfigManager;
    }

    public void addListener(String dataId, Consumer<String> callback) {
        if (nacosConfigManager == null) {
            log.warn("NacosConfigManager not available, skipping listener registration for: {}", dataId);
            return;
        }
        try {
            nacosConfigManager.getConfigService().addListener(dataId, group, new Listener() {
                @Override
                public Executor getExecutor() {
                    return executor;
                }

                @Override
                public void receiveConfigInfo(String configInfo) {
                    log.info("Nacos配置更新: {} (group={})", dataId, group);
                    try {
                        callback.accept(configInfo);
                    } catch (Exception e) {
                        log.error("配置回调执行失败: {}", dataId, e);
                    }
                }
            });
            listeners.put(dataId, callback);
            log.info("已注册Nacos配置监听: {} (group={})", dataId, group);
        } catch (NacosException e) {
            log.error("注册Nacos配置监听失败: {} - {}", dataId, e.getMessage());
        }
    }

    public String getConfig(String dataId, long timeoutMs) {
        if (nacosConfigManager == null) return null;
        try {
            return nacosConfigManager.getConfigService().getConfig(dataId, group, timeoutMs);
        } catch (NacosException e) {
            log.error("获取Nacos配置失败: {} - {}", dataId, e.getMessage());
            return null;
        }
    }

    public boolean publishConfig(String dataId, String content) {
        if (nacosConfigManager == null) return false;
        try {
            return nacosConfigManager.getConfigService().publishConfig(dataId, group, content);
        } catch (NacosException e) {
            log.error("发布Nacos配置失败: {} - {}", dataId, e.getMessage());
            return false;
        }
    }

    public Map<String, Consumer<String>> getRegisteredListeners() {
        return Map.copyOf(listeners);
    }

    @PreDestroy
    public void cleanup() {
        listeners.clear();
    }
}
