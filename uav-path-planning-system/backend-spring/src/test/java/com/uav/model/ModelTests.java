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
        user.setFullName("测试用户");
        user.setEmail("test@example.com");
        user.setEnabled(true);

        assertEquals(1L, user.getId());
        assertEquals("testuser", user.getUsername());
        assertEquals("encryptedPass", user.getPassword());
        assertEquals("测试用户", user.getFullName());
        assertEquals("test@example.com", user.getEmail());
        assertTrue(user.isEnabled());
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
        drone.setId(1L);
        drone.setName("UAV-001");
        drone.setModel("Quadrotor X8");
        drone.setSerialNumber("SN-2024-001");
        drone.setStatus("IDLE");
        drone.setCurrentLatitude(39.9);
        drone.setCurrentLongitude(116.4);
        drone.setCurrentAltitude(100.0);
        drone.setCruiseSpeed(15.0);
        drone.setMaxSpeed(20.0);
        drone.setBatteryLevel(85);

        assertEquals(1L, drone.getId());
        assertEquals("UAV-001", drone.getName());
        assertEquals("Quadrotor X8", drone.getModel());
        assertEquals("SN-2024-001", drone.getSerialNumber());
        assertEquals("IDLE", drone.getStatus());
        assertEquals(39.9, drone.getCurrentLatitude());
        assertEquals(116.4, drone.getCurrentLongitude());
        assertEquals(100.0, drone.getCurrentAltitude());
        assertEquals(15.0, drone.getCruiseSpeed());
        assertEquals(20.0, drone.getMaxSpeed());
        assertEquals(85, drone.getBatteryLevel());
    }

    @Test
    @DisplayName("Task模型测试")
    void testTaskModel() {
        Task task = new Task();
        task.setId(100L);
        task.setName("航拍任务");
        task.setDescription("高空航拍巡检");
        task.setLatitude(39.9);
        task.setLongitude(116.4);
        task.setAltitude(100.0);
        task.setDemand(5.0);
        task.setPriority(1);
        task.setStatus("PENDING");

        assertEquals(100L, task.getId());
        assertEquals("航拍任务", task.getName());
        assertEquals("高空航拍巡检", task.getDescription());
        assertEquals(39.9, task.getLatitude());
        assertEquals(116.4, task.getLongitude());
        assertEquals(100.0, task.getAltitude());
        assertEquals(5.0, task.getDemand());
        assertEquals(1, task.getPriority());
        assertEquals("PENDING", task.getStatus());
    }

    @Test
    @DisplayName("PathPlan模型测试")
    void testPathPlanModel() {
        PathPlan plan = new PathPlan();
        plan.setId(200L);
        plan.setName("航线方案A");
        plan.setDescription("城区全覆盖航线");
        plan.setDroneCount(3);
        plan.setTaskCount(10);
        plan.setTotalDistance(15000.0);
        plan.setTotalTime(120.0);
        plan.setStatus("PENDING");

        assertEquals(200L, plan.getId());
        assertEquals("航线方案A", plan.getName());
        assertEquals("城区全覆盖航线", plan.getDescription());
        assertEquals(3, plan.getDroneCount());
        assertEquals(10, plan.getTaskCount());
        assertEquals(15000.0, plan.getTotalDistance());
        assertEquals(120.0, plan.getTotalTime());
        assertEquals("PENDING", plan.getStatus());
    }

    @Test
    @DisplayName("WeatherData模型测试")
    void testWeatherDataModel() {
        WeatherData weather = new WeatherData();
        weather.setId(300L);
        weather.setMinLatitude(39.0);
        weather.setMaxLatitude(40.0);
        weather.setMinLongitude(116.0);
        weather.setMaxLongitude(117.0);
        weather.setHeight(500);
        weather.setSource("WRF");
        weather.setStatus("AVAILABLE");

        assertEquals(300L, weather.getId());
        assertEquals(39.0, weather.getMinLatitude());
        assertEquals(40.0, weather.getMaxLatitude());
        assertEquals(116.0, weather.getMinLongitude());
        assertEquals(117.0, weather.getMaxLongitude());
        assertEquals(500, weather.getHeight());
        assertEquals("WRF", weather.getSource());
        assertEquals("AVAILABLE", weather.getStatus());
    }
}
