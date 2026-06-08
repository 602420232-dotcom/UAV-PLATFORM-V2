import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as taskApi from '../api/tasks'
import { demoData } from '../utils/demoData'

export const useTaskStore = defineStore('tasks', () => {
  const list = ref([])
  const history = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchAll(params) {
    loading.value = true
    error.value = null
    try {
      const res = await taskApi.getTasks(params)
      const data = res?.data || res
      if (Array.isArray(data) && data.length > 0) {
        list.value = data
      } else {
        list.value = demoData.tasks
      }
    } catch (e) {
      error.value = e?.message || '获取任务列表失败'
      list.value = demoData.tasks
    } finally {
      loading.value = false
    }
  }

  async function fetchHistory(params) {
    loading.value = true
    error.value = null
    try {
      const res = await taskApi.getTaskHistory(params)
      const data = res?.data || res
      if (Array.isArray(data) && data.length > 0) {
        history.value = data
      } else {
        history.value = demoData.history
      }
    } catch (e) {
      error.value = e?.message || '获取历史记录失败'
      history.value = demoData.history
    } finally {
      loading.value = false
    }
  }

  function addTask(task) {
    const nextId = list.value.reduce((max, t) => Math.max(max, t.id || 0), 0) + 1
    const newTask = {
      id: nextId,
      name: task.name,
      type: task.type || 'delivery',
      location: task.location || '',
      startTime: task.startTime || new Date().toISOString(),
      endTime: task.endTime || '',
      priority: task.priority || 'medium',
      status: task.status || '待分配',
      description: task.description || ''
    }
    list.value.unshift(newTask)
    return newTask
  }

  function updateTask(id, data) {
    const idx = list.value.findIndex((t) => t.id === id)
    if (idx > -1) {
      list.value[idx] = { ...list.value[idx], ...data }
      return list.value[idx]
    }
    return null
  }

  function removeTask(id) {
    list.value = list.value.filter((t) => t.id !== id)
  }

  return {
    list,
    history,
    loading,
    error,
    fetchAll,
    fetchHistory,
    addTask,
    updateTask,
    removeTask
  }
})
