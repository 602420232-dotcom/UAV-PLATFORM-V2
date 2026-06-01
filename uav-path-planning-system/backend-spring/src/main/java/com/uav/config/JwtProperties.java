package com.uav.config;

import jakarta.annotation.PostConstruct;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {

    private String secret;
    private String refreshSecret;
    private long accessExpiration = 7200;
    private long refreshExpiration = 2592000;
    private String issuer = "uav-platform";
    private boolean enabled = true;

    @PostConstruct
    public void validate() {
        if (enabled) {
            if (secret == null || secret.isEmpty()) {
                String envSecret = System.getenv("JWT_SECRET");
                if (envSecret != null && !envSecret.isEmpty()) {
                    secret = envSecret;
                } else {
                    throw new IllegalStateException(
                        "JWT密钥未配置。请设置环境变量 JWT_SECRET 或配置项 jwt.secret。"
                        + "可以使用: openssl rand -base64 64 生成安全密钥");
                }
            }
            if (refreshSecret == null || refreshSecret.isEmpty()) {
                String envRefreshSecret = System.getenv("JWT_REFRESH_SECRET");
                if (envRefreshSecret != null && !envRefreshSecret.isEmpty()) {
                    refreshSecret = envRefreshSecret;
                } else {
                    throw new IllegalStateException(
                        "JWT刷新密钥未配置。请设置环境变量 JWT_REFRESH_SECRET 或配置项 jwt.refresh-secret。"
                        + "可以使用: openssl rand -base64 64 生成安全密钥");
                }
            }
        }
    }
}
