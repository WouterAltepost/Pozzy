// Web Push on this device: is it possible here, is this device subscribed, and turning it on
// or off. iOS only allows push from the installed home-screen app (16.4 and later).
import { deletePushSubscription, pushConfig, savePushSubscription } from '../api/push'

export function pushSupported() {
  return typeof window !== 'undefined' && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
}

export function isStandalone() {
  return window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true
}

export function isIos() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
}

async function registration() {
  // getRegistration resolves at once (undefined in dev, where no worker is registered).
  return (await navigator.serviceWorker.getRegistration()) || null
}

export async function currentSubscription() {
  if (!pushSupported()) return null
  const reg = await registration()
  return reg ? reg.pushManager.getSubscription() : null
}

function keyBytes(base64) {
  const pad = '='.repeat((4 - (base64.length % 4)) % 4)
  const raw = atob((base64 + pad).replace(/-/g, '+').replace(/_/g, '/'))
  return Uint8Array.from(raw, (c) => c.charCodeAt(0))
}

export async function enablePush() {
  if (!pushSupported()) throw new Error('This browser cannot receive push notifications.')
  const config = await pushConfig()
  if (!config.configured || !config.public_key) throw new Error('Push is not set up on the server yet (VAPID keys missing).')
  const permission = await Notification.requestPermission()
  if (permission !== 'granted') throw new Error(permission === 'denied' ? 'Notifications are blocked for Pozzy. Allow them in the system settings.' : 'Notifications were not allowed.')
  const reg = await registration()
  if (!reg) throw new Error('The app is not installed as a PWA in this browser (no service worker).')
  let sub = await reg.pushManager.getSubscription()
  if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyBytes(config.public_key) })
  await savePushSubscription(sub.toJSON())
  return sub
}

export async function disablePush() {
  const sub = await currentSubscription()
  if (!sub) return
  try {
    await deletePushSubscription(sub.endpoint)
  } finally {
    await sub.unsubscribe()
  }
}
