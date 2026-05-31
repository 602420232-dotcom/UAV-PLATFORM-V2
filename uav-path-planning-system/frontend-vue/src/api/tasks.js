import api from './index'

const BASE = '/v1/tasks'

export function getTasks(params) {
  return api.get(BASE, { params })
}

export function getTaskById(id) {
  return api.get(`${BASE}/${id}`)
}

export function createTask(data) {
  return api.post(BASE, data)
}

export function updateTask(id, data) {
  return api.put(`${BASE}/${id}`, data)
}

export function getTaskHistory(params) {
  return api.get(`${BASE}/history`, { params })
}
