package com.uav.platform.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.platform.entity.ApiKey;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface ApiKeyMapper extends BaseMapper<ApiKey> {

    @Select("SELECT * FROM sys_api_key WHERE key_value = #{keyValue} LIMIT 1")
    ApiKey selectByKeyValue(@Param("keyValue") String keyValue);

    @Select("SELECT * FROM sys_api_key WHERE tenant_id = #{tenantId}")
    List<ApiKey> selectByTenantId(@Param("tenantId") Long tenantId);

    @Update("UPDATE sys_api_key SET status = #{status} WHERE id = #{id}")
    int updateStatusById(@Param("id") Long id, @Param("status") Integer status);
}
