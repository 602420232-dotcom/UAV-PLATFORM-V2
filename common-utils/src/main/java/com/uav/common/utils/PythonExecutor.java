package com.uav.common.utils;

import com.uav.common.script.PythonScriptInvoker;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * Python 脚本执行器
 *
 * @deprecated 请使用 {@link PythonScriptInvoker} 替代。
 * PythonScriptInvoker 提供了更完善的功能，包括：
 * <ul>
 *   <li>enabled/disabled 开关</li>
 *   <li>异步执行 (executeAsync)</li>
 *   <li>自动重试 (executeWithRetry)</li>
 *   <li>Map 结果解析 (executeAsMap)</li>
 *   <li>更完整的脚本白名单</li>
 * </ul>
 * 此类保留以保持向后兼容，所有调用均委托给 PythonScriptInvoker。
 */
@Deprecated
@Slf4j
@Component
public class PythonExecutor {

    private final PythonScriptInvoker delegate;

    public PythonExecutor(PythonScriptInvoker delegate) {
        this.delegate = delegate;
        log.warn("PythonExecutor is deprecated. Use PythonScriptInvoker instead.");
    }

    /**
     * @deprecated 使用 {@link PythonScriptInvoker#execute(String, String, Map)} 替代
     */
    @Deprecated
    public String execute(String scriptName, String action, Map<String, Object> params) {
        return delegate.execute(scriptName, action, params);
    }

    /**
     * @deprecated 使用 {@link PythonScriptInvoker#executeAsync(String, String, Map)} 替代
     */
    @Deprecated
    public CompletableFuture<String> executeAsync(String scriptName, String action, Map<String, Object> params) {
        return delegate.executeAsync(scriptName, action, params);
    }

    /**
     * @deprecated 使用 {@link PythonScriptInvoker#executeWithRetry(String, String, Map, int)} 替代
     */
    @Deprecated
    public String executeWithRetry(String scriptName, String action, Map<String, Object> params, int maxRetries) {
        return delegate.executeWithRetry(scriptName, action, params, maxRetries);
    }

    /**
     * @deprecated 使用 {@link PythonScriptInvoker#executeAsMap(String, String, Map)} 替代
     */
    @Deprecated
    public Map<String, Object> executeAsMap(String scriptName, String action, Map<String, Object> params) {
        return delegate.executeAsMap(scriptName, action, params);
    }

    /**
     * @deprecated 使用 {@link PythonScriptInvoker#isPythonAvailable()} 替代
     */
    @Deprecated
    public boolean isPythonAvailable() {
        return delegate.isPythonAvailable();
    }

    /**
     * @deprecated 使用 {@link PythonScriptInvoker#shutdown()} 替代
     */
    @Deprecated
    public void shutdown() {
        delegate.shutdown();
    }
}
