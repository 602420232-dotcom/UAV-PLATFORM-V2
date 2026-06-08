import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as weatherApi from '../api/weather'
import { demoData } from '../utils/demoData'

export const useWeatherStore = defineStore('weather', () => {
  const current = ref(null)
  const windField = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchCurrent(lat = 39.9, lng = 116.4) {
    loading.value = true
    error.value = null
    try {
      const res = await weatherApi.getWeatherCurrent(lat, lng)
      const data = res?.data || res
      if (data && typeof data === 'object') {
        current.value = data
        if (data.windField) {
          windField.value = data.windField
        }
      } else {
        current.value = demoData.weather
        windField.value = demoData.weather.windField || []
      }
    } catch (e) {
      error.value = e?.message || '获取气象数据失败'
      current.value = demoData.weather
      windField.value = demoData.weather.windField || []
    } finally {
      loading.value = false
    }
  }

  return {
    current,
    windField,
    loading,
    error,
    fetchCurrent
  }
})
