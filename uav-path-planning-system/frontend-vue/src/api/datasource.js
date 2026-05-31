import api from './index'

export function getDataSources() {
  return api.get('/data-sources')
}

export function getDataSourceById(id) {
  return api.get(`/data-sources/${id}`)
}

export function testDataSource(id) {
  return api.post(`/data-sources/${id}/test`)
}

export function getDataSourceStatus(id) {
  return api.get(`/data-sources/${id}/status`)
}
