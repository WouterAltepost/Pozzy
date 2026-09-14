import { api } from '../lib/api'

const qs = (params = {}) => {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  return entries.length ? '?' + new URLSearchParams(entries).toString() : ''
}

// Events and scheduled tasks in [start, end), both ISO 8601 with offset. Returns { start, end, events, tasks }.
export const listEvents = (params) => api(`/api/calendar/events${qs(params)}`)
export const createEvent = (body) => api('/api/calendar/events', { method: 'POST', body })
export const updateEvent = (id, body) => api(`/api/calendar/events/${id}`, { method: 'PUT', body })
export const deleteEvent = (id) => api(`/api/calendar/events/${id}`, { method: 'DELETE' })
export const syncNow = () => api('/api/calendar/sync', { method: 'POST' })
export const getAccount = () => api('/api/calendar/account')
export const updateAccount = (body) => api('/api/calendar/account', { method: 'PUT', body })
export const discoverCalendars = () => api('/api/calendar/account/discover', { method: 'POST' })
