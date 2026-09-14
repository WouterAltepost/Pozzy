import { api } from '../lib/api'

export const listCourses = (includeClosed = false) => api(`/api/study/courses${includeClosed ? '?include_closed=1' : ''}`)
export const createCourse = (body) => api('/api/study/courses', { method: 'POST', body })
export const updateCourse = (id, body) => api(`/api/study/courses/${id}`, { method: 'PATCH', body })
export const deleteCourse = (id) => api(`/api/study/courses/${id}`, { method: 'DELETE' })

export const listDeadlines = (includeDone = false) => api(`/api/study/deadlines${includeDone ? '?include_done=1' : ''}`)
export const createDeadline = (body) => api('/api/study/deadlines', { method: 'POST', body })
export const updateDeadline = (id, body) => api(`/api/study/deadlines/${id}`, { method: 'PATCH', body })
export const deleteDeadline = (id) => api(`/api/study/deadlines/${id}`, { method: 'DELETE' })

export const listApplications = () => api('/api/study/applications')
export const createApplication = (body) => api('/api/study/applications', { method: 'POST', body })
export const updateApplication = (id, body) => api(`/api/study/applications/${id}`, { method: 'PATCH', body })
export const deleteApplication = (id) => api(`/api/study/applications/${id}`, { method: 'DELETE' })

export const upcoming = (days = 14) => api(`/api/study/upcoming?days=${days}`)
