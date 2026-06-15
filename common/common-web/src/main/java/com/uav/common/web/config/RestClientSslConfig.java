package com.uav.common.web.config;

import io.netty.handler.ssl.SslContext;
import io.netty.handler.ssl.SslContextBuilder;
import io.netty.handler.ssl.util.InsecureTrustManagerFactory;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.ssl.SslBundle;
import org.springframework.boot.ssl.SslBundles;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.reactive.function.client.WebClient;

import javax.net.ssl.KeyManager;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import java.io.FileInputStream;
import java.security.KeyStore;
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

    @Value("${MTLS_CLIENT_CERT:classpath:client-cert.pem}")
    private String clientCertPath;

    @Value("${MTLS_CLIENT_KEY:classpath:client-key.pem}")
    private String clientKeyPath;

    @Value("${MTLS_TRUST_CERT:classpath:truststore.pem}")
    private String trustCertPath;

    @Value("${MTLS_KEYSTORE:classpath:client-keystore.jks}")
    private String keystorePath;

    @Value("${MTLS_KEYSTORE_PASSWORD:}")
    private String keystorePassword;

    @Value("${MTLS_TRUSTSTORE:classpath:client-truststore.jks}")
    private String truststorePath;

    @Value("${MTLS_TRUSTSTORE_PASSWORD:}")
    private String truststorePassword;

    @Value("${MTLS_VERIFY_HOSTNAME:true}")
    private boolean verifyHostname;

    @Value("${MTLS_ENABLED:false}")
    private boolean mTlsEnabled;

    private static final String SSL_BUNDLE_NAME = "client";
    private static final Duration CONNECT_TIMEOUT = Duration.ofSeconds(10);
    private static final Duration READ_TIMEOUT = Duration.ofSeconds(30);

    /**
     * 配置基于 SSL Bundle 的 RestTemplate（用于同步 HTTP 调用）
     * 当 mTLS 启用时，使用 SSL Bundle 配置客户端证书
     */
    @Bean
    @Primary
    @ConditionalOnProperty(name = "MTLS_ENABLED", havingValue = "true")
    public RestTemplate mTlsRestTemplate(SslBundles sslBundles) {
        try {
            SslBundle sslBundle = sslBundles.getBundle(SSL_BUNDLE_NAME);
            SSLContext sslContext = sslBundle.createSslContext();

            HttpComponentsClientHttpRequestFactory factory = new HttpComponentsClientHttpRequestFactory();
            // 使用 Apache HttpClient 5 配置 SSL
            org.apache.hc.client5.http.impl.classic.HttpClientBuilder clientBuilder =
                    org.apache.hc.client5.http.impl.classic.HttpClientBuilder.create();

            clientBuilder.setConnectionManager(
                    org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManagerBuilder.create()
                            .setSSLSocketFactory(
                                    org.apache.hc.client5.http.ssl.SSLConnectionSocketFactoryBuilder.create()
                                            .setSslContext(sslContext)
                                            .setHostnameVerifier(verifyHostname ?
                                                    org.apache.hc.client5.http.ssl.DefaultHostnameVerifier.INSTANCE :
                                                    org.apache.hc.client5.http.ssl.NoopHostnameVerifier.INSTANCE)
                                            .build()
                            )
                            .build()
            );

            factory.setHttpClient(clientBuilder.build());
            factory.setConnectTimeout(CONNECT_TIMEOUT);
            factory.setReadTimeout(READ_TIMEOUT);

            log.info("mTLS RestTemplate configured with SSL Bundle: {}", SSL_BUNDLE_NAME);
            return new RestTemplate(factory);
        } catch (Exception e) {
            log.error("Failed to create mTLS RestTemplate", e);
            throw new RuntimeException("Failed to create mTLS RestTemplate", e);
        }
    }

    /**
     * 默认 RestTemplate（mTLS 未启用时）
     */
    @Bean
    @Primary
    @ConditionalOnProperty(name = "MTLS_ENABLED", havingValue = "false", matchIfMissing = true)
    public RestTemplate defaultRestTemplate() {
        HttpComponentsClientHttpRequestFactory factory = new HttpComponentsClientHttpRequestFactory();
        factory.setConnectTimeout(CONNECT_TIMEOUT);
        factory.setReadTimeout(READ_TIMEOUT);
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
            javax.net.ssl.SSLParameters sslParameters = sslBundle.createSslContext().getDefaultSSLParameters();

            // 使用 Netty SslContext 配置 mTLS
            SslContextBuilder sslContextBuilder = SslContextBuilder.forClient();
            KeyManager[] keyManagers = sslBundle.getManagers().getKeyManagers();
            TrustManager[] trustManagers = sslBundle.getManagers().getTrustManagers();

            sslContextBuilder.keyManager(keyManagers[0]);
            if (trustManagers != null && trustManagers.length > 0) {
                sslContextBuilder.trustManager(trustManagers);
            }

            SslContext sslContext = sslContextBuilder.build();

            reactor.netty.http.client.HttpClient httpClient = reactor.netty.http.client.HttpClient.create()
                    .secure(spec -> spec.sslContext(sslContext))
                    .responseTimeout(READ_TIMEOUT)
                    .option(reactor.netty.transport.ProxyProvider.CONNECT_TIMEOUT_MILLIS, (int) CONNECT_TIMEOUT.toMillis());

            WebClient webClient = WebClient.builder()
                    .clientConnector(new ReactorClientHttpConnector(httpClient))
                    .build();

            log.info("mTLS WebClient configured with SSL Bundle: {}", SSL_BUNDLE_NAME);
            return webClient;
        } catch (Exception e) {
            log.error("Failed to create mTLS WebClient", e);
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
        reactor.netty.http.client.HttpClient httpClient = reactor.netty.http.client.HttpClient.create()
                .responseTimeout(READ_TIMEOUT)
                .option(reactor.netty.transport.ProxyProvider.CONNECT_TIMEOUT_MILLIS, (int) CONNECT_TIMEOUT.toMillis());

        return WebClient.builder()
                .clientConnector(new ReactorClientHttpConnector(httpClient))
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

            reactor.netty.http.client.HttpClient httpClient = reactor.netty.http.client.HttpClient.create()
                    .secure(spec -> spec.sslContext(sslContext))
                    .responseTimeout(READ_TIMEOUT)
                    .option(reactor.netty.transport.ProxyProvider.CONNECT_TIMEOUT_MILLIS, (int) CONNECT_TIMEOUT.toMillis());

            log.warn("Development WebClient created with INSECURE trust manager - DO NOT USE IN PRODUCTION");
            return WebClient.builder()
                    .clientConnector(new ReactorClientHttpConnector(httpClient))
                    .build();
        } catch (Exception e) {
            log.error("Failed to create dev WebClient", e);
            throw new RuntimeException("Failed to create dev WebClient", e);
        }
    }

    /**
     * 手动加载 JKS 格式的 KeyStore（用于传统 JKS 配置场景）
     */
    private KeyStore loadKeyStore(String path, String password, String type) throws Exception {
        KeyStore keyStore = KeyStore.getInstance(type != null ? type : "JKS");
        try (FileInputStream fis = new FileInputStream(path)) {
            keyStore.load(fis, password != null ? password.toCharArray() : null);
        }
        return keyStore;
    }
}
