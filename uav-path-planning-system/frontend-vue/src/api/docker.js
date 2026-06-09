import api from './index'

const BASE = '/v1/docker'

export function getContainers() {
  return api.get(`${BASE}/containers`)
}

export function getContainerById(id) {
  return api.get(`${BASE}/containers/${id}`)
}

export function getHostStats() {
  return api.get(`${BASE}/host/stats`)
}

export function restartContainer(id) {
  return api.post(`${BASE}/containers/${id}/restart`)
}

export function stopContainer(id) {
  return api.post(`${BASE}/containers/${id}/stop`)
}

export function startContainer(id) {
  return api.post(`${BASE}/containers/${id}/start`)
}

export function getContainerLogs(id, params = {}) {
  return api.get(`${BASE}/containers/${id}/logs`, { params })
}

export function getContainerStats(id) {
  return api.get(`${BASE}/containers/${id}/stats`)
}

export function pruneContainers() {
  return api.delete(`${BASE}/containers/prune`)
}