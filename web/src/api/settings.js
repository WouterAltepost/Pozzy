import { api } from '../lib/api'

export const getSettings = () => api('/api/settings')
export const getSettingDefaults = () => api('/api/settings/defaults')
export const updateSettings = (patch) => api('/api/settings', { method: 'PUT', body: patch })
export const listJobRuns = (limit = 50) => api(`/api/settings/job-runs?limit=${limit}`)
