import { api } from '../lib/api'

export const listCaptures = (status) => api(`/api/captures${status ? '?status=' + status : ''}`)
export const createCapture = (text, process = false) => api('/api/captures', { method: 'POST', body: { text, process } })
export const processCapture = (id) => api(`/api/captures/${id}/process`, { method: 'POST' })
export const confirmCapture = (id, body = {}) => api(`/api/captures/${id}/confirm`, { method: 'POST', body })
export const discardCapture = (id) => api(`/api/captures/${id}/discard`, { method: 'POST' })
export const deleteCapture = (id) => api(`/api/captures/${id}`, { method: 'DELETE' })
