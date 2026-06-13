package com.uav.common.security.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 标记需要 API Key 认证的接口
 * <p>
 * 加在 Controller 方法上，表示该接口必须通过 HMAC 签名验证（API Key + Secret）。
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RequireApiKey {
}
