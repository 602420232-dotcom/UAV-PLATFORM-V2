import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'uav_audit_logs_v1'
const MAX_LOGS = 500

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
  } catch (e) {
    return []
  }
}

function saveToStorage(logs) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(logs))
  } catch (e) {
    console.warn('[AUDIT] 持久化失败:', e)
  }
}

export const useAuditStore = defineStore('audit', () => {
  const logs = ref(loadFromStorage())
  const currentUser = ref('anonymous')
  const currentRole = ref('anonymous')

  const recent = computed(() => getRecent(20))

  function setCurrentUser(user, role) {
    currentUser.value = user || 'anonymous'
    currentRole.value = role || 'anonymous'
  }

  function addLog(entry) {
    const fullEntry = {
      id: entry.id || `audit_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      user: entry.user || currentUser.value,
      role: entry.role || currentRole.value,
      action: entry.action || 'OTHER',
      target: entry.target || '-',
      detail: entry.detail || '',
      level: entry.level || 'info',
      timestamp: entry.timestamp || new Date().toISOString(),
      ip: entry.ip || 'local'
    }
    logs.value.push(fullEntry)
    if (logs.value.length > MAX_LOGS) {
      logs.value = logs.value.slice(logs.value.length - MAX_LOGS)
    }
    saveToStorage(logs.value)
    return fullEntry
  }

  function clearLogs() {
    logs.value = []
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch (e) {
      console.warn('[AUDIT] 清空失败:', e)
    }
  }

  function getRecent(limit = 20) {
    if (!limit || limit <= 0) return []
    return logs.value.slice(-limit).reverse()
  }

  function exportLogs(format = 'json') {
    const data = logs.value
    let content = ''
    let mime = 'text/plain'
    let filename = `audit-logs-${new Date().toISOString().replace(/[:.]/g, '-')}`

    if (format === 'csv') {
      const header = ['id', 'user', 'role', 'action', 'target', 'detail', 'level', 'timestamp', 'ip']
      const esc = (v) => {
        const s = String(v == null ? '' : v).replace(/"/g, '""')
        return /[",\n]/.test(s) ? `"${s}"` : s
      }
      const rows = data.map(row => header.map(h => esc(row[h])).join(','))
      content = [header.join(','), ...rows].join('\n')
      mime = 'text/csv;charset=utf-8'
      filename += '.csv'
    } else {
      content = JSON.stringify(data, null, 2)
      mime = 'application/json;charset=utf-8'
      filename += '.json'
    }

    try {
      const blob = new Blob(['\ufeff' + content], { type: mime })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 0)
      return true
    } catch (e) {
      console.warn('[AUDIT] 导出失败:', e)
      return false
    }
  }

  function filterByAction(action) {
    return logs.value.filter(log => log.action === action)
  }

  return {
    logs,
    currentUser,
    currentRole,
    recent,
    setCurrentUser,
    addLog,
    clearLogs,
    getRecent,
    exportLogs,
    filterByAction
  }
})

export default useAuditStore
