package com.uav.common.security.rbac;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.List;
import java.util.stream.Collectors;

/**
 * RBAC 用户详情
 * <p>
 * 实现 Spring Security 的 {@link UserDetails} 接口，封装用户基本信息、
 * 角色列表和权限列表，供认证和授权流程使用。
 * <p>
 * 权限格式：resourceType:resourceKey，如 api:v1:planning:POST:path
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RbacUserDetails implements UserDetails {

    /** 用户ID */
    private Long id;

    /** 用户名 */
    private String username;

    /** 密码哈希 */
    private String password;

    /** 邮箱 */
    private String email;

    /** 手机号 */
    private String phone;

    /** 状态：1-启用 0-禁用 */
    private Integer status;

    /** 角色列表 */
    private List<RbacRole> roles;

    /** 权限列表 */
    private List<RbacPermission> permissions;

    /** 账户是否未过期 */
    @Builder.Default
    private boolean accountNonExpired = true;

    /** 账户是否未锁定 */
    @Builder.Default
    private boolean accountNonLocked = true;

    /** 凭证是否未过期 */
    @Builder.Default
    private boolean credentialsNonExpired = true;

    /** 账户是否启用 */
    @Builder.Default
    private boolean enabled = true;

    /**
     * 返回角色编码列表作为 GrantedAuthority（格式：ROLE_ADMIN）
     */
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        // 角色权限
        List<SimpleGrantedAuthority> roleAuthorities = roles.stream()
                .map(role -> new SimpleGrantedAuthority("ROLE_" + role.getRoleCode()))
                .collect(Collectors.toList());

        // 资源权限
        List<SimpleGrantedAuthority> permissionAuthorities = permissions.stream()
                .map(perm -> new SimpleGrantedAuthority(
                        perm.getResourceType().name() + ":" + perm.getResourceKey()))
                .collect(Collectors.toList());

        roleAuthorities.addAll(permissionAuthorities);
        return roleAuthorities;
    }

    @Override
    public boolean isAccountNonExpired() {
        return accountNonExpired;
    }

    @Override
    public boolean isAccountNonLocked() {
        return accountNonLocked;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return credentialsNonExpired;
    }

    @Override
    public boolean isEnabled() {
        return enabled && status != null && status == 1;
    }
}
