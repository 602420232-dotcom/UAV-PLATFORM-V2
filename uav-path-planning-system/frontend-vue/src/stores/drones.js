import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as droneApi from '../api/drones'
import { demoData } from '../utils/demoData'

export const useDroneStore = defineStore('drones', () => {
  const list = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const res = await droneApi.getDrones()
      const data = res?.data || res
      if (Array.isArray(data) && data.length > 0) {
        list.value = data
      } else {
        list.value = demoData.drones
      }
    } catch (e) {
      error.value = e?.message || '获取无人机列表失败'
      list.value = demoData.drones
    } finally {
      loading.value = false
    }
  }

  function addDrone(drone) {
    const newDrone = {
      id: drone.id || `UAV-${String(list.value.length + 1).padStart(3, '0')}`,
      name: drone.name,
      type: drone.type || 'multirotor',
      status: drone.status || '待命',
      battery: typeof drone.battery === 'number' ? drone.battery : 100,
      location: drone.location || '39.90, 116.40',
      maxPayload: drone.maxPayload,
      maxEndurance: drone.maxEndurance,
      maxSpeed: drone.maxSpeed,
      description: drone.description
    }
    list.value.push(newDrone)
    return newDrone
  }

  function updateDrone(id, data) {
    const idx = list.value.findIndex((d) => d.id === id)
    if (idx > -1) {
      list.value[idx] = { ...list.value[idx], ...data }
      return list.value[idx]
    }
    return null
  }

  function removeDrone(id) {
    list.value = list.value.filter((d) => d.id !== id)
  }

  return {
    list,
    loading,
    error,
    fetchAll,
    addDrone,
    updateDrone,
    removeDrone
  }
})
