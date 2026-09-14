import { api } from '../lib/api'

export const listHours = ({ from, to } = {}) => {
  const params = new URLSearchParams()
  if (from) params.set('from', from)
  if (to) params.set('to', to)
  const q = params.toString()
  return api(`/api/hours${q ? '?' + q : ''}`)
}
export const hoursWeek = (weekStart) => api(`/api/hours/week${weekStart ? '?week_start=' + weekStart : ''}`)
export const createHours = (body) => api('/api/hours', { method: 'POST', body })
export const updateHours = (id, body) => api(`/api/hours/${id}`, { method: 'PATCH', body })
export const deleteHours = (id) => api(`/api/hours/${id}`, { method: 'DELETE' })
