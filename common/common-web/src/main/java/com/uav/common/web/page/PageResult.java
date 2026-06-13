package com.uav.common.web.page;

import lombok.Data;

import java.io.Serializable;
import java.util.Collections;
import java.util.List;

/**
 * 分页结果
 *
 * @param <T> 数据类型
 */
@Data
public class PageResult<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 当前页数据 */
    private List<T> list;

    /** 总记录数 */
    private long total;

    /** 当前页码 */
    private int pageNum;

    /** 每页条数 */
    private int pageSize;

    /** 总页数 */
    private int totalPages;

    /** 是否有下一页 */
    private boolean hasNext;

    /** 是否有上一页 */
    private boolean hasPrevious;

    public PageResult() {
    }

    public PageResult(List<T> list, long total, int pageNum, int pageSize) {
        this.list = list;
        this.total = total;
        this.pageNum = pageNum;
        this.pageSize = pageSize;
        this.totalPages = pageSize > 0 ? (int) Math.ceil((double) total / pageSize) : 0;
        this.hasNext = pageNum < totalPages;
        this.hasPrevious = pageNum > 1;
    }

    /**
     * 空分页结果
     */
    public static <T> PageResult<T> empty(int pageNum, int pageSize) {
        return new PageResult<>(Collections.emptyList(), 0, pageNum, pageSize);
    }

    /**
     * 构建分页结果
     */
    public static <T> PageResult<T> of(List<T> list, long total, int pageNum, int pageSize) {
        return new PageResult<>(list, total, pageNum, pageSize);
    }
}
