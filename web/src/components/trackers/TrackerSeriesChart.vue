<script setup>
// Live chart of every habit on one scale: per week, how much of its target each habit hit.
// Daily habits: days done out of seven. Weekly counts: sum over target. Numeric with a daily
// target: weekly average over target. Numeric without a target: scaled to its own best week
// (marked in the legend). Legend chips toggle series; hidden set and range persist per device.
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { trackerSeries } from '../../api/trackers'
import UiSegmented from '../ui/UiSegmented.vue'

const props = defineProps({ refreshKey: { type: [Number, String, Object], default: 0 } })

const PALETTE = ['#2563EB', '#DC2626', '#059669', '#D97706', '#7C3AED', '#DB2777', '#0891B2', '#65A30D']
const RANGES = [
  { value: '4', label: '4w' },
  { value: '12', label: '12w' },
  { value: '26', label: '26w' },
  { value: 'all', label: 'All' },
]
const read = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d } catch { return d } }
const write = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)) } catch {} }

const range = ref(String(read('pozzy.trackers.range', '12')))
const hidden = ref(new Set(read('pozzy.trackers.hidden', [])))
const data = ref(null)
const error = ref('')
const wrap = ref(null)
const width = ref(720)
const height = 220
const pad = { l: 36, r: 12, t: 12, b: 24 }
const hover = ref(null) // week index
let observer = null

async function load() {
  error.value = ''
  try {
    data.value = await trackerSeries(range.value === 'all' ? 'all' : Number(range.value))
  } catch (err) {
    error.value = err.message
  }
}
watch(range, (v) => { write('pozzy.trackers.range', v); load() })
watch(() => props.refreshKey, load)
onMounted(() => {
  load()
  width.value = Math.max(320, wrap.value?.clientWidth || 720)
  observer = new ResizeObserver((entries) => {
    const w = entries[0]?.contentRect?.width
    if (w) width.value = Math.max(320, Math.round(w))
  })
  if (wrap.value) observer.observe(wrap.value)
})
onBeforeUnmount(() => observer?.disconnect())

function toggle(id) {
  const next = new Set(hidden.value)
  next.has(id) ? next.delete(id) : next.add(id)
  hidden.value = next
  write('pozzy.trackers.hidden', [...next])
}
function showAll(on) {
  hidden.value = on ? new Set() : new Set(series.value.map((s) => s.id))
  write('pozzy.trackers.hidden', [...hidden.value])
}

// Percent of target per week plus a human label for the tooltip.
const series = computed(() => {
  if (!data.value) return []
  return data.value.series.map((s, i) => {
    const t = s.tracker
    const color = PALETTE[i % PALETTE.length]
    let scaled = false
    let pct
    let label
    if (t.type === 'daily_bool') {
      pct = s.weekly.map((w) => (w.count ? (w.met_days / 7) * 100 : null))
      label = (w) => (w.count ? `${w.met_days} of 7 days` : 'no entries')
    } else if (t.type === 'weekly_count') {
      const target = t.target_value || null
      if (target) {
        pct = s.weekly.map((w) => (w.count ? (w.sum / target) * 100 : null))
        label = (w) => (w.count ? `${round(w.sum)} of ${target}` : 'no entries')
      } else {
        scaled = true
        const best = Math.max(...s.weekly.map((w) => w.sum), 0) || 1
        pct = s.weekly.map((w) => (w.count ? (w.sum / best) * 100 : null))
        label = (w) => (w.count ? `${round(w.sum)}` : 'no entries')
      }
    } else {
      const unit = t.unit ? ' ' + t.unit : ''
      const target = t.target_period === 'day' && t.target_value ? t.target_value : null
      if (target) {
        pct = s.weekly.map((w) => (w.count ? (w.avg / target) * 100 : null))
        label = (w) => (w.count ? `avg ${round(w.avg)}${unit} of ${target}${unit}` : 'no entries')
      } else {
        scaled = true
        const best = Math.max(...s.weekly.map((w) => w.avg || 0), 0) || 1
        pct = s.weekly.map((w) => (w.count ? (w.avg / best) * 100 : null))
        label = (w) => (w.count ? `avg ${round(w.avg)}${unit}` : 'no entries')
      }
    }
    return { id: t.id, name: t.name, type: t.type, color, scaled, pct, label, weekly: s.weekly }
  })
})
const visible = computed(() => series.value.filter((s) => !hidden.value.has(s.id)))
const weeks = computed(() => data.value?.series[0]?.weekly.map((w) => w.week_start) || [])
const round = (v) => (Math.abs(v) >= 100 ? Math.round(v) : Math.round(v * 10) / 10)

const geometry = computed(() => {
  const n = weeks.value.length
  if (!n) return null
  const maxPct = Math.max(100, ...visible.value.flatMap((s) => s.pct.filter((v) => v !== null)))
  const top = Math.ceil(maxPct / 50) * 50
  const w = width.value - pad.l - pad.r
  const h = height - pad.t - pad.b
  const sx = (i) => pad.l + (n === 1 ? w / 2 : (i / (n - 1)) * w)
  const sy = (v) => pad.t + h - (v / top) * h
  const lines = visible.value.map((s) => {
    const pts = s.pct.map((v, i) => (v === null ? null : { x: sx(i), y: sy(v), i }))
    let d = ''
    let pen = false
    for (const p of pts) {
      if (!p) { pen = false; continue }
      d += `${pen ? 'L' : 'M'}${p.x.toFixed(1)},${p.y.toFixed(1)} `
      pen = true
    }
    return { ...s, d, dots: pts.filter(Boolean) }
  })
  const ticks = []
  for (let v = 0; v <= top; v += 50) ticks.push({ v, y: sy(v) })
  const labels = n <= 8 ? weeks.value.map((d, i) => ({ d, x: sx(i) })) : [0, Math.floor((n - 1) / 2), n - 1].map((i) => ({ d: weeks.value[i], x: sx(i) }))
  return { lines, ticks, labels, sx, targetY: sy(100), n }
})

function onMove(e) {
  const g = geometry.value
  if (!g || !wrap.value) return
  const rect = wrap.value.getBoundingClientRect()
  const x = ((e.clientX - rect.left) / rect.width) * width.value
  let best = 0
  let dist = Infinity
  for (let i = 0; i < g.n; i++) {
    const d = Math.abs(g.sx(i) - x)
    if (d < dist) { dist = d; best = i }
  }
  hover.value = best
}
const tip = computed(() => {
  if (hover.value === null || !geometry.value) return null
  const i = hover.value
  const x = geometry.value.sx(i)
  return {
    week: weeks.value[i],
    left: x > width.value * 0.6 ? undefined : `${(x / width.value) * 100}%`,
    right: x > width.value * 0.6 ? `${100 - (x / width.value) * 100}%` : undefined,
    x,
    rows: visible.value.map((s) => ({ name: s.name, color: s.color, text: s.label(s.weekly[i]), pct: s.pct[i] })),
  }
})
</script>

<template>
  <section class="card chart-card">
    <div class="card-head">
      <h2>All habits</h2>
      <span class="meta">
        <span class="muted small">percent of target per week</span>
        <UiSegmented v-model="range" :options="RANGES" />
      </span>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <div ref="wrap" class="plot" @pointermove="onMove" @pointerleave="hover = null">
      <svg v-if="geometry" :viewBox="`0 0 ${width} ${height}`" :style="{ height: height + 'px' }" role="img" :aria-label="`${visible.length} habits over ${geometry.n} weeks`">
        <g class="grid">
          <line v-for="t in geometry.ticks" :key="t.v" :x1="pad.l" :x2="width - pad.r" :y1="t.y" :y2="t.y" :class="{ target: t.v === 100 }" />
          <text v-for="t in geometry.ticks" :key="'l' + t.v" :x="pad.l - 6" :y="t.y + 3" text-anchor="end">{{ t.v }}%</text>
        </g>
        <line v-if="tip" class="guide" :x1="tip.x" :x2="tip.x" :y1="pad.t" :y2="height - pad.b" />
        <g v-for="s in geometry.lines" :key="s.id" class="series" :style="{ color: s.color }">
          <path :d="s.d" class="line" />
          <circle v-for="p in s.dots" :key="p.i" :cx="p.x" :cy="p.y" :r="hover === p.i ? 4 : 2.5" class="dot" />
        </g>
        <text v-for="l in geometry.labels" :key="l.d" :x="l.x" :y="height - 6" class="axis" :text-anchor="l.x < pad.l + 20 ? 'start' : l.x > width - pad.r - 20 ? 'end' : 'middle'">{{ l.d.slice(5) }}</text>
      </svg>
      <p v-else-if="data" class="muted small empty">No trackers yet.</p>
      <div v-if="tip" class="tip" :style="{ left: tip.left, right: tip.right }">
        <div class="tip-week num">Week of {{ tip.week }}</div>
        <div v-for="r in tip.rows" :key="r.name" class="tip-row">
          <span class="swatch" :style="{ background: r.color }"></span>
          <span class="tip-name">{{ r.name }}</span>
          <span class="muted num">{{ r.text }}</span>
        </div>
      </div>
    </div>
    <div class="legend">
      <button v-for="s in series" :key="s.id" type="button" class="chip" :class="{ off: hidden.has(s.id) }" :aria-pressed="!hidden.has(s.id)" @click="toggle(s.id)">
        <span class="swatch" :style="{ background: s.color }"></span>{{ s.name }}<span v-if="s.scaled" class="muted xs"> scaled</span>
      </button>
      <span v-if="series.length > 1" class="legend-actions">
        <button type="button" class="link-btn" @click="showAll(true)">all</button>
        <button type="button" class="link-btn" @click="showAll(false)">none</button>
      </span>
    </div>
  </section>
</template>

<style scoped>
.chart-card { padding-bottom: var(--sp-3); }
.meta { display: inline-flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.plot { position: relative; width: 100%; min-width: 0; touch-action: pan-y; }
.plot svg { width: 100%; display: block; }
.grid line { stroke: var(--line); stroke-width: 1; }
.grid line.target { stroke: var(--ink-3); stroke-dasharray: 4 3; }
.grid text, .axis { font-size: 10px; fill: var(--ink-3); font-variant-numeric: tabular-nums; }
.guide { stroke: var(--ink-3); stroke-width: 1; stroke-dasharray: 2 3; }
.line { fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linejoin: round; stroke-linecap: round; }
.dot { fill: currentColor; transition: r var(--dur-hover) ease; }
.series { opacity: 0.95; }
.empty { padding: var(--sp-5) 0; text-align: center; }
.tip { position: absolute; top: 8px; z-index: 2; pointer-events: none; background: color-mix(in srgb, var(--surface) 92%, transparent); -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px); border: 1px solid var(--line); border-radius: var(--r-md); box-shadow: var(--shadow-2); padding: var(--sp-2) var(--sp-3); font-size: var(--fs-sm); min-width: 180px; transform: translateX(12px); }
.tip[style*="right"] { transform: translateX(-12px); }
.tip-week { font-weight: 500; margin-bottom: 4px; }
.tip-row { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 6px; align-items: center; }
.swatch { display: inline-block; width: 9px; height: 9px; border-radius: 50%; }
.legend { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: var(--sp-3); }
.chip { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 10px; border: 1px solid var(--line); border-radius: var(--r-pill); background: var(--surface); color: var(--ink); font: inherit; font-size: var(--fs-sm); font-weight: 500; cursor: pointer; transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease, border-color var(--dur-hover) ease, opacity var(--dur-hover) ease; }
.chip.off { color: var(--ink-3); border-style: dashed; }
.chip.off .swatch { opacity: 0.35; }
@media (hover: hover) and (pointer: fine) { .chip:hover { border-color: var(--line-2); } }
.legend-actions { display: inline-flex; gap: var(--sp-2); margin-left: auto; }
</style>
