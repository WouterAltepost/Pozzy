import { api } from '../lib/api'

export const getBriefing = (date) => api(`/api/ai/briefing${date ? '?date=' + date : ''}`)
export const regenerateBriefing = (date) => api('/api/ai/briefing', { method: 'POST', body: date ? { date } : {} })
export const getSpend = () => api('/api/ai/spend')
