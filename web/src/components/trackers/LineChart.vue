<script setup>
// One habit's history as a single smooth line with a soft wash under it. Hairline grid on
// three round values, dates on three ticks, the latest value labelled at the end of the line,
// the goal as a quiet labelled line. Hover or drag for a crosshair with the date and value.
// A long daily series is noise as a line, so the line shows an average and each day stays as
// a faint dot behind it, the way Health draws trends.
// No chart library: the viewBox follows the container width so text never stretches.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { areaPath, niceTicks, shortDate, smoothPath } from '../../lib/chart'

const props = defineProps({
  points: { type: Array, default: () => [] },
  target: { type: Number, default: null },
  unit: { type: String, default: '' },
  height: { type: Number, default: 160 },
  color: { type: String, default: '' },
})

const wrap = ref(null)
const width = ref(520)
let observer = null
onMounted(() => {
  if (!wrap.value) return
  width.value = Math.max(240, wrap.value.clientWidth || 520)
  observer = new ResizeObserver((entries) => {
    const w = entries[0]?.contentRect?.width
    if (w) width.value = Math.max(240, Math.round(w))
  })
  observer.observe(wrap.value)
})
onBeforeUnmount(() => observer?.disconnect())

const pad = { l: 36, r: 44, t: 14, b: 24 }
const fmt = (v) => (Math.abs(v) >= 100 ? Math.round(v) : Math.round(v * 10) / 10)
const uid = `lc-${Math.random().toString(36).slice(2, 8)}`

const geometry = computed(() => {
  const pts = props.points.filter((p) => typeof p.value === 'number')
  if (!pts.length) return null
  const xs = pts.map((p) => new Date(p.date + 'T12:00:00').getTime())
  const ys = pts.map((p) => p.value)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  // Counts and percentages start at zero; a value like body weight zooms to its own range.
  const lo = Math.min(...ys, props.target ?? Infinity)
  const hi = Math.max(...ys, props.target ?? -Infinity)
  const fromZero = lo >= 0 && lo <= (hi - lo) * 1.5
  const ticks = niceTicks(fromZero ? 0 : lo, hi === lo ? hi + 1 : hi, 3)
  const minY = ticks[0]
  const maxY = ticks[ticks.length - 1]
  const w = width.value - pad.l - pad.r
  const h = props.height - pad.t - pad.b
  const sx = (x) => pad.l + (maxX === minX ? w / 2 : ((x - minX) / (maxX - minX)) * w)
  const sy = (y) => pad.t + h - ((y - minY) / (maxY - minY || 1)) * h
  // Up to 3 weeks: the days themselves. Up to about 2 months: a trailing 7 day mean by calendar
  // date (a missed day does not stretch the window). Longer: one mean per calendar week, drawn
  // at the middle of the week, which keeps months of data calm.
  const DAY = 86400000
  const mode = pts.length > 60 ? 'week' : pts.length > 21 ? 'rolling' : 'day'
  const avg = pts.map((p, i) => {
    const win = pts.filter((_, j) => xs[j] <= xs[i] && xs[j] > xs[i] - 7 * DAY).map((q) => q.value)
    return win.reduce((a, v) => a + v, 0) / win.length
  })
  const dots = pts.map((p, i) => ({ x: sx(xs[i]), y: sy(p.value), key: p.date }))
  let coords
  if (mode === 'week') {
    const weeks = new Map()
    pts.forEach((p, i) => {
      const d = new Date(xs[i])
      const monday = xs[i] - ((d.getDay() + 6) % 7) * DAY
      if (!weeks.has(monday)) weeks.set(monday, [])
      weeks.get(monday).push(p.value)
    })
    coords = [...weeks.entries()].sort((a, b) => a[0] - b[0]).map(([monday, vals]) => {
      const mean = vals.reduce((a, v) => a + v, 0) / vals.length
      const mid = Math.min(maxX, Math.max(minX, monday + 3 * DAY))
      const iso = new Date(monday).toISOString().slice(0, 10)
      return { x: sx(mid), y: sy(mean), value: mean, avg: mean, date: iso, week: true }
    })
  } else {
    coords = pts.map((p, i) => ({ x: sx(xs[i]), y: sy(mode === 'rolling' ? avg[i] : p.value), avg: avg[i], ...p }))
  }
  // Date labels at the first day, the middle and the last day of the range.
  const n = pts.length
  const tickIdx = [0, Math.round((n - 1) / 2), n - 1].filter((v, i, a) => a.indexOf(v) === i)
  const averaged = mode !== 'day'
  return {
    coords,
    line: smoothPath(coords),
    area: areaPath(coords, sy(minY)),
    grid: ticks.map((v) => ({ v, y: sy(v) })),
    targetY: props.target != null ? sy(props.target) : null,
    labels: tickIdx.map((i) => ({ x: sx(xs[i]), text: shortDate(pts[i].date), anchor: n === 1 ? 'middle' : i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle' })),
    last: coords[coords.length - 1],
    averaged,
    mode,
    dots,
  }
})

const hover = ref(null)
function onMove(e) {
  const g = geometry.value
  if (!g || !wrap.value) return
  const rect = wrap.value.getBoundingClientRect()
  const x = ((e.clientX - rect.left) / rect.width) * width.value
  let best = null
  let dist = Infinity
  for (const c of g.coords) {
    const d = Math.abs(c.x - x)
    if (d < dist) { dist = d; best = c }
  }
  hover.value = best
}
const stroke = computed(() => props.color || 'var(--brand)')
</script>

<template>
  <div ref="wrap" class="wrap" :style="{ '--c': stroke }" @pointermove="onMove" @pointerleave="hover = null">
    <svg :viewBox="`0 0 ${width} ${height}`" class="chart" :style="{ height: height + 'px' }" role="img" :aria-label="geometry ? `${geometry.coords.length} points, latest ${fmt(geometry.last.value)} ${unit}` : 'No entries yet'">
      <template v-if="geometry">
        <defs>
          <linearGradient :id="uid" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" :stop-color="stroke" stop-opacity="0.2" />
            <stop offset="1" :stop-color="stroke" stop-opacity="0" />
          </linearGradient>
        </defs>
        <g class="grid">
          <line v-for="t in geometry.grid" :key="t.v" :x1="pad.l" :x2="width - pad.r" :y1="t.y" :y2="t.y" />
          <text v-for="t in geometry.grid" :key="'l' + t.v" :x="pad.l - 8" :y="t.y + 3.5" text-anchor="end">{{ fmt(t.v) }}</text>
        </g>
        <g v-if="geometry.targetY != null" class="target">
          <line :x1="pad.l" :x2="width - pad.r" :y1="geometry.targetY" :y2="geometry.targetY" />
          <text :x="width - pad.r + 6" :y="geometry.targetY + 3.5">goal</text>
        </g>
        <g v-if="geometry.averaged" class="days"><circle v-for="d in geometry.dots" :key="d.key" :cx="d.x" :cy="d.y" r="2" /></g>
        <path v-if="geometry.coords.length > 1" :d="geometry.area" :fill="`url(#${uid})`" />
        <path v-if="geometry.coords.length > 1" :d="geometry.line" class="line" />
        <line v-if="hover" class="cross" :x1="hover.x" :x2="hover.x" :y1="pad.t" :y2="height - pad.b" />
        <circle :cx="(hover || geometry.last).x" :cy="(hover || geometry.last).y" r="4.5" class="dot" />
        <text v-if="!hover" :x="geometry.last.x + 8" :y="geometry.last.y + 4" class="end">{{ fmt(geometry.averaged ? geometry.last.avg : geometry.last.value) }}</text>
        <text v-for="l in geometry.labels" :key="l.text + l.x" :x="l.x" :y="height - 5" :text-anchor="l.anchor" class="axis">{{ l.text }}</text>
      </template>
      <text v-else :x="width / 2" :y="height / 2" text-anchor="middle" class="axis">No entries yet</text>
    </svg>
    <div v-if="hover" class="tip" :style="{ left: `${(hover.x / width) * 100}%` }">
      <span class="tip-date">{{ hover.week ? 'Week of ' : '' }}{{ shortDate(hover.date) }}</span>
      <span class="tip-val">{{ fmt(hover.value) }}<template v-if="unit"> {{ unit }}</template></span>
      <span v-if="geometry?.mode === 'rolling'" class="tip-date">7 day average {{ fmt(hover.avg) }}</span>
      <span v-else-if="hover.week" class="tip-date">weekly average</span>
    </div>
  </div>
</template>

<style scoped>
.wrap { position: relative; width: 100%; min-width: 0; touch-action: pan-y; }
.chart { width: 100%; display: block; overflow: visible; }
.grid line { stroke: var(--line); stroke-width: 1; }
.grid text, .axis { font-size: 11px; fill: var(--ink-3); font-variant-numeric: tabular-nums; }
.target line { stroke: var(--ink-4); stroke-width: 1; stroke-dasharray: 3 3; }
.target text { font-size: 11px; fill: var(--ink-3); }
.line { fill: none; stroke: var(--c); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.dot { fill: var(--c); stroke: var(--surface); stroke-width: 2; }
.end { font-size: 12px; font-weight: 600; fill: var(--ink); font-variant-numeric: tabular-nums; }
.cross { stroke: var(--ink-4); stroke-width: 1; }
.days circle { fill: var(--c); opacity: 0.22; }
.tip { position: absolute; top: -6px; transform: translate(-50%, -100%); display: flex; flex-direction: column; align-items: center; padding: 6px 10px; border-radius: 10px; background: var(--surface); box-shadow: 0 4px 16px rgb(0 0 0 / 0.12), 0 0 0 0.5px var(--line-2); pointer-events: none; white-space: nowrap; z-index: 2; }
.tip-date { font-size: var(--fs-xs); color: var(--ink-3); }
.tip-val { font-size: var(--fs-md); font-weight: 600; color: var(--ink); }
</style>
