package com.uav.assimilation.controller;

import com.uav.assimilation.dto.GprPostprocessRequest;
import com.uav.assimilation.dto.GprPostprocessResponse;
import com.uav.assimilation.dto.GprUncertaintyResponse;
import com.uav.assimilation.service.GprPostprocessService;
import com.uav.common.core.result.Result;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

/**
 * GPR 后处理控制器
 * <p>
 * 提供 GPR（高斯过程回归）后处理和不确定性查询接口，
 * 调用 algorithm-engine 的 GPRUncertaintyAdapter 进行计算。
 */
@RestController
@RequestMapping("/api/v1/assimilation")
@RequiredArgsConstructor
public class GprPostprocessController {

    private final GprPostprocessService gprPostprocessService;

    /**
     * GPR 后处理
     * <p>
     * 接收同化结果数据和 GPR 参数，调用 algorithm-engine 的 GPRUncertaintyAdapter，
     * 返回均值场、方差场和置信区间。
     *
     * @param request GPR 后处理请求参数
     * @return 均值场 + 方差场 + 置信区间
     */
    @PostMapping("/gpr-postprocess")
    @PreAuthorize("hasAuthority('assimilation:gpr:write')")
    public Result<GprPostprocessResponse> gprPostprocess(
            @Valid @RequestBody GprPostprocessRequest request) {
        GprPostprocessResponse response = gprPostprocessService.postprocess(request);
        return Result.success(response);
    }

    /**
     * GPR 不确定性查询
     * <p>
     * 查询指定区域和时间的不确定性场，返回不确定性分布和置信度统计。
     *
     * @param region 查询区域
     * @param time   查询时间
     * @return 不确定性分布 + 置信度统计
     */
    @GetMapping("/gpr/uncertainty")
    @PreAuthorize("hasAuthority('assimilation:gpr:read')")
    public Result<GprUncertaintyResponse> queryUncertainty(
            @RequestParam("region") String region,
            @RequestParam("time") String time) {
        GprUncertaintyResponse response = gprPostprocessService.queryUncertainty(region, time);
        return Result.success(response);
    }
}
