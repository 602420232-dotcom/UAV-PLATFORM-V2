/* eslint-disable no-undef */
/**
 * UAV Path Planner - IndexedDB 封装
 *
 * 提供原生 IndexedDB API 的 Promise 封装，用于存储：
 *   - netcdf_cache      : 上传的 NetCDF 文件（Blob），key = hash / 文件名
 *   - cesium_tiles      : Cesium / Leaflet 瓦片 Blob，key = tile URL 或 "z/x/y"
 *   - task_offline_packages : 任务离线数据包（JSON），key = taskId
 *
 * 统一能力：
 *   - initDB()          : 打开 / 升级数据库
 *   - put/get/del/keys  : 基础 CRUD
 *   - clear / clearAll  : 清理
 *   - isAvailable()     : 判断运行环境是否可用
 *   - getStorageInfo()  : 使用 navigator.storage.estimate() 获取配额
 *   - cleanExpired()    : 遍历指定 store，删除 expireAt < now 的记录
 *
 * 顶层 try/catch 兼容：
 *   - SSR / Node 环境
 *   - indexedDB 未定义（隐私模式、旧浏览器）
 */

const DB_NAME = 'UAV_PATH_PLANNER_CACHE_V1'
const DB_VERSION = 1

const STORE_NETCDF = 'netcdf_cache'
const STORE_TILES = 'cesium_tiles'
const STORE_OFFLINE = 'task_offline_packages'

const ALL_STORES = [STORE_NETCDF, STORE_TILES, STORE_OFFLINE]

let _dbPromise = null

function _hasIndexedDB() {
  try {
    return (
      typeof indexedDB !== 'undefined' &&
      typeof IDBKeyRange !== 'undefined'
    )
  } catch (e) {
    return false
  }
}

function _openDB() {
  return new Promise((resolve, reject) => {
    if (!_hasIndexedDB()) {
      reject(new Error('[IndexedDB] 当前环境不支持 IndexedDB'))
      return
    }
    let req
    try {
      req = indexedDB.open(DB_NAME, DB_VERSION)
    } catch (e) {
      reject(e)
      return
    }

    req.onupgradeneeded = (evt) => {
      const db = evt.target.result
      const existing = new Set(db.objectStoreNames)

      if (!existing.has(STORE_NETCDF)) {
        db.createObjectStore(STORE_NETCDF, { keyPath: 'key' })
      }
      if (!existing.has(STORE_TILES)) {
        db.createObjectStore(STORE_TILES, { keyPath: 'key' })
      }
      if (!existing.has(STORE_OFFLINE)) {
        db.createObjectStore(STORE_OFFLINE, { keyPath: 'key' })
      }
    }

    req.onsuccess = (evt) => {
      const db = evt.target.result
      try {
        db.onversionchange = () => {
          try { db.close() } catch (_) {}
          _dbPromise = null
        }
      } catch (_) {}
      if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.DEV) {
        console.info('[IndexedDB] init', DB_NAME, 'v' + DB_VERSION)
      }
      resolve(db)
    }

    req.onerror = (evt) => {
      const err = (evt.target && evt.target.error) || new Error('[IndexedDB] open error')
      _dbPromise = null
      reject(err)
    }

    req.onblocked = () => {
      reject(new Error('[IndexedDB] 其他标签页正在使用旧版本数据库，请关闭后重试'))
    }
  })
}

export function initDB() {
  if (!_hasIndexedDB()) {
    return Promise.reject(new Error('[IndexedDB] 当前环境不支持 IndexedDB'))
  }
  if (!_dbPromise) {
    _dbPromise = _openDB().catch((err) => {
      _dbPromise = null
      throw err
    })
  }
  return _dbPromise
}

export function isAvailable() {
  try {
    if (!_hasIndexedDB()) return false
    // 简单写权限检查：部分隐私模式下 indexedDB.open 会立刻失败
    // 这里不做真的 open 探测，避免影响性能
    return true
  } catch (e) {
    return false
  }
}

export async function getStorageInfo() {
  try {
    if (typeof navigator === 'undefined' || !navigator.storage || !navigator.storage.estimate) {
      return { quota: 0, usage: 0, usagePercent: 0 }
    }
    const info = await navigator.storage.estimate()
    const quota = Number(info.quota) || 0
    const usage = Number(info.usage) || 0
    const usagePercent = quota > 0 ? +((usage / quota) * 100).toFixed(2) : 0
    return { quota, usage, usagePercent }
  } catch (e) {
    return { quota: 0, usage: 0, usagePercent: 0, error: e && e.message }
  }
}

function _withStore(storeName, mode, executor) {
  return initDB().then((db) => {
    return new Promise((resolve, reject) => {
      let tx
      try {
        tx = db.transaction(storeName, mode)
      } catch (e) {
        reject(e)
        return
      }
      const store = tx.objectStore(storeName)
      let result
      try {
        result = executor(store, resolve, reject)
      } catch (e) {
        reject(e)
        return
      }
      tx.oncomplete = () => resolve(result)
      tx.onerror = (evt) => {
        const err = (evt.target && evt.target.error) || new Error('[IndexedDB] transaction error')
        reject(err)
      }
      tx.onabort = (evt) => {
        const err = (evt.target && evt.target.error) || new Error('[IndexedDB] transaction aborted')
        reject(err)
      }
    })
  })
}

export function put(storeName, key, value) {
  if (!_hasIndexedDB()) return Promise.reject(new Error('[IndexedDB] not available'))
  return _withStore(storeName, 'readwrite', (store, resolve) => {
    const record = { key, value, updatedAt: Date.now() }
    const req = store.put(record)
    req.onsuccess = () => resolve(record)
    req.onerror = (evt) => { throw (evt.target && evt.target.error) || new Error('put failed') }
  })
}

export function get(storeName, key) {
  if (!_hasIndexedDB()) return Promise.reject(new Error('[IndexedDB] not available'))
  return _withStore(storeName, 'readonly', (store, resolve) => {
    const req = store.get(key)
    req.onsuccess = (evt) => {
      const rec = evt.target.result
      resolve(rec ? rec.value : undefined)
    }
    req.onerror = (evt) => { throw (evt.target && evt.target.error) || new Error('get failed') }
  })
}

export function del(storeName, key) {
  if (!_hasIndexedDB()) return Promise.reject(new Error('[IndexedDB] not available'))
  return _withStore(storeName, 'readwrite', (store, resolve) => {
    const req = store.delete(key)
    req.onsuccess = () => resolve(true)
    req.onerror = (evt) => { throw (evt.target && evt.target.error) || new Error('del failed') }
  })
}

export function keys(storeName) {
  if (!_hasIndexedDB()) return Promise.reject(new Error('[IndexedDB] not available'))
  return _withStore(storeName, 'readonly', (store, resolve) => {
    const req = store.getAllKeys()
    req.onsuccess = (evt) => resolve(Array.isArray(evt.target.result) ? evt.target.result : [])
    req.onerror = (evt) => { throw (evt.target && evt.target.error) || new Error('keys failed') }
  })
}

export function clear(storeName) {
  if (!_hasIndexedDB()) return Promise.reject(new Error('[IndexedDB] not available'))
  return _withStore(storeName, 'readwrite', (store, resolve) => {
    const req = store.clear()
    req.onsuccess = () => resolve(true)
    req.onerror = (evt) => { throw (evt.target && evt.target.error) || new Error('clear failed') }
  })
}

export async function clearAll() {
  if (!_hasIndexedDB()) return Promise.reject(new Error('[IndexedDB] not available'))
  await Promise.all(ALL_STORES.map((s) => clear(s).catch(() => {})))
  return true
}

/**
 * 清理指定 store 中已经过期的记录（value.expireAt < now）。
 * 只处理 value 为对象且存在 expireAt 字段的情况，其他记录保留。
 * @returns {Promise<number>} 被删除的条数
 */
export function cleanExpired(storeName) {
  if (!_hasIndexedDB()) return Promise.reject(new Error('[IndexedDB] not available'))
  return initDB().then((db) => {
    return new Promise((resolve, reject) => {
      let tx
      try {
        tx = db.transaction(storeName, 'readwrite')
      } catch (e) {
        reject(e)
        return
      }
      const store = tx.objectStore(storeName)
      let removed = 0
      const cursorReq = store.openCursor()
      cursorReq.onsuccess = (evt) => {
        const cursor = evt.target.result
        if (!cursor) return
        const rec = cursor.value
        const val = rec && rec.value
        if (val && typeof val === 'object' && typeof val.expireAt === 'number') {
          if (val.expireAt < Date.now()) {
            removed += 1
            cursor.delete()
          }
        }
        cursor.continue()
      }
      cursorReq.onerror = (evt) => {
        reject((evt.target && evt.target.error) || new Error('cleanExpired failed'))
      }
      tx.oncomplete = () => resolve(removed)
      tx.onerror = (evt) => reject((evt.target && evt.target.error) || new Error('cleanExpired tx error'))
    })
  })
}

/**
 * 便捷工具：为某个 value 生成带 meta 的包装对象（供调用方在 put 之前组装）。
 * @param {Blob|any} payload - 主数据（通常是 Blob）
 * @param {object} meta      - { name?, size?, profile?, ... }
 * @param {number} ttlMs     - 存活时间（毫秒），不传则永久
 */
export function withMeta(payload, meta = {}, ttlMs) {
  const now = Date.now()
  const value = {
    blob: payload && (payload instanceof Blob || payload.type) ? payload : undefined,
    json: payload && !(payload instanceof Blob) && typeof payload === 'object' ? payload : undefined,
    meta: Object.assign({ uploadedAt: now }, meta || {}),
    expireAt: ttlMs ? now + ttlMs : Infinity
  }
  if (value.blob === undefined) delete value.blob
  if (value.json === undefined) delete value.json
  return value
}

const indexedDBUtils = {
  DB_NAME,
  DB_VERSION,
  STORE_NETCDF,
  STORE_TILES,
  STORE_OFFLINE,
  initDB,
  isAvailable,
  getStorageInfo,
  put,
  get,
  del,
  keys,
  clear,
  clearAll,
  cleanExpired,
  withMeta
}

export { DB_NAME, DB_VERSION, STORE_NETCDF, STORE_TILES, STORE_OFFLINE }

export default indexedDBUtils
