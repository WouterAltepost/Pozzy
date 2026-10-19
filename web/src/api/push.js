import { api } from '../lib/api'

export const pushConfig = () => api('/api/push/config')
export const savePushSubscription = (sub) => api('/api/push/subscriptions', { method: 'POST', body: sub })
export const deletePushSubscription = (endpoint) => api('/api/push/subscriptions', { method: 'DELETE', body: { endpoint } })
export const sendTestPush = () => api('/api/push/test', { method: 'POST' })
