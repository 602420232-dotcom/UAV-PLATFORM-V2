package com.uav.common.web.page;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

import java.io.Serializable;

/**
 * 分页查询基类
 */
@Data
public class PageQuery implements Serializable {

    private static final long serialVersionUID = 1L;

    private static final int DEFAULT_PAGE_NUM = 1;
    private static final int DEFAULT_PAGE_SIZE = 10;
    private static final int MAX_PAGE_SIZE = 500;

    /** 当前页码 */
    @Min(value = 1, message = "页码必须大于等于1")
    private int pageNum = DEFAULT_PAGE_NUM;

    /** 每页条数 */
    @Min(value = 1, message = "每页条数必须大于等于1")
    @Max(value = MAX_PAGE_SIZE, message = "每页条数不能超过" + MAX_PAGE_SIZE)
    private int pageSize = DEFAULT_PAGE_SIZE;

    /**
     * 获取偏移量（用于MyBatis等）
     */
    public int getOffset() {
        return (pageNum - 1) * pageSize;
    }
}
