package com.uav.platform.config;

import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.uav.platform.interceptor.TenantLineInnerInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MybatisPlusConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor(TenantLineInnerInterceptor tenantLineInnerInterceptor) {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(tenantLineInnerInterceptor);
        return interceptor;
    }
}
