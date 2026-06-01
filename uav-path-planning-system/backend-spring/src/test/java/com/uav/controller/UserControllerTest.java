package com.uav.controller;

import com.uav.model.User;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("UserController 用户管理测试")
class UserControllerTest {

    private UserController userController;

    @BeforeEach
    void setUp() {
        userController = new UserController();
        ReflectionTestUtils.setField(userController, "initDefaultUsers", "true");
        userController.init();
    }

    @Test
    @DisplayName("初始化创建默认用户")
    void testInitCreatesDefaultUsers() {
        userController.init();
        var users = userController.getUsers();
        assertFalse(users.isEmpty());
    }

    @Test
    @DisplayName("跳过初始化")
    void testInitSkipped() {
        UserController controller = new UserController();
        ReflectionTestUtils.setField(controller, "initDefaultUsers", "false");
        controller.init();
        var users = controller.getUsers();
        assertTrue(users.isEmpty());
    }

    @Test
    @DisplayName("获取用户列表")
    void testGetUsers() {
        var users = userController.getUsers();
        assertFalse(users.isEmpty());
        assertEquals(2, users.size());
    }

    @Test
    @DisplayName("按ID获取用户")
    void testGetUserById() {
        User user = userController.getUser(1L);
        assertNotNull(user);
        assertEquals("admin", user.getUsername());
    }

    @Test
    @DisplayName("获取不存在的用户返回null")
    void testGetNonExistentUser() {
        User user = userController.getUser(999L);
        assertNull(user);
    }

    @Test
    @DisplayName("创建新用户")
    void testCreateUser() {
        User newUser = new User();
        newUser.setUsername("operator");
        newUser.setPassword("password123");
        newUser.setRole("OPERATOR");
        newUser.setName("操作员");

        User created = userController.createUser(newUser);
        assertNotNull(created);
        assertNotNull(created.getId());
        assertNotEquals("password123", created.getPassword());
        assertEquals(3, userController.getUsers().size());
    }

    @Test
    @DisplayName("更新用户信息")
    void testUpdateUser() {
        User update = new User();
        update.setUsername("admin_updated");
        update.setName("管理员新名");
        update.setRole("ADMIN");

        User result = userController.updateUser(1L, update);
        assertNotNull(result);
        assertEquals("admin_updated", result.getUsername());
        assertEquals("管理员新名", result.getName());
    }

    @Test
    @DisplayName("更新用户密码")
    void testUpdateUserPassword() {
        User update = new User();
        update.setPassword("newPass123");
        User result = userController.updateUser(1L, update);
        assertNotNull(result);
        assertNotEquals("newPass123", result.getPassword());
    }

    @Test
    @DisplayName("更新不存在用户返回null")
    void testUpdateNonExistentUser() {
        User update = new User();
        update.setUsername("ghost");
        User result = userController.updateUser(999L, update);
        assertNull(result);
    }

    @Test
    @DisplayName("删除用户")
    void testDeleteUser() {
        assertTrue(userController.deleteUser(1L));
        assertEquals(1, userController.getUsers().size());
    }

    @Test
    @DisplayName("删除不存在用户返回false")
    void testDeleteNonExistentUser() {
        assertFalse(userController.deleteUser(999L));
    }
}