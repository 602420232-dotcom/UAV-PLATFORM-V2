import api from './index'

const BASE = '/api/assimilation'

export function executeAssimilation(data) {
  return api.post(`${BASE}/execute`, data)
}

export function getVariance(data) {
  return api.post(`${BASE}/variance`, data)
}

export function batchProcess(data) {
  return api.post(`${BASE}/batch`, data)
}

