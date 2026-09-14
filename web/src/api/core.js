import { api } from '../lib/api'

export const getHealth = () => api('/api/health')
export const getMe = () => api('/api/me')
export const getAreas = () => api('/api/areas')
export const getSettings = () => api('/api/settings')
export const updateSettings = (patch) => api('/api/settings', { method: 'PUT', body: patch })
