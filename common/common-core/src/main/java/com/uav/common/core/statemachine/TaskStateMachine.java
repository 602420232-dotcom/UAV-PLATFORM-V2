package com.uav.common.core.statemachine;

import com.uav.common.core.constant.TaskStatus;
import com.uav.common.core.exception.BizException;
import com.uav.common.core.result.ResultCode;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.Set;

/**
 * 异步任务状态机
 * <p>
 * 定义任务状态的合法转换规则，在状态变更前进行校验。
 * <pre>
 *   QUEUED  -> RUNNING, CANCELLED
 *   RUNNING -> SUCCESS, FAILED, TIMEOUT, CANCELLED
 *   SUCCESS -> (终态)
 *   FAILED  -> QUEUED (允许重试)
 *   TIMEOUT -> QUEUED (允许重试)
 *   CANCELLED -> (终态)
 * </pre>
 */
@Component
public class TaskStateMachine {

    /**
     * 合法状态转换定义
     */
    private static final Map<TaskStatus, Set<TaskStatus>> TRANSITIONS = Map.of(
            TaskStatus.QUEUED, Set.of(TaskStatus.RUNNING, TaskStatus.CANCELLED),
            TaskStatus.RUNNING, Set.of(TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED),
            TaskStatus.SUCCESS, Set.of(),
            TaskStatus.FAILED, Set.of(TaskStatus.QUEUED),
            TaskStatus.TIMEOUT, Set.of(TaskStatus.QUEUED),
            TaskStatus.CANCELLED, Set.of()
    );

    /**
     * 判断状态转换是否合法
     *
     * @param from 源状态
     * @param to   目标状态
     * @return 是否允许转换
     */
    public boolean canTransition(TaskStatus from, TaskStatus to) {
        if (from == null || to == null) {
            return false;
        }
        Set<TaskStatus> allowedTargets = TRANSITIONS.get(from);
        return allowedTargets != null && allowedTargets.contains(to);
    }

    /**
     * 校验状态转换，不合法则抛出 {@link BizException}
     *
     * @param from 源状态
     * @param to   目标状态
     * @throws BizException 状态转换不合法时抛出
     */
    public void validateTransition(TaskStatus from, TaskStatus to) {
        if (!canTransition(from, to)) {
            throw new BizException(ResultCode.BAD_REQUEST,
                    String.format("非法状态转换: %s -> %s", from.getName(), to.getName()));
        }
    }

    /**
     * 通过状态名称校验状态转换
     *
     * @param fromName 源状态名称
     * @param toName   目标状态名称
     * @throws BizException 状态转换不合法或状态名称无效时抛出
     */
    public void validateTransition(String fromName, String toName) {
        TaskStatus from = TaskStatus.fromName(fromName);
        TaskStatus to = TaskStatus.fromName(toName);
        if (from == null) {
            throw new BizException(ResultCode.BAD_REQUEST,
                    String.format("未知的源状态: %s", fromName));
        }
        if (to == null) {
            throw new BizException(ResultCode.BAD_REQUEST,
                    String.format("未知的目标状态: %s", toName));
        }
        validateTransition(from, to);
    }
}
