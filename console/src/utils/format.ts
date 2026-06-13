/**
 * 格式化日期时间
 */
export function formatDateTime(value: string | Date | null | undefined): string {
  if (!value) return '-'
  const date = typeof value === 'string' ? new Date(value) : value
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  const s = String(date.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${min}:${s}`
}

/**
 * 格式化日期（不含时间）
 */
export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return '-'
  const date = typeof value === 'string' ? new Date(value) : value
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/**
 * 格式化数字（千分位）
 */
export function formatNumber(value: number | null | undefined): string {
  if (value == null) return '-'
  return value.toLocaleString('zh-CN')
}

/**
 * 截断字符串
 */
export function truncate(value: string, length: number): string {
  if (!value) return ''
  if (value.length <= length) return value
  return value.slice(0, length) + '...'
}

/**
 * API Key 脱敏显示
 */
export function maskApiKey(key: string): string {
  if (!key || key.length <= 8) return key
  return key.slice(0, 4) + '****' + key.slice(-4)
}
