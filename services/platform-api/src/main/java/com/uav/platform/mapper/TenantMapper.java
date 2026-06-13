package com.uav.platform.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.platform.entity.Tenant;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface TenantMapper extends BaseMapper<Tenant> {

    @Select("SELECT * FROM sys_tenant WHERE schema_name = #{schemaName} LIMIT 1")
    Tenant selectBySchemaName(@Param("schemaName") String schemaName);
}
