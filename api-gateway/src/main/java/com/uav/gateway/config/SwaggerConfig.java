package com.uav.gateway.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.cloud.gateway.route.RouteDefinitionLocator;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import springfox.documentation.swagger.web.SwaggerResourcesProvider;
import springfox.documentation.swagger.web.SwaggerResource;
import springfox.documentation.swagger2.annotations.EnableSwagger2WebFlux;

import java.util.ArrayList;
import java.util.List;

/**
 * API Gateway Swagger聚合配置
 * 统一汇总所有微服务的OpenAPI文档
 */
@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("UAV Path Planning System API")
                        .version("2.2.0")
                        .description("无人机低空作业管理系统 - API网关统一接口文档\n\n" +
                                "包含以下微服务API：\n" +
                                "- UAV Platform (8080)\n" +
                                "- WRF Processor (8081)\n" +
                                "- Meteor Forecast (8082)\n" +
                                "- Path Planning (8083)\n" +
                                "- Data Assimilation (8084)\n" +
                                "- Weather Collector (8086)\n")
                        .license(new License()
                                .name("Apache 2.0")
                                .url("https://www.apache.org/licenses/LICENSE-2.0")))
                .addServersItem(new Server()
                        .url("/")
                        .description("API Gateway"));
    }

    /**
     * 聚合各个微服务的Swagger资源
     */
    @Bean
    @Primary
    public SwaggerResourcesProvider swaggerResourcesProvider(
            RouteDefinitionLocator routeLocator) {
        return () -> {
            List<SwaggerResource> resources = new ArrayList<>();
            
            // 手动注册各服务路由
            resources.add(createSwaggerResource("uav-platform", "/api/platform/v3/api-docs", "2.0"));
            resources.add(createSwaggerResource("wrf-processor", "/api/wrf/v3/api-docs", "2.0"));
            resources.add(createSwaggerResource("meteor-forecast", "/api/forecast/v3/api-docs", "2.0"));
            resources.add(createSwaggerResource("path-planning", "/api/planning/v3/api-docs", "2.0"));
            resources.add(createSwaggerResource("data-assimilation", "/api/assimilation/v3/api-docs", "2.0"));
            resources.add(createSwaggerResource("weather-collector", "/api/weather/v3/api-docs", "2.0"));
            
            return resources;
        };
    }

    private SwaggerResource createSwaggerResource(String name, String location, String version) {
        SwaggerResource resource = new SwaggerResource();
        resource.setName(name);
        resource.setLocation(location);
        resource.setSwaggerVersion(version);
        return resource;
    }
}
