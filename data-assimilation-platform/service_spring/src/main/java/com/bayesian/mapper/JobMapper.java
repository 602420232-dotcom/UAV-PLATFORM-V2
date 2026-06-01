package com.bayesian.mapper;
import com.bayesian.entity.Job;
import java.util.List;
import org.apache.ibatis.annotations.*;

@Mapper
public interface JobMapper {

    @Insert("INSERT INTO assimilation_jobs(job_id, algorithm, input_data, status, created_at) " +
            "VALUES(#{jobId}, #{algorithm}, #{inputData}, #{status}, #{createdAt})")
    void insert(Job job);

    @Select("SELECT * FROM assimilation_jobs WHERE job_id = #{jobId}")
    Job findByJobId(String jobId);

    @Select("SELECT * FROM assimilation_jobs ORDER BY created_at DESC LIMIT #{limit}")
    List<Job> findRecent(@Param("limit") int limit);

    @Update("UPDATE assimilation_jobs SET status = #{status}, result_data = #{resultData}, " +
            "error_message = #{errorMessage}, updated_at = NOW() WHERE job_id = #{jobId}")
    void updateStatus(Job job);
}
