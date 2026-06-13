package com.uav.sdk.auth;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;

/**
 * HMAC-SHA256 签名工具
 * <p>
 * 用于对 API 请求进行签名认证，与平台服务端的签名算法一致。
 */
public final class SignatureUtil {

    private static final String HMAC_ALGORITHM = "HmacSHA256";

    private SignatureUtil() {}

    /**
     * 生成 HMAC-SHA256 签名
     *
     * @param data      待签名数据
     * @param secretKey 密钥
     * @return Base64 编码的签名
     */
    public static String sign(String data, String secretKey) {
        try {
            Mac mac = Mac.getInstance(HMAC_ALGORITHM);
            SecretKeySpec secretKeySpec = new SecretKeySpec(
                    secretKey.getBytes(StandardCharsets.UTF_8), HMAC_ALGORITHM);
            mac.init(secretKeySpec);
            byte[] bytes = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(bytes);
        } catch (Exception e) {
            throw new RuntimeException("HMAC-SHA256 签名失败", e);
        }
    }

    /**
     * 构建签名字符串
     *
     * @param method    HTTP 方法
     * @param path      请求路径
     * @param timestamp 时间戳
     * @param apiKey    API Key
     * @param body      请求体（可为空）
     * @return 签名原文
     */
    public static String buildSignString(String method, String path,
                                          String timestamp, String apiKey, String body) {
        return String.join("\n",
                method.toUpperCase(),
                path,
                timestamp,
                apiKey,
                body != null ? body : "");
    }

    /**
     * 验证签名
     *
     * @param data      原始数据
     * @param secretKey 密钥
     * @param signature 待验证的签名
     * @return 是否匹配
     */
    public static boolean verify(String data, String secretKey, String signature) {
        String expected = sign(data, secretKey);
        return MessageDigest.isEqual(
                signature.getBytes(StandardCharsets.UTF_8),
                expected.getBytes(StandardCharsets.UTF_8));
    }
}
