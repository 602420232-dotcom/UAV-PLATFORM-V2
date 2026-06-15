package com.uav.platform.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.platform.entity.AlgorithmRegistration;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 算法注册数据访问层
 */
@Mapper
public interface AlgorithmRegistrationMapper extends BaseMapper<AlgorithmRegistration> {

    /**
     * 根据算法名称和版本查询
     */
    @Select("SELECT * FROM sys_algorithm_registration WHERE name = #{name} AND version = #{version} LIMIT 1")
    AlgorithmRegistration selectByNameAndVersion(@Param("name") String name, @Param("version") String version);

    /**
     * 根据算法类型查询所有已启用的算法
     */
    @Select("SELECT * FROM sys_algorithm_registration WHERE type = #{type} AND status = 1 ORDER BY updated_at DESC")
    List<AlgorithmRegistration> selectEnabledByType(@Param("type") String type);

    /**
     * 查询指定算法的所有版本
     */
    @Select("SELECT * FROM sys_algorithm_registration WHERE name = #{name} ORDER BY created_at DESC")
    List<AlgorithmRegistration> selectVersionsByName(@Param("name") String name);
}
