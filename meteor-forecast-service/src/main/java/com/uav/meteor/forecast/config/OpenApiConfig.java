package com.uav.meteor.forecast.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class OpenApiConfig {

    @Value("${server.port:8080}")
    private int serverPort;

    @Value("${spring.application.name:meteor-forecast-service}")
    private String applicationName;

    @Bean
    public OpenAPI customOpenAPI() {
        final String securitySchemeName = "bearerAuth";

        return new OpenAPI()
                .info(new Info()
                        .title("Meteor Forecast Service API")
                        .version("2.0")
                        .description("气象预测服务 - LSTM + XGBoost + GPR 气象预测与订正\n\n" +
                                "功能模块：\n" +
                                "- LSTM时序气象预测\n" +
                                "- XGBoost气象要素订正\n" +
                                "- GPR高斯过程回归预测\n" +
                                "- 气象因子融合分析")
                        .contact(new Contact()
                                .name("DITHIOTHREITOL")
                                .email("support@uav-platform.com")
                                .url("https://github.com/DITHIOTHREITOL"))
                        .license(new License()
                                .name("Apache 2.0")
                                .url("https://www.apache.org/licenses/LICENSE-2.0")))
                .servers(List.of(
                        new Server()
                                .url("http://localhost:" + serverPort)
                                .description("Local Development Server"),
                        new Server()
                                .url("http://meteor-forecast-service:8080")
                                .description("Docker Compose Service"),
                        new Server()
                                .url("http://meteor-forecast-service:8080")
                                .description("Kubernetes Service")))
                .addSecurityItem(new SecurityRequirement().addList(securitySchemeName))
                .components(new Components()
                        .addSecuritySchemes(securitySchemeName,
                                new SecurityScheme()
                                        .name(securitySchemeName)
                                        .type(SecurityScheme.Type.HTTP)
                                        .scheme("bearer")
                                        .bearerFormat("JWT")
                                        .description("Enter JWT token")));
    }
}
