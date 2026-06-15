package com.uav.platform.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.uav.platform.entity.AlgorithmRegistration;
import com.uav.platform.mapper.AlgorithmRegistrationMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.regex.Pattern;

/**
 * 算法注册中心业务逻辑层
 * 提供算法注册、版本管理、健康检查等功能
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AlgorithmRegistryService extends ServiceImpl<AlgorithmRegistrationMapper, AlgorithmRegistration> {

    private final AlgorithmRegistrationMapper algorithmRegistrationMapper;
    private final RestTemplate restTemplate = new RestTemplate();

    /**
     * 语义化版本正则表达式
     */
    private static final Pattern SEMVER_PATTERN = Pattern.compile(
            "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-((?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\\.(?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\\+([0-9a-zA-Z-]+(?:\\.[0-9a-zA-Z-]+)*))?$"
    );

    /**
     * 支持的算法类型
     */
    private static final List<String> SUPPORTED_TYPES = List.of(
            "planning", "observation", "assimilation", "risk", "weather", "fusion", "generic"
    );

    /**
     * 注册新算法
     *
     * @param registration 算法注册信息
     * @return 注册后的算法实体
     */
    @Transactional(rollbackFor = Exception.class)
    public AlgorithmRegistration register(AlgorithmRegistration registration) {
        // 验证算法名称
        if (registration.getName() == null || registration.getName().trim().isEmpty()) {
            throw new IllegalArgumentException("算法名称不能为空");
        }

        // 验证算法类型
        if (registration.getType() == null || !SUPPORTED_TYPES.contains(registration.getType().toLowerCase())) {
            throw new IllegalArgumentException("不支持的算法类型: " + registration.getType() +
                    ", 支持的类型: " + SUPPORTED_TYPES);
        }

        // 验证版本号格式
        if (registration.getVersion() == null || !SEMVER_PATTERN.matcher(registration.getVersion()).matches()) {
            throw new IllegalArgumentException("版本号格式不正确，请使用语义化版本格式（如：1.0.0）");
        }

        // 验证端点格式
        if (registration.getEndpoint() == null || !registration.getEndpoint().startsWith("http")) {
            throw new IllegalArgumentException("端点必须是有效的 HTTP/HTTPS URL");
        }

        // 检查是否已存在相同名称和版本的算法
        AlgorithmRegistration existing = algorithmRegistrationMapper.selectByNameAndVersion(
                registration.getName(), registration.getVersion());
        if (existing != null) {
            throw new IllegalArgumentException("算法已存在: " + registration.getName() + " v" + registration.getVersion());
        }

        // 设置默认值
        registration.setStatus(1);
        registration.setCreatedAt(LocalDateTime.now());
        registration.setUpdatedAt(LocalDateTime.now());

        save(registration);
        log.info("算法注册成功: {} v{} (类型: {}, 端点: {})",
                registration.getName(), registration.getVersion(),
                registration.getType(), registration.getEndpoint());

        return registration;
    }

    /**
     * 发布新版本
     *
     * @param baseId      基础算法ID
     * @param newVersion  新版本号
     * @param newEndpoint 新端点（可选，为空则继承原端点）
     * @param newSchema   新参数Schema（可选，为空则继承原Schema）
     * @return 新版本算法实体
     */
    @Transactional(rollbackFor = Exception.class)
    public AlgorithmRegistration publishVersion(Long baseId, String newVersion, String newEndpoint, String newSchema) {
        AlgorithmRegistration base = getById(baseId);
        if (base == null) {
            throw new IllegalArgumentException("算法不存在: " + baseId);
        }

        // 验证新版本号格式
        if (newVersion == null || !SEMVER_PATTERN.matcher(newVersion).matches()) {
            throw new IllegalArgumentException("版本号格式不正确，请使用语义化版本格式（如：1.0.0）");
        }

        // 检查新版本是否已存在
        AlgorithmRegistration existing = algorithmRegistrationMapper.selectByNameAndVersion(base.getName(), newVersion);
        if (existing != null) {
            throw new IllegalArgumentException("版本已存在: " + base.getName() + " v" + newVersion);
        }

        // 创建新版本
        AlgorithmRegistration newVersionEntity = new AlgorithmRegistration();
        newVersionEntity.setName(base.getName());
        newVersionEntity.setType(base.getType());
        newVersionEntity.setVersion(newVersion);
        newVersionEntity.setEndpoint(newEndpoint != null ? newEndpoint : base.getEndpoint());
        newVersionEntity.setParamSchema(newSchema != null ? newSchema : base.getParamSchema());
        newVersionEntity.setDescription(base.getDescription());
        newVersionEntity.setStatus(1);
        newVersionEntity.setCreatedAt(LocalDateTime.now());
        newVersionEntity.setUpdatedAt(LocalDateTime.now());

        save(newVersionEntity);
        log.info("算法新版本发布成功: {} v{} (基于 v{})",
                base.getName(), newVersion, base.getVersion());

        return newVersionEntity;
    }

    /**
     * 注销算法
     *
     * @param id 算法ID
     */
    @Transactional(rollbackFor = Exception.class)
    public void unregister(Long id) {
        AlgorithmRegistration registration = getById(id);
        if (registration == null) {
            throw new IllegalArgumentException("算法不存在: " + id);
        }

        removeById(id);
        log.info("算法已注销: {} v{}", registration.getName(), registration.getVersion());
    }

    /**
     * 分页查询算法列表
     *
     * @param current  当前页
     * @param size     每页大小
     * @param type     算法类型（可选筛选）
     * @param status   状态（可选筛选）
     * @return 分页结果
     */
    public Page<AlgorithmRegistration> listAlgorithms(Integer current, Integer size, String type, Integer status) {
        Page<AlgorithmRegistration> page = new Page<>(current, size);
        return lambdaQuery()
                .eq(type != null && !type.isEmpty(), AlgorithmRegistration::getType, type)
                .eq(status != null, AlgorithmRegistration::getStatus, status)
                .orderByDesc(AlgorithmRegistration::getUpdatedAt)
                .page(page);
    }

    /**
     * 获取指定算法的所有版本
     *
     * @param name 算法名称
     * @return 版本列表
     */
    public List<AlgorithmRegistration> getVersions(String name) {
        return algorithmRegistrationMapper.selectVersionsByName(name);
    }

    /**
     * 执行健康检查
     * 向算法端点发送健康探测请求
     *
     * @param id 算法ID
     * @return 健康状态：true-健康，false-异常
     */
    public boolean healthCheck(Long id) {
        AlgorithmRegistration registration = getById(id);
        if (registration == null) {
            throw new IllegalArgumentException("算法不存在: " + id);
        }

        String healthEndpoint = registration.getEndpoint() + "/actuator/health";
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(healthEndpoint, String.class);
            boolean healthy = response.getStatusCode().is2xxSuccessful();

            // 更新状态
            Integer newStatus = healthy ? 1 : 0;
            if (!newStatus.equals(registration.getStatus())) {
                registration.setStatus(newStatus);
                registration.setUpdatedAt(LocalDateTime.now());
                updateById(registration);
            }

            log.info("算法健康检查完成: {} v{} - {}",
                    registration.getName(), registration.getVersion(),
                    healthy ? "健康" : "异常");
            return healthy;
        } catch (Exception e) {
            log.warn("算法健康检查失败: {} v{} - {}",
                    registration.getName(), registration.getVersion(), e.getMessage());

            // 标记为异常状态
            registration.setStatus(0);
            registration.setUpdatedAt(LocalDateTime.now());
            updateById(registration);
            return false;
        }
    }

    /**
     * 批量健康检查所有已启用算法
     */
    public void healthCheckAll() {
        List<AlgorithmRegistration> enabledAlgorithms = lambdaQuery()
                .eq(AlgorithmRegistration::getStatus, 1)
                .list();

        for (AlgorithmRegistration algorithm : enabledAlgorithms) {
            try {
                healthCheck(algorithm.getId());
            } catch (Exception e) {
                log.error("批量健康检查异常: {} v{}", algorithm.getName(), algorithm.getVersion(), e);
            }
        }
    }

    /**
     * 更新算法状态
     *
     * @param id     算法ID
     * @param status 新状态
     */
    @Transactional(rollbackFor = Exception.class)
    public void updateStatus(Long id, Integer status) {
        AlgorithmRegistration registration = getById(id);
        if (registration == null) {
            throw new IllegalArgumentException("算法不存在: " + id);
        }

        registration.setStatus(status);
        registration.setUpdatedAt(LocalDateTime.now());
        updateById(registration);
        log.info("算法状态更新: {} v{} -> 状态 {}",
                registration.getName(), registration.getVersion(), status);
    }
}
