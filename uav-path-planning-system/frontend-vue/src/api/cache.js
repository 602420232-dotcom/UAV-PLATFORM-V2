export {
  cacheStore,
  CACHE_STRATEGIES,
  CACHE_RULES,
  matchStrategy,
  cacheKey,
  invalidateWeather,
  invalidateTask,
  invalidateStatic,
  invalidateAllCache
} from './index'

import idb from '../utils/indexedDB'

// 便捷方法
export const invalidate = (tag) => {
  cacheStore.clearByTag(tag)
  cacheStore.invalidateLarge(tag).catch(() => {})
}

export const getStorageInfo = () => idb.getStorageInfo()

export default { cacheStore, invalidateWeather, invalidateTask, invalidateStatic, invalidateAllCache, invalidate, getStorageInfo }
