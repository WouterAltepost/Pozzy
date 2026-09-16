import { api } from '../lib/api'

export const getBriefing = (date) => api(`/api/ai/briefing${date ? '?date=' + date : ''}`)
export const regenerateBriefing = (date) => api('/api/ai/briefing', { method: 'POST', body: date ? { date } : {} })
export const getSpend = () => api('/api/ai/spend')
export const addBriefingNote = (text, date) => api('/api/ai/briefing/notes', { method: 'POST', body: { text, ...(date ? { date } : {}) } })
export const applyBriefingActions = (noteIndex, actions, date) =>
  api(`/api/ai/briefing/notes/${noteIndex}/apply`, { method: 'POST', body: { actions, ...(date ? { date } : {}) } })
export const planWeek = (start, days = 7) => api('/api/ai/plan', { method: 'POST', body: { start, days } })
