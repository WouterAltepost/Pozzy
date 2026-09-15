import { api } from '../lib/api'

export const listTrackers = (includeInactive = false) => api(`/api/trackers${includeInactive ? '?include_inactive=1' : ''}`)
export const trackerWeek = (weekStart, includeInactive = false) => {
  const params = new URLSearchParams()
  if (weekStart) params.set('week_start', weekStart)
  if (includeInactive) params.set('include_inactive', '1')
  const q = params.toString()
  return api(`/api/trackers/week${q ? '?' + q : ''}`)
}
export const createTracker = (body) => api('/api/trackers', { method: 'POST', body })
export const updateTracker = (id, body) => api(`/api/trackers/${id}`, { method: 'PATCH', body })
export const deleteTracker = (id) => api(`/api/trackers/${id}`, { method: 'DELETE' })
export const trackerHistory = (id, weeks = 8) => api(`/api/trackers/${id}/history?${weeks === 'all' ? 'all=1' : 'weeks=' + weeks}`)
export const upsertEntry = (id, body) => api(`/api/trackers/${id}/entries`, { method: 'PUT', body })
export const deleteEntry = (id, date) => api(`/api/trackers/${id}/entries/${date}`, { method: 'DELETE' })
export const tickTracker = (id, date) => api(`/api/trackers/${id}/tick`, { method: 'POST', body: date ? { date } : {} })
