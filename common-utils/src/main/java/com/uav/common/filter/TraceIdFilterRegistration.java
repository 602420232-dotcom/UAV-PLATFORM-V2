package com.uav.common.filter;

import jakarta.servlet.Filter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnWebApplication;
import org.springframework.boot.autoconfigure.condition.ConditionalOnWebApplication.Type;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;

/**
 * 自动注册 TraceIdFilter（仅在Servlet环境下生效）
 * Reactive环境（如API Gateway）不受影响
 */
@AutoConfiguration
@ConditionalOnClass(name = "jakarta.servlet.Filter")
@ConditionalOnWebApplication(type = Type.SERVLET)
public class TraceIdFilterRegistration {

    @Bean
    public FilterRegistrationBean<Filter> traceIdFilter(TraceIdFilter traceIdFilter) {
        FilterRegistrationBean<Filter> bean = new FilterRegistrationBean<>();
        bean.setFilter((request, response, chain) -> {
            HttpServletRequest httpRequest = (HttpServletRequest) request;
            HttpServletResponse httpResponse = (HttpServletResponse) response;

            String traceId = traceIdFilter.resolveTraceId(httpRequest.getHeader(traceIdFilter.getTraceIdHeader()));
            traceIdFilter.setupMdc(traceId);
            httpResponse.setHeader(traceIdFilter.getTraceIdHeader(), traceId);

            try {
                chain.doFilter(request, response);
            } finally {
                traceIdFilter.cleanup();
            }
        });
        bean.setOrder(Integer.MIN_VALUE);
        bean.addUrlPatterns("/*");
        return bean;
    }
}
