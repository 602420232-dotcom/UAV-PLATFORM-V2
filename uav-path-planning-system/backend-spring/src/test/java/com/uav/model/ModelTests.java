package com.uav.model;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("领域模型测试")
class ModelTests {

    @Test
    @DisplayName("User模型完整测试")
    void testUserModel() {
        User user = new User();
        user.setId(1L);
        user.setUsername("testuser");
        user.setPassword("encryptedPass");
        user.setRole("ADMIN");
        user.setName("测试用户");
        user.setEmail("test@example.com");
        user.setPhone("13800138000");

        assertEquals(1L, user.getId());
        assertEquals("testuser", user.getUsername());
        assertEquals("encryptedPass", user.getPassword());
        assertEquals("ADMIN", user.getRole());
        assertEquals("测试用户", user.getName());
        assertEquals("test@example.com", user.getEmail());
        assertEquals("13800138000", user.getPhone());
    }

    @Test
    @DisplayName("Role模型测试")
    void testRoleModel() {
        Role role = new Role();
        role.setId(1L);
        role.setName("ADMIN");
        assertEquals(1L, role.getId());
        assertEquals("ADMIN", role.getName());
    }

    @Test
    @DisplayName("Drone模型测试")
    void testDroneModel() {
        Drone drone = new Drone();
        drone.setId("UAV-001");
        drone.setStatus("active");
        drone.setLatitude(39.9);
        drone.setLongitude(116.4);
        drone.setAltitude(100.0);
        drone.setSpeed(15.0);
        drone.setBattery(85);

        assertEquals("UAV-001", drone.getId());
        assertEquals("active", drone.getStatus());
        assertEquals(39.9, drone.getLatitude());
        assertEquals(116.4, drone.getLongitude());
        assertEquals(100.0, drone.getAltitude());
        assertEquals(15.0, drone.getSpeed());
        assertEquals(85, drone.getBattery());
    }

    @Test
    @DisplayName("Task模型测试")
    void testTaskModel() {
        Task task = new Task();
        task.setId(100L);
        task.setName("航拍任务");
        task.setType("survey");
        task.setStatus("pending");
        task.setPriority(1);

        assertEquals(100L, task.getId());
        assertEquals("航拍任务", task.getName());
        assertEquals("survey", task.getType());
        assertEquals("pending", task.getStatus());
        assertEquals(1, task.getPriority());
    }

    @Test
    @DisplayName("PathPlan模型测试")
    void testPathPlanModel() {
        PathPlan plan = new PathPlan();
        plan.setId(200L);
        plan.setName("航线方案A");
        plan.setDroneId("UAV-001");
        plan.setStatus("active");

        assertEquals(200L, plan.getId());
        assertEquals("航线方案A", plan.getName());
        assertEquals("UAV-001", plan.getDroneId());
        assertEquals("active", plan.getStatus());
    }

    @Test
    @DisplayName("WeatherData模型测试")
    void testWeatherDataModel() {
        com.uav.model.WeatherData weather = new com.uav.model.WeatherData();
        weather.setId(300L);
        weather.setLatitude(39.9);
        weather.setLongitude(116.4);
        weather.setTemperature(25.0);
        weather.setWindSpeed(5.0);
        weather.setWindDirection(180);
        weather.setHumidity(60);
        weather.setPressure(1013.25);

        assertEquals(300L, weather.getId());
        assertEquals(39.9, weather.getLatitude());
        assertEquals(116.4, weather.getLongitude());
        assertEquals(25.0, weather.getTemperature());
        assertEquals(5.0, weather.getWindSpeed());
        assertEquals(180, weather.getWindDirection());
        assertEquals(60, weather.getHumidity());
        assertEquals(1013.25, weather.getPressure());
    }
}