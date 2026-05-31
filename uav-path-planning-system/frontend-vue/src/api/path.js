import api from './index'

export function planPath(data) {
  return api.post('/path/plan', data)
}

export function getPathHistory(params) {
  return api.get('/path/history', { params })
}

export function getPathById(id) {
  return api.get(`/path/${id}`)
}

export function getPathRealtime() {
  return api.get('/path/realtime')
}
