import api from './index'

const BASE = '/v1'

export function getSystemStatus() {
  return api.get(`${BASE}/system/status`)
}

export function getServiceHealth() {
  return api.get(`/actuator/health`)
}

export function getDashboardStats() {
  return api.get(`${BASE}/dashboard`)
}

export function getAlerts() {
  return api.get(`${BASE}/alerts`)
}
