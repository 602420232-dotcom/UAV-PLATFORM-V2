package com.uav.controller;
import com.uav.model.User;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import jakarta.annotation.PostConstruct;
import java.util.ArrayList;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class UserController {

    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    @Value("${app.default-password:Uav@2024!Secure}")
    private String defaultPassword;

    @Value("${app.init-default-users:true}")
    private boolean initDefaultUsers;

    private List<User> users = new ArrayList<>();

    @PostConstruct
    public void init() {
        if (!initDefaultUsers) {
            return;
        }
        User admin = new User();
        admin.setId(1L);
        admin.setUsername("admin");
        admin.setPassword(passwordEncoder.encode(defaultPassword));
        admin.setRole("ADMIN");
        admin.setName("管理员");
        admin.setEmail("admin@example.com");
        admin.setPhone("13800138000");

        User dispatcher = new User();
        dispatcher.setId(2L);
        dispatcher.setUsername("dispatcher");
        dispatcher.setPassword(passwordEncoder.encode(defaultPassword));
        dispatcher.setRole("DISPATCHER");
        dispatcher.setName("调度员");
        dispatcher.setEmail("dispatcher@example.com");
        dispatcher.setPhone("13800138001");

        users.add(admin);
        users.add(dispatcher);
    }

    @GetMapping("/admin/users")
    public List<User> getUsers() {
        return users;
    }

    @GetMapping("/admin/users/{id}")
    public User getUser(@PathVariable Long id) {
        return users.stream().filter(u -> u.getId().equals(id)).findFirst().orElse(null);
    }

    @PostMapping("/admin/users")
    public User createUser(@RequestBody User user) {
        user.setId((long) (users.size() + 1));
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        users.add(user);
        return user;
    }

    @PutMapping("/admin/users/{id}")
    public User updateUser(@PathVariable Long id, @RequestBody User user) {
        User existingUser = users.stream().filter(u -> u.getId().equals(id)).findFirst().orElse(null);
        if (existingUser != null) {
            existingUser.setUsername(user.getUsername());
            if (user.getPassword() != null && !user.getPassword().isEmpty()) {
                existingUser.setPassword(passwordEncoder.encode(user.getPassword()));
            }
            existingUser.setRole(user.getRole());
            existingUser.setName(user.getName());
            existingUser.setEmail(user.getEmail());
            existingUser.setPhone(user.getPhone());
        }
        return existingUser;
    }

    @DeleteMapping("/admin/users/{id}")
    public boolean deleteUser(@PathVariable Long id) {
        return users.removeIf(u -> u.getId().equals(id));
    }
}
