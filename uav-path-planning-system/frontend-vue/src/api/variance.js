import api from './index'

const BASE = '/api/v1/variance'

export function computeVariance(params) {
  return api.post(`${BASE}/compute`, params)
}

export function getVarianceMatrix(shape, config) {
  return api.post(`${BASE}/variance-matrix`, { shape, config })
}

export function adaptiveVariance(params) {
  return api.post(`${BASE}/adaptive`, params)
}

export function getVarianceParams() {
  return api.get(`${BASE}/params`)
}

export function setVarianceParams(params) {
  return api.post(`${BASE}/params`, params)
}

export function resetVarianceOptimizer() {
  return api.post(`${BASE}/reset`)
}

export function getVarianceStatus() {
  return api.get(`${BASE}/status`)
}
