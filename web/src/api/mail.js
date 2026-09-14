import { api } from '../lib/api'

const qs = (params = {}) => {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  return entries.length ? '?' + new URLSearchParams(entries).toString() : ''
}

export const listEmails = (params) => api(`/api/mail/emails${qs(params)}`)
export const getEmail = (id) => api(`/api/mail/emails/${id}`)
export const updateEmail = (id, body) => api(`/api/mail/emails/${id}`, { method: 'PATCH', body })
export const createTaskFromEmail = (id, body = {}) => api(`/api/mail/emails/${id}/task`, { method: 'POST', body })
export const reclassifyEmail = (id) => api(`/api/mail/emails/${id}/reclassify`, { method: 'POST' })
export const topEmails = (limit) => api(`/api/mail/top${qs({ limit })}`)
export const mailCounts = () => api('/api/mail/counts')
export const listAccounts = () => api('/api/mail/accounts')
export const updateAccount = (id, body) => api(`/api/mail/accounts/${id}`, { method: 'PATCH', body })
export const testAccount = (id) => api(`/api/mail/accounts/${id}/test`, { method: 'POST' })
export const syncMail = () => api('/api/mail/sync', { method: 'POST' })

export const CATEGORIES = ['client', 'school', 'finance', 'personal', 'newsletter', 'notification', 'other']
export const PRIORITIES = [
  [1, 'Urgent'],
  [2, 'Important'],
  [3, 'Normal'],
  [4, 'Low'],
]
