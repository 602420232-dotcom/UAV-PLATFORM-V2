package com.uav.model;

import lombok.Data;
import java.util.Set;
import jakarta.persistence.*;

@Data
@Entity
@Table(name = "roles")
public class Role {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false)
    private String name;
    
    @Column(nullable = false)
    private String description;
    
    @ManyToMany(mappedBy = "roles")
    private Set<User> users;
}