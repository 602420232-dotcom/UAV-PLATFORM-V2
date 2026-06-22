package com.uav.common.security.rbac;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

/**
 * 用户 Repository
 * <p>
 * 提供基于 JPA 的用户数据访问，支持关联查询角色和权限。
 */
public interface RbacUserRepository extends JpaRepository<com.uav.common.security.rbac.RbacUser, Long> {

    /**
     * 根据用户名查询用户（包含角色和权限）
     *
     * @param username 用户名
     * @return 用户实体，不存在则返回 null
     */
    @Query("SELECT DISTINCT u FROM RbacUser u " +
           "LEFT JOIN FETCH u.roles r " +
           "LEFT JOIN FETCH r.permissions p " +
           "WHERE u.username = :username")
    RbacUser findByUsernameWithRolesAndPermissions(@Param("username") String username);
}
