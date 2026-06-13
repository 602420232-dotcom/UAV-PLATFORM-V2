package com.uav.common.core.aspect;

import com.uav.common.core.annotation.Idempotent;
import com.uav.common.core.exception.BizException;
import com.uav.common.core.result.ResultCode;
import com.uav.common.core.util.IdempotentKeyGenerator;
import com.uav.common.core.util.TenantContext;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.util.concurrent.TimeUnit;

/**
 * 幂等控制切面
 * <p>
 * 拦截标注了 {@link Idempotent} 注解的方法，基于 Redis 实现请求幂等校验。
 * <ul>
 *   <li>请求到达时生成幂等 Key，检查 Redis 中是否已存在</li>
 *   <li>已存在则拒绝重复请求</li>
 *   <li>不存在则设置 Key（带 TTL），执行方法</li>
 *   <li>方法执行成功后更新 Key 状态</li>
 * </ul>
 */
@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class IdempotentAspect {

    private final StringRedisTemplate redisTemplate;

    @Around("@annotation(idempotent)")
    public Object around(ProceedingJoinPoint joinPoint, Idempotent idempotent) throws Throwable {
        // 获取当前请求信息
        ServletRequestAttributes attributes =
                (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attributes == null) {
            // 非 Web 请求环境，直接放行
            return joinPoint.proceed();
        }

        HttpServletRequest request = attributes.getRequest();
        String apiPath = request.getRequestURI();
        String tenantId = TenantContext.getTenantId() != null ? TenantContext.getTenantId() : "default";

        // 获取请求参数（取第一个参数作为幂等依据）
        Object[] args = joinPoint.getArgs();
        Object params = (args != null && args.length > 0) ? args[0] : new Object();

        // 生成幂等 Key
        String idempotentKey = IdempotentKeyGenerator.generate(tenantId, apiPath, params);
        String processingKey = idempotentKey + ":processing";

        log.debug("幂等校验, key={}", idempotentKey);

        // 检查是否已有处理完成的请求
        Boolean hasKey = redisTemplate.hasKey(idempotentKey);
        if (Boolean.TRUE.equals(hasKey)) {
            String status = redisTemplate.opsForValue().get(idempotentKey);
            if ("done".equals(status)) {
                log.warn("重复请求被拒绝, key={}", idempotentKey);
                throw new BizException(ResultCode.TOO_MANY_REQUESTS, idempotent.message());
            }
        }

        // 检查是否有正在处理中的请求
        Boolean isProcessing = redisTemplate.hasKey(processingKey);
        if (Boolean.TRUE.equals(isProcessing)) {
            log.warn("请求正在处理中，拒绝重复提交, key={}", idempotentKey);
            throw new BizException(ResultCode.TOO_MANY_REQUESTS, idempotent.message());
        }

        // 标记为处理中（短 TTL 防止死锁）
        redisTemplate.opsForValue().set(processingKey, "1",
                Math.min(idempotent.ttlSeconds(), 300), TimeUnit.SECONDS);

        try {
            // 执行目标方法
            Object result = joinPoint.proceed();

            // 方法执行成功，标记幂等 Key 为已完成
            redisTemplate.opsForValue().set(idempotentKey, "done",
                    idempotent.ttlSeconds(), TimeUnit.SECONDS);
            redisTemplate.delete(processingKey);

            return result;
        } catch (Throwable ex) {
            // 方法执行失败，删除处理中标记，允许重试
            redisTemplate.delete(processingKey);
            throw ex;
        }
    }
}
