import { defineStore } from 'pinia'
import { ref } from 'vue'
import { demoData, normalizeApiResponse } from '../utils/demoData'
import * as droneApi from '../api/drones'
import * as taskApi from '../api/tasks'
import * as weatherApi from '../api/weather'
import * as dataSourceApi from '../api/datasource'

// ── Type Definitions ──────────────────────────────────────────────────────────

interface Drone {
  id: string
  name: string
  type: string
  status: string
  battery: number
  location: string
}

interface Task {
  id: number
  name: string
  type: string
  location: string
  priority: string
  status: string
  description: string
}

interface TaskRoute {
  droneId: number
  path: string[]
  distance: number
  time: number
  risk: string
}

interface HistoryRecord {
  id: number
  name: string
  startTime: string
  endTime: string
  status: string
  duration: string
  droneCount: number
  taskCount: number
  totalDistance: number
  totalTime: number
  routes: TaskRoute[]
  weatherData: {
    windSpeed: number
    windDirection: number
    temperature: number
    humidity: number
    turbulence: string
    visibility: number
  }
}

interface WindFieldPoint {
  lat: number
  lng: number
  speed: number
  direction: number
  temperature: number
  humidity: number
}

interface WeatherData {
  windSpeed: number
  windDirection: number
  temperature: number
  humidity: number
  windField?: WindFieldPoint[]
}

interface DataSource {
  id: number
  name: string
  type: string
  format: string
  status: string
  createdAt: string
  updatedAt?: string
}

interface LoadingState {
  drones: boolean
  tasks: boolean
  history: boolean
  weather: boolean
  dataSources: boolean
}

interface ErrorState {
  drones: string | null
  tasks: string | null
  history: string | null
  weather: string | null
  dataSources: string | null
}

// ── Store ─────────────────────────────────────────────────────────────────────

export const useDataStore = defineStore('data', () => {
  // State
  const drones = ref<Drone[]>([])
  const tasks = ref<Task[]>([])
  const historyData = ref<HistoryRecord[]>([])
  const weatherData = ref<WeatherData | null>(null)
  const windField = ref<WindFieldPoint[]>([])
  const dataSources = ref<DataSource[]>([])

  const loading = ref<LoadingState>({
    drones: false,
    tasks: false,
    history: false,
    weather: false,
    dataSources: false
  })
  const error = ref<ErrorState>({
    drones: null,
    tasks: null,
    history: null,
    weather: null,
    dataSources: null
  })
  const useDemo = ref(true)
  const lastApiFailureTime = ref<number | null>(null)
  const apiAvailable = ref(false)

  // 待取消的请求控制器
  const pendingControllers = new Map<string, AbortController>()

  // Helper to wrap API calls with fallback
  async function fetchWithFallback<T>(apiFn: (signal: AbortSignal) => Promise<any>, demoValue: T, type: keyof LoadingState): Promise<T> {
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
        return result as T
      }
    } catch (err: any) {
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
      (signal) => droneApi.getDrones({ signal }),
      demoData.drones as Drone[],
      'drones'
    )
  }

  async function fetchTasks(params = {}) {
    tasks.value = await fetchWithFallback(
      (signal) => taskApi.getTasks(params, { signal }),
      demoData.tasks as Task[],
      'tasks'
    )
  }

  async function fetchHistory() {
    historyData.value = await fetchWithFallback(
      (signal) => taskApi.getTaskHistory({ signal }),
      demoData.history as HistoryRecord[],
      'history'
    )
  }

  async function fetchWeather(lat = 39.9, lng = 116.4) {
    await fetchWithFallback(
      (signal) => weatherApi.getWeatherCurrent(lat, lng, { signal }),
      () => {
        weatherData.value = demoData.weather as WeatherData
        if (demoData.weather.windField) windField.value = demoData.weather.windField as WindFieldPoint[]
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
      (signal) => dataSourceApi.getDataSources({ signal }),
      [
        { id: 1, name: 'GOES-16卫星数据', type: 'satellite', format: 'netcdf', status: 'active', createdAt: '2024-01-01T00:00:00Z' },
        { id: 2, name: '多普勒雷达数据', type: 'radar', format: 'hdf5', status: 'active', createdAt: '2024-01-02T00:00:00Z' },
        { id: 3, name: '气象地面站数据', type: 'ground_station', format: 'csv', status: 'active', createdAt: '2024-01-03T00:00:00Z' },
        { id: 4, name: '海洋浮标数据', type: 'buoy', format: 'json', status: 'active', createdAt: '2024-01-04T00:00:00Z' }
      ] as DataSource[],
      'dataSources'
    )
  }

  async function createDataSource(data: Partial<DataSource>) {
    try {
      const controller = new AbortController()
      addController('createDataSource', controller)
      const response = await dataSourceApi.createDataSource(data, { signal: controller.signal })
      removeController('createDataSource')
      const newDataSource: DataSource = response || {
        id: Math.max(0, ...dataSources.value.map(item => item.id), 0) + 1,
        ...data,
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      } as DataSource
      dataSources.value.unshift(newDataSource)
      apiAvailable.value = true
      return newDataSource
    } catch (err: any) {
      if (err.name === 'AbortError') throw err
      console.error('[createDataSource]', err)
      throw err
    }
  }

  async function updateDataSource(id: number, data: Partial<DataSource>) {
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
    } catch (err: any) {
      if (err.name === 'AbortError') throw err
      console.error('[updateDataSource]', err)
      throw err
    }
  }

  async function deleteDataSource(id: number) {
    try {
      const controller = new AbortController()
      addController('deleteDataSource', controller)
      await dataSourceApi.deleteDataSource(id, { signal: controller.signal })
      removeController('deleteDataSource')
      const index = dataSources.value.findIndex(item => item.id === id)
      if (index > -1) {
        dataSources.value.splice(index, 1)
      }
    } catch (err: any) {
      if (err.name === 'AbortError') throw err
      console.error('[deleteDataSource]', err)
      const index = dataSources.value.findIndex(item => item.id === id)
      if (index > -1) {
        dataSources.value.splice(index, 1)
      }
    }
  }

  // 请求取消管理
  function addController(id: string, controller: AbortController) {
    pendingControllers.set(id, controller)
  }

  function removeController(id: string) {
    pendingControllers.delete(id)
  }

  function cancelRequest(id: string) {
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
    Object.keys(loading.value).forEach(key => loading.value[key as keyof LoadingState] = false)
    Object.keys(error.value).forEach(key => error.value[key as keyof ErrorState] = null)
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
