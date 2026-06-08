package com.uav.common.security;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * JWT 配置属性类
 */
@Data
@Component
@ConfigurationProperties(prefix = "uav.jwt")
public class JwtProperties {

    /**
     * JWT 密钥
     */
    private String secret;

    /**
     * 是否启用 JWT
     */
    private boolean enabled = true;

    /**
     * Access Token 过期时间（毫秒）
     */
    private long expirationMs = 7200000; // 2小时

    /**
     * Refresh Token 过期时间（毫秒）
     */
    private long refreshExpirationMs = 2592000000L; // 30天

    /**
     * Token 签发者
     */
    private String issuer = "uav-platform";

    /**
     * Token 前缀
     */
    private String tokenPrefix = "Bearer ";

    /**
     * HTTP Header 名称
     */
    private String header = "Authorization";
}
