import api from './index'

const BASE = '/api/v1/drones'

export function getDrones() {
  return api.get(BASE)
}

export function getDroneById(id) {
  return api.get(`${BASE}/${id}`)
}

export function getDroneStatus(id) {
  return api.get(`${BASE}/${id}/status`)
}

export function getDroneTelemetry(id) {
  return api.get(`${BASE}/${id}/telemetry`)
}
