import { api } from '../lib/api'

export const listDos = ({ date, from, to } = {}) => {
  const params = new URLSearchParams()
  if (date) params.set('date', date)
  if (from) params.set('from', from)
  if (to) params.set('to', to)
  const q = params.toString()
  return api(`/api/dos${q ? '?' + q : ''}`)
}
export const createDo = (body) => api('/api/dos', { method: 'POST', body })
export const updateDo = (id, body) => api(`/api/dos/${id}`, { method: 'PATCH', body })
export const deleteDo = (id) => api(`/api/dos/${id}`, { method: 'DELETE' })
export const suggestDos = (date) => api('/api/dos/suggest', { method: 'POST', body: date ? { date } : {} })
export const rolloverNow = () => api('/api/dos/rollover', { method: 'POST' })
