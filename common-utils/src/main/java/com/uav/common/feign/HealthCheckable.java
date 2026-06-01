package com.uav.common.feign;

import java.util.Map;

/**
 * 健康检查接口
 * 所有需要被 PlatformController 进行健康检查的 Feign Client 都应实现此接口。
 * 
 * 使用接口替代 instanceof 链，提高可扩展性和类型安全性。
 * 新增服务时只需在对应的 Feign Client 中 implements HealthCheckable 即可。
 */
public interface HealthCheckable {

    /**
     * 执行健康检查
     * @return 健康检查结果，包含 status 等字段
     */
    Map<String, Object> health();
}
