import { ref, onUnmounted, watch } from 'vue'

/**
 * 自动轮询 composable
 * 提供定时刷新数据的能力，支持条件启停
 *
 * @param {Function} fetchFn - 数据获取函数（async）
 * @param {Object} options
 * @param {number} options.interval - 轮询间隔（毫秒），默认 5000
 * @param {boolean|ref} options.enabled - 是否启用，默认 true
 * @param {boolean} options.immediate - 是否立即执行首次调用，默认 true
 * @returns {{ polling: Ref<boolean>, start: Function, stop: Function }}
 */
export function usePolling(fetchFn, options = {}) {
  const {
    interval = 5000,
    enabled = true,
    immediate = true
  } = options

  const polling = ref(false)
  let timer = null

  const enabledRef = typeof enabled === 'boolean' ? ref(enabled) : enabled

  const start = () => {
    stop()
    polling.value = true
    if (immediate) {
      fetchFn()
    }
    timer = setInterval(() => {
      fetchFn()
    }, interval)
  }

  const stop = () => {
    polling.value = false
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  watch(enabledRef, (val) => {
    if (val) {
      start()
    } else {
      stop()
    }
  }, { immediate: true })

  onUnmounted(() => {
    stop()
  })

  return { polling, start, stop }
}
