package com.uav.common.security.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 标记应急特权接口
 * <p>
 * 用于标识在应急模式下可绕过部分常规权限校验的接口。
 * 需要结合 {@link com.uav.common.core.util.TenantContext#isEmergency()} 使用。
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RequireEmergency {
}
