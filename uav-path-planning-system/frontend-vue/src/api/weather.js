import api from './index'

const BASE = '/api/v1/weather'

export function getWeatherForecast(params) {
  return api.get(`${BASE}/forecast`, { params })
}

export function getWeatherHeatmap(bounds) {
  return api.post(`${BASE}/heatmap`, bounds)
}

export function getWeatherAlerts() {
  return api.get(`${BASE}/alerts`)
}

export function getWeatherCurrent(lat, lng) {
  return api.get(`${BASE}/current`, { params: { lat, lng } })
}
