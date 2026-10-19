// Shared habit vocabulary: how a habit is scheduled, how one day of it reads, and its icon.
import {
  PhBarbell, PhBed, PhBicycle, PhBookOpen, PhBrain, PhCoffee, PhDrop, PhFire, PhFlower, PhForkKnife,
  PhGuitar, PhHeart, PhLeaf, PhMoon, PhPencilSimple, PhPersonSimpleRun, PhPersonSimpleWalk, PhPill,
  PhPlant, PhScales, PhShower, PhSmileyBlank, PhSneakerMove, PhSun, PhSwimmingPool, PhTimer, PhTooth,
  PhTranslate, PhWine, PhCheckCircle, PhDeviceMobileSlash, PhPersonSimpleTaiChi,
} from '@phosphor-icons/vue'

export const ICONS = {
  check: PhCheckCircle,
  barbell: PhBarbell,
  run: PhPersonSimpleRun,
  walk: PhPersonSimpleWalk,
  sneaker: PhSneakerMove,
  bike: PhBicycle,
  swim: PhSwimmingPool,
  stretch: PhPersonSimpleTaiChi,
  pill: PhPill,
  drop: PhDrop,
  food: PhForkKnife,
  coffee: PhCoffee,
  nodrink: PhWine,
  scales: PhScales,
  bed: PhBed,
  moon: PhMoon,
  sun: PhSun,
  shower: PhShower,
  sauna: PhFire,
  tooth: PhTooth,
  book: PhBookOpen,
  brain: PhBrain,
  pencil: PhPencilSimple,
  language: PhTranslate,
  guitar: PhGuitar,
  timer: PhTimer,
  phone: PhDeviceMobileSlash,
  heart: PhHeart,
  mood: PhSmileyBlank,
  leaf: PhLeaf,
  plant: PhPlant,
  flower: PhFlower,
}

export function iconFor(t) {
  return ICONS[t?.icon] || ICONS.check
}

export const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
export const WEEKDAY_LETTERS = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

export const isWeekly = (t) => t?.target_period === 'week'
export const isBool = (t) => t?.type === 'daily_bool'
export const isCount = (t) => t?.type === 'weekly_count'
export const isValue = (t) => t?.type === 'numeric' || t?.type === 'duration'

export function unitOf(t) {
  if (t.type === 'duration') return t.unit || 'min'
  return t.unit || ''
}

export function scheduleLabel(t) {
  if (isWeekly(t)) return t.target_value ? `${fmt(t.target_value)}${isCount(t) ? 'x' : ' ' + unitOf(t)} a week` : 'Weekly'
  if (t.schedule === 'weekdays') {
    const mask = t.schedule_days || 127
    if (mask === 0b0011111) return 'Weekdays'
    if (mask === 0b1100000) return 'Weekends'
    return WEEKDAYS.filter((_, i) => (mask >> i) & 1).join(', ')
  }
  if (t.schedule === 'every_n_days') return `Every ${t.schedule_n} days`
  return 'Every day'
}

export function targetLabel(t) {
  if (isBool(t) || !t.target_value) return ''
  return `${fmt(t.target_value)}${unitOf(t) ? ' ' + unitOf(t) : ''} per ${t.target_period}`
}

export function streakLabel(t) {
  if (!t.streak) return ''
  const unit = isWeekly(t) ? 'week' : 'day'
  return `${t.streak} ${unit}${t.streak === 1 ? '' : 's'}`
}

export function fmt(n) {
  if (n === null || n === undefined) return ''
  return String(Math.round(Number(n) * 100) / 100)
}

export function cellOf(t, day) {
  return t?.days?.find((d) => d.date === day) || null
}

// One day of a habit, as the Today list and the grid read it.
export function dayState(t, cell, today) {
  if (!cell) return 'none'
  if (cell.date > today) return 'future'
  if (cell.status === 'skipped') return 'skipped'
  if (cell.met) return 'done'
  if (cell.value) return 'part'
  if (!isWeekly(t) && !cell.due) return 'off'
  return 'open'
}

// Relative label for the next due day: "Tomorrow", "Fri", "in 9 days".
export function nextDueLabel(day, from) {
  if (!day) return ''
  const [y, m, d] = day.split('-').map(Number)
  const [fy, fm, fd] = from.split('-').map(Number)
  const diff = Math.round((new Date(y, m - 1, d) - new Date(fy, fm - 1, fd)) / 86400000)
  if (diff <= 0) return 'Today'
  if (diff === 1) return 'Tomorrow'
  if (diff < 7) return WEEKDAYS[(new Date(y, m - 1, d).getDay() + 6) % 7]
  return `in ${diff} days`
}
