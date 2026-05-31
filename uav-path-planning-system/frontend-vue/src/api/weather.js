import api from './index'

const BASE = '/api/v1/weather'

export function getWeatherForecast(params) {
  return api.get(`/v1/weather/forecast`, { params })
}

export function getWeatherHeatmap(bounds) {
  return api.post(`/v1/weather/heatmap`, bounds)
}

export function getWeatherAlerts() {
  return api.get(`/v1/weather/alerts`)
}

export function getWeatherCurrent(lat, lng) {
  return api.get(`/v1/weather/current`, { params: { lat, lng } })
}
