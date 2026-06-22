package com.uav.common.web.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.ssl.SslContext;
import io.netty.handler.ssl.SslContextBuilder;
import io.netty.handler.ssl.util.InsecureTrustManagerFactory;
import lombok.extern.slf4j.Slf4j;
import org.apache.hc.client5.http.config.ConnectionConfig;
import org.apache.hc.client5.http.config.RequestConfig;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManagerBuilder;
import org.apache.hc.client5.http.io.HttpClientConnectionManager;
import org.apache.hc.client5.http.ssl.DefaultClientTlsStrategy;
import org.apache.hc.core5.util.Timeout;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.ssl.SslBundle;
import org.springframework.boot.ssl.SslBundles;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.reactive.function.client.WebClient;

import java.security.cert.X509Certificate;
import java.time.Duration;

/**
 * RestClient SSL 配置类
 * 使用 Spring Boot 4.1.0 的 SSL Bundle 功能配置服务间 mTLS
 * 支持 RestTemplate 和 WebClient 的 SSL 上下文配置
 */
@Slf4j
@Configuration
@ConditionalOnProperty(name = "spring.ssl.bundle.pem.client.keystore.certificate", matchIfMissing = false)
public class RestClientSslConfig {

    @Value("${MTLS_ENABLED:false}")
    private boolean mTlsEnabled;

    private static final String SSL_BUNDLE_NAME = "client";
    private static final int CONNECT_TIMEOUT_MS = 10000;
    private static final int READ_TIMEOUT_MS = 30000;

    /**
     * 配置基于 SSL Bundle 的 RestTemplate（用于同步 HTTP 调用）
     * 当 mTLS 启用时，使用 SSL Bundle 配置客户端证书
     */
    @Bean
    @Primary
    @ConditionalOnProperty(name = "MTLS_ENABLED", havingValue = "true")
    public RestTemplate mTlsRestTemplate(SslBundles sslBundles) {
        SslBundle sslBundle = sslBundles.getBundle(SSL_BUNDLE_NAME);
        javax.net.ssl.SSLContext sslContext = sslBundle.createSslContext();

        ConnectionConfig connConfig = ConnectionConfig.custom()
                .setConnectTimeout(Timeout.ofMilliseconds(CONNECT_TIMEOUT_MS))
                .setSocketTimeout(Timeout.ofMilliseconds(READ_TIMEOUT_MS))
                .build();

        HttpClientConnectionManager cm = PoolingHttpClientConnectionManagerBuilder.create()
                .setTlsSocketStrategy(new DefaultClientTlsStrategy(sslContext))
                .setDefaultConnectionConfig(connConfig)
                .build();

        RequestConfig requestConfig = RequestConfig.custom()
                .setResponseTimeout(Timeout.ofMilliseconds(READ_TIMEOUT_MS))
                .build();

        org.springframework.http.client.HttpComponentsClientHttpRequestFactory factory =
                new org.springframework.http.client.HttpComponentsClientHttpRequestFactory(
                        HttpClients.custom()
                                .setConnectionManager(cm)
                                .setDefaultRequestConfig(requestConfig)
                                .build());

        log.info("mTLS RestTemplate configured with SSL Bundle: {}", SSL_BUNDLE_NAME);
        return new RestTemplate(factory);
    }

    /**
     * 默认 RestTemplate（mTLS 未启用时）
     */
    @Bean
    @Primary
    @ConditionalOnProperty(name = "MTLS_ENABLED", havingValue = "false", matchIfMissing = true)
    public RestTemplate defaultRestTemplate() {
        ConnectionConfig connConfig = ConnectionConfig.custom()
                .setConnectTimeout(Timeout.ofMilliseconds(CONNECT_TIMEOUT_MS))
                .setSocketTimeout(Timeout.ofMilliseconds(READ_TIMEOUT_MS))
                .build();

        HttpClientConnectionManager cm = PoolingHttpClientConnectionManagerBuilder.create()
                .setDefaultConnectionConfig(connConfig)
                .build();

        RequestConfig requestConfig = RequestConfig.custom()
                .setResponseTimeout(Timeout.ofMilliseconds(READ_TIMEOUT_MS))
                .build();

        org.springframework.http.client.HttpComponentsClientHttpRequestFactory factory =
                new org.springframework.http.client.HttpComponentsClientHttpRequestFactory(
                        HttpClients.custom()
                                .setConnectionManager(cm)
                                .setDefaultRequestConfig(requestConfig)
                                .build());
        return new RestTemplate(factory);
    }

    /**
     * 配置基于 SSL Bundle 的 WebClient（用于异步 HTTP 调用）
     * 当 mTLS 启用时，使用 Netty Reactor 配置客户端证书
     */
    @Bean
    @Primary
    @ConditionalOnProperty(name = "MTLS_ENABLED", havingValue = "true")
    public WebClient mTlsWebClient(SslBundles sslBundles) {
        try {
            SslBundle sslBundle = sslBundles.getBundle(SSL_BUNDLE_NAME);

            SslContextBuilder sslContextBuilder = SslContextBuilder.forClient();
            javax.net.ssl.KeyManager[] keyManagers = sslBundle.getManagers().getKeyManagers();
            javax.net.ssl.TrustManager[] trustManagers = sslBundle.getManagers().getTrustManagers();

            sslContextBuilder.keyManager(keyManagers[0]);
            if (trustManagers != null && trustManagers.length > 0) {
                sslContextBuilder.trustManager((X509Certificate) trustManagers[0]);
            }

            SslContext sslContext = sslContextBuilder.build();

            WebClient webClient = WebClient.builder()
                    .clientConnector(new ReactorClientHttpConnector(
                            reactor.netty.http.client.HttpClient.create()
                                    .secure(spec -> spec.sslContext(sslContext))
                                    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, CONNECT_TIMEOUT_MS)
                                    .responseTimeout(Duration.ofMillis(READ_TIMEOUT_MS))))
                    .build();

            log.info("mTLS WebClient configured with SSL Bundle: {}", SSL_BUNDLE_NAME);
            return webClient;
        } catch (javax.net.ssl.SSLException e) {
            log.error("Failed to create mTLS WebClient SSL context", e);
            throw new RuntimeException("Failed to create mTLS WebClient", e);
        }
    }

    /**
     * 默认 WebClient（mTLS 未启用时）
     */
    @Bean
    @Primary
    @ConditionalOnProperty(name = "MTLS_ENABLED", havingValue = "false", matchIfMissing = true)
    public WebClient defaultWebClient() {
        return WebClient.builder()
                .clientConnector(new ReactorClientHttpConnector(
                        reactor.netty.http.client.HttpClient.create()
                                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, CONNECT_TIMEOUT_MS)
                                .responseTimeout(Duration.ofMillis(READ_TIMEOUT_MS))))
                .build();
    }

    /**
     * 开发环境专用：禁用证书验证的 WebClient（仅用于本地开发/测试）
     * 需要显式启用：MTLS_DEV_MODE=true
     */
    @Bean("devWebClient")
    @ConditionalOnProperty(name = "MTLS_DEV_MODE", havingValue = "true")
    public WebClient devWebClient() {
        try {
            SslContext sslContext = SslContextBuilder.forClient()
                    .trustManager(InsecureTrustManagerFactory.INSTANCE)
                    .build();

            log.warn("Development WebClient created with INSECURE trust manager - DO NOT USE IN PRODUCTION");
            return WebClient.builder()
                    .clientConnector(new ReactorClientHttpConnector(
                            reactor.netty.http.client.HttpClient.create()
                                    .secure(spec -> spec.sslContext(sslContext))
                                    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, CONNECT_TIMEOUT_MS)
                                    .responseTimeout(Duration.ofMillis(READ_TIMEOUT_MS))))
                    .build();
        } catch (Exception e) {
            log.error("Failed to create dev WebClient", e);
            throw new RuntimeException("Failed to create dev WebClient", e);
        }
    }
}
