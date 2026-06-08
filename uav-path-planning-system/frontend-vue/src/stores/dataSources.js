import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as dsApi from '../api/datasource'

const DEFAULT_SOURCES = [
  { id: 1, name: 'GOES-16卫星数据', type: 'satellite', format: 'netcdf', status: 'active', createdAt: '2024-01-01T00:00:00Z' },
  { id: 2, name: '多普勒雷达数据', type: 'radar', format: 'hdf5', status: 'active', createdAt: '2024-01-02T00:00:00Z' },
  { id: 3, name: '气象地面站数据', type: 'ground_station', format: 'csv', status: 'active', createdAt: '2024-01-03T00:00:00Z' },
  { id: 4, name: '海洋浮标数据', type: 'buoy', format: 'json', status: 'active', createdAt: '2024-01-04T00:00:00Z' }
]

export const useDataSourceStore = defineStore('dataSources', () => {
  const list = ref([...DEFAULT_SOURCES])
  const loading = ref(false)
  const error = ref(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const res = await dsApi.getDataSources()
      const data = res?.data || res
      if (Array.isArray(data) && data.length > 0) {
        list.value = data
      }
    } catch (e) {
      error.value = e?.message || '获取数据源列表失败'
    } finally {
      loading.value = false
    }
  }

  function add(data) {
    const nextId = list.value.reduce((max, s) => Math.max(max, s.id || 0), 0) + 1
    const item = {
      id: nextId,
      name: data.name,
      type: data.type,
      format: data.format || 'json',
      status: data.status || 'active',
      createdAt: new Date().toISOString(),
      config: data.config
    }
    list.value.unshift(item)
    return item
  }

  function update(id, data) {
    const idx = list.value.findIndex((s) => s.id === id)
    if (idx > -1) {
      list.value[idx] = { ...list.value[idx], ...data, updatedAt: new Date().toISOString() }
      return list.value[idx]
    }
    return null
  }

  function remove(id) {
    list.value = list.value.filter((s) => s.id !== id)
  }

  return {
    list,
    loading,
    error,
    fetchAll,
    add,
    update,
    remove
  }
})
