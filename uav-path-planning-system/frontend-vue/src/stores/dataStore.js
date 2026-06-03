import { defineStore } from 'pinia'
import { ref } from 'vue'
import { demoData, normalizeApiResponse } from '../utils/demoData'
import * as droneApi from '../api/drones'
import * as taskApi from '../api/tasks'
import * as weatherApi from '../api/weather'
import * as dataSourceApi from '../api/datasource'

export const useDataStore = defineStore('data', () => {
  // State
  const drones = ref([])
  const tasks = ref([])
  const historyData = ref([])
  const weatherData = ref(null)
  const windField = ref([])
  const dataSources = ref([])

  const loading = ref({
    drones: false,
    tasks: false,
    history: false,
    weather: false,
    dataSources: false
  })
  const error = ref({
    drones: null,
    tasks: null,
    history: null,
    weather: null,
    dataSources: null
  })
  const useDemo = ref(true)
  const lastApiFailureTime = ref(null)
  const apiAvailable = ref(false)

  // 待取消的请求控制器
  const pendingControllers = new Map()

  // Helper to wrap API calls with fallback
  async function fetchWithFallback(apiFn, demoValue, type) {
    loading.value[type] = true
    error.value[type] = null
    try {
      const controller = new AbortController()
      addController(type, controller)
      const response = await apiFn(controller.signal)
      removeController(type)
      const result = normalizeApiResponse(response)
      if (result && (Array.isArray(result) ? result.length > 0 : true)) {
        useDemo.value = false
        apiAvailable.value = true
        return result
      }
    } catch (err) {
      if (err.name === 'AbortError') return demoValue
      console.warn(`[${type}] API failed, falling back to demo`, err)
      error.value[type] = err.message
      lastApiFailureTime.value = Date.now()
      apiAvailable.value = false
    } finally {
      loading.value[type] = false
    }
    // Fallback to demo data
    return demoValue
  }

  // Actions
  async function fetchDrones() {
    drones.value = await fetchWithFallback(
      () => droneApi.getDrones(),
      demoData.drones,
      'drones'
    )
  }

  async function fetchTasks(params = {}) {
    tasks.value = await fetchWithFallback(
      () => taskApi.getTasks(params),
      demoData.tasks,
      'tasks'
    )
  }

  async function fetchHistory() {
    historyData.value = await fetchWithFallback(
      () => taskApi.getTaskHistory(),
      demoData.history,
      'history'
    )
  }

  async function fetchWeather(lat = 39.9, lng = 116.4) {
    await fetchWithFallback(
      () => weatherApi.getWeatherCurrent(lat, lng),
      () => {
        weatherData.value = demoData.weather
        if (demoData.weather.windField) windField.value = demoData.weather.windField
        return demoData.weather
      },
      'weather'
    )
    if (weatherData.value && weatherData.value.windField) {
      windField.value = weatherData.value.windField
    }
  }

  // 数据源管理
  async function fetchDataSources() {
    dataSources.value = await fetchWithFallback(
      () => dataSourceApi.getDataSources(),
      [
        { id: 1, name: 'GOES-16卫星数据', type: 'satellite', format: 'netcdf', status: 'active', createdAt: '2024-01-01T00:00:00Z' },
        { id: 2, name: '多普勒雷达数据', type: 'radar', format: 'hdf5', status: 'active', createdAt: '2024-01-02T00:00:00Z' },
        { id: 3, name: '气象地面站数据', type: 'ground_station', format: 'csv', status: 'active', createdAt: '2024-01-03T00:00:00Z' },
        { id: 4, name: '海洋浮标数据', type: 'buoy', format: 'json', status: 'active', createdAt: '2024-01-04T00:00:00Z' }
      ],
      'dataSources'
    )
  }

  async function createDataSource(data) {
    try {
      const controller = new AbortController()
      addController('createDataSource', controller)
      const response = await dataSourceApi.createDataSource(data, { signal: controller.signal })
      removeController('createDataSource')
      const newDataSource = response || {
        id: Math.max(0, ...dataSources.value.map(item => item.id), 0) + 1,
        ...data,
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      dataSources.value.unshift(newDataSource)
      apiAvailable.value = true
      return newDataSource
    } catch (err) {
      if (err.name === 'AbortError') throw err
      console.error('[createDataSource]', err)
      throw err
    }
  }

  async function updateDataSource(id, data) {
    try {
      const controller = new AbortController()
      addController('updateDataSource', controller)
      await dataSourceApi.updateDataSource(id, data, { signal: controller.signal })
      removeController('updateDataSource')
      const index = dataSources.value.findIndex(item => item.id === id)
      if (index > -1) {
        dataSources.value[index] = {
          ...dataSources.value[index],
          ...data,
          updatedAt: new Date().toISOString()
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') throw err
      console.error('[updateDataSource]', err)
      throw err
    }
  }

  async function deleteDataSource(id) {
    try {
      const controller = new AbortController()
      addController('deleteDataSource', controller)
      await dataSourceApi.deleteDataSource(id, { signal: controller.signal })
      removeController('deleteDataSource')
      const index = dataSources.value.findIndex(item => item.id === id)
      if (index > -1) {
        dataSources.value.splice(index, 1)
      }
    } catch (err) {
      if (err.name === 'AbortError') throw err
      console.error('[deleteDataSource]', err)
      const index = dataSources.value.findIndex(item => item.id === id)
      if (index > -1) {
        dataSources.value.splice(index, 1)
      }
    }
  }

  // 请求取消管理
  function addController(id, controller) {
    pendingControllers.set(id, controller)
  }

  function removeController(id) {
    pendingControllers.delete(id)
  }

  function cancelRequest(id) {
    const controller = pendingControllers.get(id)
    if (controller) {
      controller.abort()
      pendingControllers.delete(id)
    }
  }

  function cancelAllRequests() {
    pendingControllers.forEach((controller) => controller.abort())
    pendingControllers.clear()
  }

  // Reset function
  function reset() {
    cancelAllRequests()
    drones.value = []
    tasks.value = []
    historyData.value = []
    weatherData.value = null
    windField.value = []
    dataSources.value = []
    Object.keys(loading.value).forEach(key => loading.value[key] = false)
    Object.keys(error.value).forEach(key => error.value[key] = null)
  }

  return {
    // State
    drones,
    tasks,
    historyData,
    weatherData,
    windField,
    dataSources,
    loading,
    error,
    useDemo,
    apiAvailable,
    lastApiFailureTime,

    // Actions
    fetchDrones,
    fetchTasks,
    fetchHistory,
    fetchWeather,
    fetchDataSources,
    createDataSource,
    updateDataSource,
    deleteDataSource,
    addController,
    cancelRequest,
    cancelAllRequests,
    reset
  }
})
