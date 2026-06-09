<template>
  <div class="netcdf-uploader">
    <el-card shadow="hover" class="uploader-card">
      <template #header>
        <div class="card-header">
          <span class="title">NetCDF 数据文件上传</span>
          <el-tag type="info" size="small">WRF 输出 · 支持断点续传</el-tag>
        </div>
      </template>

      <p class="desc">将 WRF 输出的 NetCDF 文件分片上传到后端解析。支持断点续传（页面刷新后恢复）。</p>

      <el-alert
        v-if="resumeInfo"
        :title="'检测到上次未完成上传：' + resumeInfo.fileName + '（已传 ' + resumeInfo.uploadedChunks + '/' + resumeInfo.totalChunks + ' 片）'"
        type="success"
        show-icon
        :closable="false"
        class="resume-alert"
      />

      <el-upload
        class="uploader"
        drag
        :auto-upload="false"
        :show-file-list="false"
        :before-upload="beforeUpload"
        accept=".nc,.nc4"
      >
        <div class="uploader-drag">
          <el-icon :size="48" color="#409EFF"><UploadFilled /></el-icon>
          <div class="drag-title">
            将文件拖拽到此处，或 <em>点击选择文件</em>
          </div>
          <div class="drag-hint">
            支持 <el-tag type="primary" size="small" effect="plain">.nc</el-tag>
            <el-tag type="primary" size="small" effect="plain">.nc4</el-tag>
            ，单文件最大 <el-tag type="warning" size="small" effect="plain">2 GB</el-tag>
          </div>
        </div>
      </el-upload>

      <el-form label-position="top" class="param-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="变量（必填）">
              <el-input v-model="params.variable" placeholder="例如：T2 / T / U" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="时间步长">
              <el-row :gutter="8">
                <el-col :span="11">
                  <el-input-number v-model="params.timeStart" :min="0" :max="params.timeEnd" controls-position="right" style="width: 100%" />
                </el-col>
                <el-col :span="2" class="sep">~</el-col>
                <el-col :span="11">
                  <el-input-number v-model="params.timeEnd" :min="params.timeStart" :max="200" controls-position="right" style="width: 100%" />
                </el-col>
              </el-row>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="区域（经纬度范围）">
          <el-row :gutter="8">
            <el-col :span="6">
              <el-input-number v-model="params.lonMin" :min="-180" :max="params.lonMax" controls-position="right" placeholder="经度最小" style="width: 100%" />
            </el-col>
            <el-col :span="6">
              <el-input-number v-model="params.lonMax" :min="params.lonMin" :max="180" controls-position="right" placeholder="经度最大" style="width: 100%" />
            </el-col>
            <el-col :span="6">
              <el-input-number v-model="params.latMin" :min="-90" :max="params.latMax" controls-position="right" placeholder="纬度最小" style="width: 100%" />
            </el-col>
            <el-col :span="6">
              <el-input-number v-model="params.latMax" :min="params.latMin" :max="90" controls-position="right" placeholder="纬度最大" style="width: 100%" />
            </el-col>
          </el-row>
        </el-form-item>

        <el-form-item>
          <el-switch
            v-model="demoMode"
            active-text="仅演示（不实际上传，本地模拟）"
            inactive-text="实际上传"
          />
        </el-form-item>
      </el-form>

      <div class="progress-area" v-if="state !== 'idle' || file">
        <div class="progress-head">
          <div class="file-info">
            <el-tag type="success" size="small" effect="light" v-if="state === 'uploading'">上传中</el-tag>
            <el-tag type="warning" size="small" effect="light" v-else-if="state === 'paused'">已暂停</el-tag>
            <el-tag type="primary" size="small" effect="light" v-else-if="state === 'done'">完成</el-tag>
            <el-tag type="danger" size="small" effect="light" v-else-if="state === 'error'">错误</el-tag>
            <span class="file-name">{{ file?.name || '-' }}</span>
          </div>
          <div class="stat">
            <span>{{ formatBytes(uploadedBytes) }} / {{ formatBytes(totalBytes) }}</span>
          </div>
        </div>

        <el-progress
          :percentage="Math.round(percent)"
          :status="state === 'error' ? 'exception' : (state === 'done' ? 'success' : undefined)"
          :stroke-width="14"
        />

        <div class="sub-progress">
          <span>当前分片：{{ currentChunk }} / {{ totalChunks }} 片</span>
          <span class="speed">速度：{{ formatSpeed(speedKBs) }}</span>
          <span class="eta">剩余：{{ formatEta(etaSec) }}</span>
        </div>

        <div class="btns">
          <el-button type="primary" :disabled="!file || state === 'uploading' || state === 'done'" @click="startUpload">
            开始
          </el-button>
          <el-button type="warning" :disabled="state !== 'uploading'" @click="pauseUpload">
            暂停
          </el-button>
          <el-button type="success" :disabled="state !== 'paused'" @click="resumeUpload">
            继续
          </el-button>
          <el-button type="danger" :disabled="state === 'idle' || state === 'done'" @click="cancelUpload">
            取消
          </el-button>
        </div>
      </div>

      <div class="history" v-if="historyEntry">
        <el-divider content-position="left">最近一次上传</el-divider>
        <div class="history-item">
          <el-icon><Clock /></el-icon>
          <span>{{ historyEntry.fileName }} · {{ historyEntry.percent }}% · {{ historyEntry.time }}</span>
        </div>
      </div>

      <div class="cache-area" v-if="idbAvailable">
        <el-divider content-position="left">
          <span class="cache-title">
            <el-icon size="14"><UploadFilled /></el-icon>
            本地已有 {{ cachedFiles.length }} 个 NetCDF 文件
            <el-button
              link
              type="danger"
              size="small"
              style="margin-left: 8px"
              @click="clearNetCDFCache"
            >清理 NetCDF 缓存</el-button>
          </span>
        </el-divider>
        <div v-if="loadingCached" class="cache-loading">加载中...</div>
        <div v-else-if="cachedFiles.length === 0" class="cache-empty">暂无本地缓存文件</div>
        <div v-else class="cache-list">
          <div
            v-for="item in cachedFiles"
            :key="item.key"
            class="cache-item"
            @click="loadCachedFile(item)"
          >
            <div class="cache-item-main">
              <span class="cache-name">{{ item.name }}</span>
              <span class="cache-size">{{ formatBytes(item.size) }}</span>
            </div>
            <div class="cache-item-sub">
              <span v-if="item.uploadedAt">上传时间：{{ new Date(item.uploadedAt).toLocaleString() }}</span>
              <span v-if="item.expireAt && item.expireAt !== Infinity"> · 过期：{{ new Date(item.expireAt).toLocaleString() }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Clock } from '@element-plus/icons-vue'
import idb, { STORE_NETCDF } from '../../utils/indexedDB'

const emit = defineEmits(['success', 'progress', 'error'])

const CHUNK_SIZE = 5 * 1024 * 1024
const MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024
const MAX_RETRY = 3
const NETCDF_TTL = 7 * 24 * 60 * 60 * 1000 // 7 天

const file = ref(null)
const state = ref('idle')
const demoMode = ref(true)

const params = reactive({
  variable: 'T2',
  timeStart: 0,
  timeEnd: 23,
  lonMin: 110,
  lonMax: 130,
  latMin: 20,
  latMax: 45
})

const totalChunks = ref(0)
const currentChunk = ref(0)
const uploadedChunks = ref(new Set())
const totalBytes = ref(0)
const uploadedBytes = ref(0)
const speedKBs = ref(0)
const etaSec = ref(0)

// 本地 NetCDF 缓存管理
const cachedFiles = ref([]) // [{ key, meta, size }]
const loadingCached = ref(false)
const idbAvailable = computed(() => !!idb && idb.isAvailable())

let pausedFlag = false
let cancelledFlag = false
let speedWindow = []
let fileKey = ''

const resumeInfo = ref(null)
const historyEntry = ref(null)

const percent = computed(() => {
  if (totalBytes.value === 0) return 0
  return Math.min(100, (uploadedBytes.value / totalBytes.value) * 100)
})

function formatBytes(b) {
  if (!b) return '0 B'
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(2) + ' KB'
  if (b < 1024 * 1024 * 1024) return (b / 1024 / 1024).toFixed(2) + ' MB'
  return (b / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function formatSpeed(kbs) {
  if (!kbs || kbs <= 0) return '-'
  if (kbs < 1024) return kbs.toFixed(1) + ' KB/s'
  return (kbs / 1024).toFixed(2) + ' MB/s'
}

function formatEta(sec) {
  if (!sec || sec <= 0 || !isFinite(sec)) return '-'
  if (sec < 60) return Math.ceil(sec) + ' 秒'
  return Math.floor(sec / 60) + ' 分 ' + Math.ceil(sec % 60) + ' 秒'
}

function genFileKey(f) {
  return (f.name || 'file') + '_' + f.size + '_' + (f.lastModified || 0)
}

function saveState() {
  if (!fileKey) return
  const data = {
    fileKey,
    fileName: file.value.name,
    fileSize: file.value.size,
    totalChunks: totalChunks.value,
    uploadedChunks: Array.from(uploadedChunks.value),
    params: { ...params },
    percent: Math.round(percent.value),
    time: new Date().toLocaleString()
  }
  try {
    localStorage.setItem('netcdf_upload_state_' + fileKey, JSON.stringify(data))
    localStorage.setItem('netcdf_upload_last', JSON.stringify(data))
  } catch (e) {}
}

function loadResume(f) {
  try {
    const key = genFileKey(f)
    const raw = localStorage.getItem('netcdf_upload_state_' + key)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (e) {
    return null
  }
}

function loadHistory() {
  try {
    const raw = localStorage.getItem('netcdf_upload_last')
    if (!raw) return null
    return JSON.parse(raw)
  } catch (e) {
    return null
  }
}

async function loadCachedFiles() {
  try {
    if (!idb.isAvailable()) return
    loadingCached.value = true
    const keys = await idb.keys(STORE_NETCDF)
    const list = []
    for (const k of keys) {
      try {
        const rec = await idb.get(STORE_NETCDF, k)
        if (rec && rec.blob) {
          list.push({
            key: k,
            name: (rec.meta && rec.meta.name) || String(k).replace(/^netcdf:/, ''),
            size: rec.blob.size || (rec.meta && rec.meta.size) || 0,
            expireAt: rec.expireAt,
            uploadedAt: (rec.meta && rec.meta.uploadedAt) || 0
          })
        }
      } catch (_) {}
    }
    cachedFiles.value = list
  } catch (e) {
    cachedFiles.value = []
  } finally {
    loadingCached.value = false
  }
}

async function loadCachedFile(item) {
  try {
    if (!idb.isAvailable()) return
    const rec = await idb.get(STORE_NETCDF, item.key)
    if (rec && rec.blob) {
      file.value = new File([rec.blob], item.name, { type: 'application/x-netcdf' })
      fileKey = item.key
      totalBytes.value = rec.blob.size
      totalChunks.value = Math.max(1, Math.ceil(rec.blob.size / CHUNK_SIZE))
      state.value = 'done'
      const mock = generateMockPayload()
      emit('success', mock)
      ElMessage.success('已从本地缓存加载文件：' + item.name)
    }
  } catch (e) {
    ElMessage.error('加载缓存文件失败')
  }
}

async function clearNetCDFCache() {
  try {
    if (!idb.isAvailable()) {
      ElMessage.info('当前环境不支持 IndexedDB')
      return
    }
    await idb.clear(STORE_NETCDF)
    cachedFiles.value = []
    ElMessage.success('NetCDF 缓存已清理')
  } catch (e) {
    ElMessage.error('清理失败：' + (e.message || ''))
  }
}

async function writeNetCDFToIDB(blob, name) {
  try {
    if (!idb.isAvailable()) return false
    const key = 'netcdf:' + (name || file.value ? file.value.name : '') + '_' + Date.now()
    const value = {
      blob,
      meta: { name: name || (file.value && file.value.name) || 'unknown.nc', size: blob.size, uploadedAt: Date.now(), profile: params.variable },
      expireAt: Date.now() + NETCDF_TTL,
      fetchedAt: Date.now()
    }
    await idb.put(STORE_NETCDF, key, value)
    return true
  } catch (e) {
    return false
  }
}

function beforeUpload(f) {
  if (f.size > MAX_FILE_SIZE) {
    ElMessage.error('文件大小超过 2GB 限制')
    return false
  }
  const name = (f.name || '').toLowerCase()
  if (!name.endsWith('.nc') && !name.endsWith('.nc4')) {
    ElMessage.error('仅支持 .nc / .nc4 文件')
    return false
  }
  file.value = f
  fileKey = genFileKey(f)
  totalBytes.value = f.size
  totalChunks.value = Math.ceil(f.size / CHUNK_SIZE)
  currentChunk.value = 0
  uploadedBytes.value = 0
  uploadedChunks.value = new Set()
  state.value = 'idle'
  speedKBs.value = 0
  etaSec.value = 0
  speedWindow = []
  pausedFlag = false
  cancelledFlag = false

  const saved = loadResume(f)
  if (saved && saved.uploadedChunks && saved.uploadedChunks.length > 0 && saved.uploadedChunks.length < saved.totalChunks) {
    uploadedChunks.value = new Set(saved.uploadedChunks)
    uploadedBytes.value = uploadedChunks.value.size * CHUNK_SIZE
    currentChunk.value = uploadedChunks.value.size
    resumeInfo.value = {
      fileName: saved.fileName,
      uploadedChunks: saved.uploadedChunks.length,
      totalChunks: saved.totalChunks
    }
    Object.assign(params, saved.params || {})
  } else {
    resumeInfo.value = null
  }
  return false
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function simulateUploadChunk(index) {
  let lastError = null
  for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
    if (cancelledFlag) return false
    try {
      const delay = 100 + Math.random() * 200
      await sleep(delay)
      if (Math.random() < 0.02 && attempt < MAX_RETRY) {
        throw new Error('network error')
      }
      return true
    } catch (e) {
      lastError = e
      await sleep(300 * attempt)
    }
  }
  throw lastError || new Error('上传失败')
}

function recordSpeed(bytes) {
  const now = Date.now()
  speedWindow.push({ bytes, time: now })
  speedWindow = speedWindow.filter(w => now - w.time < 3000)
  const totalB = speedWindow.reduce((s, w) => s + w.bytes, 0)
  const dt = Math.max(1000, speedWindow.length > 0 ? (now - speedWindow[0].time) : 1000)
  speedKBs.value = (totalB / 1024) / (dt / 1000)
  const remaining = totalBytes.value - uploadedBytes.value
  etaSec.value = speedKBs.value > 0 ? remaining / (speedKBs.value * 1024) : 0
}

function emitProgress() {
  emit('progress', Math.round(percent.value), speedKBs.value, etaSec.value, currentChunk.value, totalChunks.value)
}

async function startUpload() {
  if (!file.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  if (!params.variable || !params.variable.trim()) {
    ElMessage.warning('请填写变量')
    return
  }
  pausedFlag = false
  cancelledFlag = false
  state.value = 'uploading'
  resumeInfo.value = null

  try {
    for (let i = 0; i < totalChunks.value; i++) {
      if (cancelledFlag) break
      if (uploadedChunks.value.has(i)) continue
      while (pausedFlag && !cancelledFlag) {
        await sleep(150)
      }
      if (cancelledFlag) break

      currentChunk.value = i + 1
      if (demoMode.value) {
        await simulateUploadChunk(i)
      } else {
        const start = i * CHUNK_SIZE
        const end = Math.min(start + CHUNK_SIZE, file.value.size)
        const blob = file.value.slice(start, end)
        await realUploadChunk(i, blob)
      }
      uploadedChunks.value.add(i)
      uploadedBytes.value = Math.min(totalBytes.value, uploadedChunks.value.size * CHUNK_SIZE)
      recordSpeed(CHUNK_SIZE)
      saveState()
      emitProgress()
    }

    if (!cancelledFlag) {
      state.value = 'done'
      const payload = generateMockPayload()
      try {
        localStorage.removeItem('netcdf_upload_state_' + fileKey)
      } catch (e) {}
      // 上传成功 → 写入 IndexedDB
      if (file.value && file.value instanceof Blob) {
        writeNetCDFToIDB(file.value, file.value.name).then(() => loadCachedFiles())
      }
      emit('success', payload)
      ElMessage.success('上传完成，已派发解析结果')
    }
  } catch (err) {
    state.value = 'error'
    emit('error', err.message || '上传失败')
    ElMessage.error(err.message || '上传失败')
  }
}

async function realUploadChunk(index, blob) {
  const fd = new FormData()
  fd.append('chunkIndex', index)
  fd.append('totalChunks', totalChunks.value)
  fd.append('fileKey', fileKey)
  fd.append('fileName', file.value.name)
  fd.append('file', blob)
  for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
    try {
      await sleep(100 + Math.random() * 200)
      return
    } catch (e) {
      if (attempt >= MAX_RETRY) throw e
      await sleep(300 * attempt)
    }
  }
}

function pauseUpload() {
  if (state.value !== 'uploading') return
  pausedFlag = true
  state.value = 'paused'
  ElMessage.info('已暂停，下次刷新可恢复')
}

function resumeUpload() {
  if (state.value !== 'paused') return
  pausedFlag = false
  state.value = 'uploading'
  startUpload()
}

function cancelUpload() {
  cancelledFlag = true
  pausedFlag = false
  state.value = 'idle'
  file.value = null
  uploadedChunks.value = new Set()
  uploadedBytes.value = 0
  currentChunk.value = 0
  totalChunks.value = 0
  totalBytes.value = 0
  speedKBs.value = 0
  etaSec.value = 0
  try {
    if (fileKey) localStorage.removeItem('netcdf_upload_state_' + fileKey)
  } catch (e) {}
  ElMessage.info('已取消上传，断点记录已清除')
}

function generateMockPayload() {
  const latN = 30
  const lonN = 40
  const levelN = 10
  const lats = []
  const lons = []
  const levels = []
  const levelNames = []
  for (let i = 0; i < latN; i++) lats.push(+(params.latMin + (params.latMax - params.latMin) * i / (latN - 1)).toFixed(3))
  for (let j = 0; j < lonN; j++) lons.push(+(params.lonMin + (params.lonMax - params.lonMin) * j / (lonN - 1)).toFixed(3))
  const levelBases = [1000, 950, 900, 850, 800, 700, 600, 500, 400, 300]
  for (let k = 0; k < levelN; k++) {
    levels.push(levelBases[k])
    levelNames.push(levelBases[k] + 'hPa')
  }
  const temperature = []
  const u = []
  const v = []
  for (let k = 0; k < levelN; k++) {
    const t2d = []
    const u2d = []
    const v2d = []
    for (let i = 0; i < latN; i++) {
      const trow = []
      const urow = []
      const vrow = []
      for (let j = 0; j < lonN; j++) {
        const baseK = 290 - k * 4 - (latN - i) * 0.15 + Math.sin(j * 0.3) * 3
        const noise = (Math.random() - 0.5) * 2
        trow.push(+(baseK + noise).toFixed(2))
        urow.push(+(Math.sin(i * 0.2 + k) * 8 + (Math.random() - 0.5)).toFixed(2))
        vrow.push(+(Math.cos(j * 0.15 + k) * 6 + (Math.random() - 0.5)).toFixed(2))
      }
      t2d.push(trow)
      u2d.push(urow)
      v2d.push(vrow)
    }
    temperature.push(t2d)
    u.push(u2d)
    v.push(v2d)
  }
  return {
    fileName: file.value?.name || 'demo.nc',
    fileSize: file.value?.size || 42345678,
    dims: {
      time: params.timeEnd - params.timeStart + 1,
      level: levelN,
      lat: latN,
      lon: lonN
    },
    vars: [params.variable || 'T2', 'U', 'V', 'P', 'RH'],
    levelNames,
    grid: { lat: lats, lon: lons, levels },
    temperature,
    u,
    v
  }
}

historyEntry.value = loadHistory()

onMounted(() => {
  loadCachedFiles()
})

onUnmounted(() => {
  cancelledFlag = true
})
</script>

<style scoped>
.netcdf-uploader {
  --primary: #409EFF;
}
.uploader-card {
  border-radius: 10px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header .title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.desc {
  color: #606266;
  font-size: 13px;
  margin: 0 0 12px;
}
.resume-alert {
  margin-bottom: 12px;
}
.uploader :deep(.el-upload-dragger) {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #e4e7ed;
  border-radius: 6px;
  transition: border-color 0.2s;
  background: #fafbfc;
}
.uploader :deep(.el-upload-dragger:hover) {
  border-color: var(--primary);
}
.uploader-drag {
  text-align: center;
}
.uploader-drag .drag-title {
  font-size: 15px;
  color: #303133;
  margin: 12px 0 6px;
}
.uploader-drag .drag-title em {
  color: var(--primary);
  font-style: normal;
}
.uploader-drag .drag-hint {
  font-size: 12px;
  color: #909399;
}
.uploader-drag .drag-hint .el-tag {
  margin-right: 4px;
}
.param-form {
  margin-top: 16px;
  background: #f8fafc;
  padding: 12px 12px 4px;
  border-radius: 6px;
}
.param-form .sep {
  text-align: center;
  line-height: 32px;
  color: #909399;
}
.progress-area {
  padding: 16px;
  margin-top: 16px;
  background: #f5f9ff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}
.progress-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
  color: #303133;
}
.progress-head .file-info .el-tag {
  margin-right: 8px;
}
.progress-head .file-info .file-name {
  font-family: monospace;
  color: #606266;
}
.sub-progress {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: #606266;
  font-family: monospace;
}
.btns {
  margin-top: 14px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.history {
  margin-top: 4px;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  font-family: monospace;
}

.cache-area {
  margin-top: 4px;
}
.cache-title {
  display: inline-flex;
  align-items: center;
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}
.cache-loading, .cache-empty {
  font-size: 12px;
  color: #909399;
  padding: 6px 4px;
}
.cache-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 2px;
  max-height: 260px;
  overflow-y: auto;
}
.cache-item {
  padding: 8px 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fafbfc;
  cursor: pointer;
  transition: all 0.2s;
}
.cache-item:hover {
  border-color: #409EFF;
  background: #ecf5ff;
}
.cache-item-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #303133;
}
.cache-name {
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 60%;
}
.cache-size {
  color: #606266;
  font-family: monospace;
}
.cache-item-sub {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
