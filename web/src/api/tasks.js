import { api } from '../lib/api'

const qs = (params = {}) => {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  return entries.length ? '?' + new URLSearchParams(entries).toString() : ''
}

export const listTasks = (params) => api(`/api/tasks${qs(params)}`)
export const getTask = (id) => api(`/api/tasks/${id}`)
export const createTask = (body) => api('/api/tasks', { method: 'POST', body })
export const updateTask = (id, body) => api(`/api/tasks/${id}`, { method: 'PATCH', body })
export const deleteTask = (id) => api(`/api/tasks/${id}`, { method: 'DELETE' })
export const completeTask = (id, actualMinutes) =>
  api(`/api/tasks/${id}/complete`, { method: 'POST', body: actualMinutes ? { actual_minutes: actualMinutes } : {} })
export const moveTask = (id, quadrant) => api(`/api/tasks/${id}/move`, { method: 'POST', body: { quadrant } })
export const suggestSlot = (id, body = {}) => api(`/api/tasks/${id}/suggest-slot`, { method: 'POST', body })
export const scheduleTask = (id, body) => api(`/api/tasks/${id}/schedule`, { method: 'POST', body })
export const unscheduleTask = (id) => api(`/api/tasks/${id}/unschedule`, { method: 'POST' })
