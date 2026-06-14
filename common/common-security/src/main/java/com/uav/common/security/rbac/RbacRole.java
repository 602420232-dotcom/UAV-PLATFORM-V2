package com.uav.common.security.rbac;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToMany;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.HashSet;
import java.util.Set;

/**
 * RBAC 角色实体
 * <p>
 * 对应数据库表 sys_role，每个角色拥有唯一的 roleCode 作为业务标识。
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "sys_role")
public class RbacRole {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "role_name", nullable = false, length = 64)
    private String roleName;

    @Column(name = "role_code", nullable = false, length = 64, unique = true)
    private String roleCode;

    @Column(name = "description", length = 256)
    private String description;

    @Column(name = "status", nullable = false)
    private Integer status;

    @ManyToMany(mappedBy = "roles")
    @Builder.Default
    private Set<RbacPermission> permissions = new HashSet<>();

    public Set<RbacPermission> getPermissions() {
        return permissions;
    }
}
