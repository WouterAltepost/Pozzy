import { api } from '../lib/api'

export const listReviews = () => api('/api/reviews')
export const getReview = (week) => api(`/api/reviews/${week}`)
export const generateReview = (week) => api(`/api/reviews/${week}/generate`, { method: 'POST' })
export const refreshReviewStats = (week) => api(`/api/reviews/${week}/refresh-stats`, { method: 'POST' })
export const updateReview = (week, body) => api(`/api/reviews/${week}`, { method: 'PATCH', body })
export const finalizeReview = (week) => api(`/api/reviews/${week}/finalize`, { method: 'POST' })
