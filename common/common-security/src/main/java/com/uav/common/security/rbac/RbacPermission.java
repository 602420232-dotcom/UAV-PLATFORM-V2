package com.uav.common.security.rbac;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * RBAC 权限实体
 * <p>
 * 对应数据库表 sys_permission，支持三种资源类型：API、MENU、DATA。
 * resource_key 采用冒号分隔的层级格式，如 api:v1:planning:POST:path。
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "sys_permission")
public class RbacPermission {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "permission_name", nullable = false, length = 128)
    private String permissionName;

    @Enumerated(EnumType.STRING)
    @Column(name = "resource_type", nullable = false, length = 16)
    private ResourceType resourceType;

    @Column(name = "resource_key", nullable = false, length = 256, unique = true)
    private String resourceKey;

    @Column(name = "description", length = 256)
    private String description;

    /**
     * 资源类型枚举
     */
    public enum ResourceType {
        /** API 接口权限 */
        API,
        /** 菜单权限 */
        MENU,
        /** 数据权限 */
        DATA
    }
}
