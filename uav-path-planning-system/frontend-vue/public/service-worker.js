/* eslint-disable no-restricted-globals */
/**
 * UAV Path Planner - Service Worker
 * 版本：uav-v1.1
 * 功能：
 *   - 对 GET /v1/weather/* 请求做 IndexedDB 读写（命中直接返回 Blob，未命中 fetch 后写回）
 *   - stale-while-revalidate：对 /api/* GET 请求，缓存到 SW cache 并在后台刷新
 *   - install 阶段 skipWaiting，激活阶段 clients.claim 并清理旧 uav-v0 缓存
 */
const SW_VERSION = 'uav-v1.1'
const PRECACHE = `${SW_VERSION}-precache`
const RUNTIME_CACHE = `${SW_VERSION}-runtime`
const OLD_CACHE_RE = /^uav-v0/

// IndexedDB 原生封装（SW 作用域中可用）
const IDB_NAME = 'UAV_PATH_PLANNER_CACHE_V1'
const IDB_STORE = 'cesium_tiles'
const WEATHER_STORE = 'netcdf_cache'
const WEATHER_TTL = 7 * 24 * 60 * 60 * 1000 // 7 天

function openDB() {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('no indexedDB'))
      return
    }
    const req = indexedDB.open(IDB_NAME, 1)
    req.onupgradeneeded = (evt) => {
      const db = evt.target.result
      if (!db.objectStoreNames.contains(IDB_STORE)) db.createObjectStore(IDB_STORE, { keyPath: 'key' })
      if (!db.objectStoreNames.contains(WEATHER_STORE)) db.createObjectStore(WEATHER_STORE, { keyPath: 'key' })
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
    req.onblocked = () => reject(new Error('blocked'))
  })
}

function idbGet(storeName, key) {
  return openDB().then((db) => new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readonly')
    const s = tx.objectStore(storeName)
    const r = s.get(key)
    r.onsuccess = () => resolve(r.result)
    r.onerror = () => reject(r.error)
  })).catch(() => null)
}

function idbPut(storeName, key, value) {
  return openDB().then((db) => new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite')
    const s = tx.objectStore(storeName)
    const r = s.put({ key, value, updatedAt: Date.now() })
    r.onsuccess = () => resolve(true)
    r.onerror = () => reject(r.error)
  })).catch(() => false)
}

function isWeatherRequest(url) {
  return /^https?:\/\/[^/]*\/v1\/weather\//i.test(url) || url.includes('/v1/weather/')
}

function isTileRequest(url) {
  return /tile[s]?\.|openstreetmap\.org|tile.*\.(png|jpg|jpeg|webp)/i.test(url)
}

async function tryServeFromIDB(storeName, requestUrl) {
  const rec = await idbGet(storeName, requestUrl)
  if (!rec || !rec.value || !rec.value.blob) return null
  if (rec.value.expireAt && rec.value.expireAt !== Infinity && rec.value.expireAt < Date.now()) {
    return null
  }
  return new Response(rec.value.blob, {
    status: 200,
    statusText: 'OK (from-IDB)',
    headers: {
      'Content-Type': rec.value.contentType || 'application/octet-stream',
      'X-Cache': 'HIT-IDB',
      'Cache-Control': 'no-cache'
    }
  })
}

async function fetchAndCacheIDB(request, storeName, ttl) {
  try {
    const resp = await fetch(request)
    if (!resp || !resp.ok || resp.status !== 200) return resp
    const clone = resp.clone()
    const blob = await clone.blob()
    const contentType = (resp.headers && resp.headers.get('content-type')) || 'application/octet-stream'
    idbPut(storeName, request.url, {
      blob,
      contentType,
      expireAt: Date.now() + ttl,
      fetchedAt: Date.now()
    }).catch(() => {})
    return resp
  } catch (e) {
    return new Response(JSON.stringify({ error: 'network-error' }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json' }
    })
  }
}

// ===== Install =====
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(PRECACHE).then(() => {
      try { self.skipWaiting() } catch (_) {}
      return Promise.resolve()
    })
  )
})

// ===== Activate =====
self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      caches.keys().then((keys) =>
        Promise.all(
          keys.map((k) => {
            if (k === PRECACHE || k === RUNTIME_CACHE) return Promise.resolve()
            if (OLD_CACHE_RE.test(k) || k.startsWith('uav-')) return caches.delete(k)
            return Promise.resolve()
          })
        )
      ),
      (async () => {
        if (self.clients && self.clients.claim) {
          try { await self.clients.claim() } catch (_) {}
        }
      })()
    ])
  )
})

// ===== Fetch =====
self.addEventListener('fetch', (event) => {
  const req = event.request
  if (!req || req.method !== 'GET') return

  const url = req.url
  if (!url) return

  // 气象 API：IndexedDB 读写
  if (isWeatherRequest(url)) {
    event.respondWith((async () => {
      const fromIdb = await tryServeFromIDB(WEATHER_STORE, url)
      if (fromIdb) return fromIdb
      return fetchAndCacheIDB(req, WEATHER_STORE, WEATHER_TTL)
    })())
    return
  }

  // 瓦片：IndexedDB 读写
  if (isTileRequest(url)) {
    event.respondWith((async () => {
      const fromIdb = await tryServeFromIDB(IDB_STORE, url)
      if (fromIdb) return fromIdb
      return fetchAndCacheIDB(req, IDB_STORE, 30 * 24 * 60 * 60 * 1000)
    })())
    return
  }

  // 其他 GET：stale-while-revalidate（仍使用 SW cache）
  if (url.startsWith(self.location.origin + '/api/') || url.startsWith('/api/')) {
    event.respondWith(
      caches.open(RUNTIME_CACHE).then((cache) =>
        cache.match(req).then((cached) => {
          const fetchPromise = fetch(req).then((resp) => {
            if (resp && resp.ok) cache.put(req, resp.clone()).catch(() => {})
            return resp
          }).catch(() => cached)
          return cached || fetchPromise
        })
      )
    )
  }
})
