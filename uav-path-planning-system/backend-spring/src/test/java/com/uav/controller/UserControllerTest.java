package com.uav.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.model.User;
import com.uav.service.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.http.MediaType;

import java.util.Arrays;
import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(UserController.class)
@AutoConfigureMockMvc(addFilters = false)
@DisplayName("UserController 用户管理测试")
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private UserService userService;

    private User adminUser;
    private User operatorUser;

    @BeforeEach
    void setUp() {
        adminUser = new User();
        adminUser.setId(1L);
        adminUser.setUsername("admin");
        adminUser.setPassword("encoded-password");
        adminUser.setEmail("admin@example.com");
        adminUser.setFullName("管理员");
        adminUser.setEnabled(true);

        operatorUser = new User();
        operatorUser.setId(2L);
        operatorUser.setUsername("operator");
        operatorUser.setPassword("encoded-password");
        operatorUser.setEmail("operator@example.com");
        operatorUser.setFullName("操作员");
        operatorUser.setEnabled(true);
    }

    @Test
    @DisplayName("获取用户列表")
    void testGetUsers() throws Exception {
        List<User> users = Arrays.asList(adminUser, operatorUser);
        when(userService.findAll()).thenReturn(users);

        mockMvc.perform(get("/api/admin/users"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].username").value("admin"))
                .andExpect(jsonPath("$[1].username").value("operator"));

        verify(userService, times(1)).findAll();
    }

    @Test
    @DisplayName("按ID获取用户")
    void testGetUserById() throws Exception {
        when(userService.findById(1L)).thenReturn(adminUser);

        mockMvc.perform(get("/api/admin/users/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("admin"))
                .andExpect(jsonPath("$.fullName").value("管理员"));

        verify(userService, times(1)).findById(1L);
    }

    @Test
    @DisplayName("获取不存在的用户返回404")
    void testGetNonExistentUser() throws Exception {
        when(userService.findById(999L)).thenReturn(null);

        mockMvc.perform(get("/api/admin/users/999"))
                .andExpect(status().isNotFound())
                .andExpect(content().string("用户不存在"));

        verify(userService, times(1)).findById(999L);
    }

    @Test
    @DisplayName("创建新用户")
    void testCreateUser() throws Exception {
        User newUser = new User();
        newUser.setUsername("newuser");
        newUser.setPassword("password123");
        newUser.setEmail("newuser@example.com");
        newUser.setFullName("新用户");

        User createdUser = new User();
        createdUser.setId(3L);
        createdUser.setUsername("newuser");
        createdUser.setPassword("encoded-password");
        createdUser.setEmail("newuser@example.com");
        createdUser.setFullName("新用户");

        when(userService.create(any(User.class))).thenReturn(createdUser);

        mockMvc.perform(post("/api/admin/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(newUser)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(3L))
                .andExpect(jsonPath("$.username").value("newuser"))
                .andExpect(jsonPath("$.password").value("encoded-password"));

        verify(userService, times(1)).create(any(User.class));
    }

    @Test
    @DisplayName("更新用户信息")
    void testUpdateUser() throws Exception {
        User updateUser = new User();
        updateUser.setUsername("admin_updated");
        updateUser.setFullName("管理员新名");
        updateUser.setEmail("admin_new@example.com");

        User updatedUser = new User();
        updatedUser.setId(1L);
        updatedUser.setUsername("admin_updated");
        updatedUser.setPassword("encoded-password");
        updatedUser.setEmail("admin_new@example.com");
        updatedUser.setFullName("管理员新名");

        when(userService.update(eq(1L), any(User.class))).thenReturn(updatedUser);

        mockMvc.perform(put("/api/admin/users/1")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updateUser)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("admin_updated"))
                .andExpect(jsonPath("$.fullName").value("管理员新名"));

        verify(userService, times(1)).update(eq(1L), any(User.class));
    }

    @Test
    @DisplayName("更新不存在用户返回404")
    void testUpdateNonExistentUser() throws Exception {
        User updateUser = new User();
        updateUser.setUsername("ghost");

        when(userService.update(eq(999L), any(User.class))).thenReturn(null);

        mockMvc.perform(put("/api/admin/users/999")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updateUser)))
                .andExpect(status().isNotFound())
                .andExpect(content().string("用户不存在"));

        verify(userService, times(1)).update(eq(999L), any(User.class));
    }

    @Test
    @DisplayName("删除用户")
    void testDeleteUser() throws Exception {
        when(userService.findById(1L)).thenReturn(adminUser);
        doNothing().when(userService).delete(1L);

        mockMvc.perform(delete("/api/admin/users/1"))
                .andExpect(status().isNoContent());

        verify(userService, times(1)).findById(1L);
        verify(userService, times(1)).delete(1L);
    }

    @Test
    @DisplayName("删除不存在用户返回404")
    void testDeleteNonExistentUser() throws Exception {
        when(userService.findById(999L)).thenReturn(null);

        mockMvc.perform(delete("/api/admin/users/999"))
                .andExpect(status().isNotFound())
                .andExpect(content().string("用户不存在"));

        verify(userService, times(1)).findById(999L);
        verify(userService, never()).delete(anyLong());
    }
}
