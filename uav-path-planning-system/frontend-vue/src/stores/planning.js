import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as pathApi from '../api/path'
import { demoData } from '../utils/demoData'

export const usePlanningStore = defineStore('planning', () => {
  const taskPoints = ref([...demoData.pathPlanning.defaultTaskPoints])
  const noFlyZones = ref([
    { id: 1, name: '禁飞区A', type: 'circle', center: [39.9142, 116.4174], radius: 200 },
    { id: 2, name: '禁飞区B', type: 'circle', center: [39.9242, 116.4274], radius: 150 }
  ])
  const savedPlans = ref([...demoData.pathPlanning.defaultSavedPlans])
  const result = ref(null)
  const realtime = ref({ ...demoData.pathPlanning.defaultRealtimeData })
  const loading = ref(false)
  const error = ref(null)

  function addTaskPoint(point) {
    const nextId = taskPoints.value.reduce((max, p) => Math.max(max, p.id || 0), 0) + 1
    taskPoints.value.push({
      id: nextId,
      name: point.name || `任务点${nextId}`,
      lat: point.lat,
      lng: point.lng,
      demand: point.demand || 1,
      startTime: point.startTime,
      endTime: point.endTime,
      serviceTime: point.serviceTime
    })
  }

  function removeTaskPoint(id) {
    taskPoints.value = taskPoints.value.filter((p) => p.id !== id)
  }

  function clearTaskPoints() {
    taskPoints.value = []
  }

  function addNoFlyZone(zone) {
    const newZone = {
      id: Date.now(),
      name: zone.name,
      type: zone.type || 'circle',
      center: zone.center,
      radius: zone.radius,
      points: zone.points
    }
    noFlyZones.value.push(newZone)
    return newZone
  }

  function removeNoFlyZone(id) {
    noFlyZones.value = noFlyZones.value.filter((z) => z.id !== id)
  }

  async function execute(params = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await pathApi.planPath({
        taskPoints: taskPoints.value,
        noFlyZones: noFlyZones.value,
        ...params
      })
      const data = res?.data || res
      if (data && data.routes) {
        result.value = data
      } else {
        result.value = demoData.pathPlanning.mockResult
      }
    } catch (e) {
      error.value = e?.message || '路径规划失败'
      result.value = demoData.pathPlanning.mockResult
    } finally {
      loading.value = false
    }
    return result.value
  }

  function savePlan(name) {
    const plan = {
      id: savedPlans.value.length + 1,
      name,
      taskPoints: [...taskPoints.value],
      result: result.value,
      savedAt: new Date().toISOString()
    }
    savedPlans.value.push(plan)
    return plan
  }

  function deletePlan(id) {
    savedPlans.value = savedPlans.value.filter((p) => p.id !== id)
  }

  function reset() {
    result.value = null
    error.value = null
  }

  return {
    taskPoints,
    noFlyZones,
    savedPlans,
    result,
    realtime,
    loading,
    error,
    addTaskPoint,
    removeTaskPoint,
    clearTaskPoints,
    addNoFlyZone,
    removeNoFlyZone,
    execute,
    savePlan,
    deletePlan,
    reset
  }
})
