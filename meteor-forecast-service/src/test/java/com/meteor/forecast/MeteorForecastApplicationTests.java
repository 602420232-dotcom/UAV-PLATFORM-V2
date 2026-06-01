package com.meteor.forecast;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
@Disabled("需要完整基础设施（MySQL + Nacos），在CI集成测试环境中运行")
class MeteorForecastApplicationTests {

    @Test
    void contextLoads() {
    }
}
