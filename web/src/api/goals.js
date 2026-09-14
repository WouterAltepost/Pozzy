import { api } from '../lib/api'

export const listGoals = (weekStart) => api(`/api/goals${weekStart ? '?week_start=' + weekStart : ''}`)
export const createGoal = (body) => api('/api/goals', { method: 'POST', body })
export const updateGoal = (id, body) => api(`/api/goals/${id}`, { method: 'PATCH', body })
export const addGoalProgress = (id, delta = 1) => api(`/api/goals/${id}/progress`, { method: 'POST', body: { delta } })
export const deleteGoal = (id) => api(`/api/goals/${id}`, { method: 'DELETE' })
