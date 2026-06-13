package com.uav.platform.interceptor;

import com.baomidou.mybatisplus.extension.plugins.inner.InnerInterceptor;
import com.uav.platform.config.DynamicDataSource;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.ibatis.executor.Executor;
import org.apache.ibatis.mapping.BoundSql;
import org.apache.ibatis.mapping.MappedStatement;
import org.apache.ibatis.session.ResultHandler;
import org.apache.ibatis.session.RowBounds;
import org.springframework.stereotype.Component;

import java.sql.SQLException;

@Slf4j
@Component
@RequiredArgsConstructor
public class TenantLineInnerInterceptor implements InnerInterceptor {

    private final DynamicDataSource dynamicDataSource;

    @Override
    public void beforeQuery(Executor executor, MappedStatement ms, Object parameter,
                            RowBounds rowBounds, ResultHandler resultHandler, BoundSql boundSql) throws SQLException {
        String schema = resolveSchema(parameter);
        if (schema != null) {
            DynamicDataSource.CONTEXT.set(schema);
        }
    }

    @Override
    public void beforeUpdate(Executor executor, MappedStatement ms, Object parameter) throws SQLException {
        String schema = resolveSchema(parameter);
        if (schema != null) {
            DynamicDataSource.CONTEXT.set(schema);
        }
    }

    private String resolveSchema(Object parameter) {
        String current = DynamicDataSource.CONTEXT.get();
        if (current != null) {
            return current;
        }
        return null;
    }
}
