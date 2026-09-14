// Small date helpers. All "day" values are YYYY-MM-DD strings in the browser's local zone,
// which for this single-user app is Europe/Amsterdam.

export function toDay(d = new Date()) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function addDays(day, n) {
  const [y, m, d] = day.split('-').map(Number)
  const dt = new Date(y, m - 1, d + n)
  return toDay(dt)
}

export function today() {
  return toDay(new Date())
}

export function tomorrow() {
  return addDays(today(), 1)
}

export function mondayOf(day = today()) {
  const [y, m, d] = day.split('-').map(Number)
  const dt = new Date(y, m - 1, d)
  const offset = (dt.getDay() + 6) % 7 // Monday = 0
  return toDay(new Date(y, m - 1, d - offset))
}

export function weekDays(monday) {
  return Array.from({ length: 7 }, (_, i) => addDays(monday, i))
}

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function shortDay(day) {
  const [y, m, d] = day.split('-').map(Number)
  const dt = new Date(y, m - 1, d)
  return `${DAY_NAMES[(dt.getDay() + 6) % 7]} ${d}`
}

export function formatDay(day) {
  if (!day) return ''
  const [y, m, d] = day.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
}

export function formatDateTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

export function minutesToHours(min) {
  const m = Math.round(min || 0)
  const h = Math.floor(m / 60)
  const rest = m % 60
  if (!h) return `${rest}m`
  return rest ? `${h}h ${String(rest).padStart(2, '0')}m` : `${h}h`
}

export function daysUntil(day) {
  if (!day) return null
  const [y, m, d] = day.split('-').map(Number)
  const target = new Date(y, m - 1, d)
  const now = new Date()
  const base = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return Math.round((target - base) / 86400000)
}
