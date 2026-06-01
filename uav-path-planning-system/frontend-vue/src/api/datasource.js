import api from './index'

export function getDataSources() {
  return api.get('/data-sources')
}

export function getDataSourceById(id) {
  return api.get(`/data-sources/${id}`)
}

export function createDataSource(data) {
  return api.post('/data-sources', data)
}

export function updateDataSource(id, data) {
  return api.put(`/data-sources/${id}`, data)
}

export function deleteDataSource(id) {
  return api.delete(`/data-sources/${id}`)
}

export function testDataSource(id) {
  return api.post(`/data-sources/${id}/test`)
}

export function getDataSourceStatus(id) {
  return api.get(`/data-sources/${id}/status`)
}
