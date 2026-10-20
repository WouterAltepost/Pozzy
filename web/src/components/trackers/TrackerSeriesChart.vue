<script setup>
// Consistency: how much of each habit's target was met, week by week. Eight lines on one scale
// read as spaghetti, so the card leads with one number (this week so far, against last week),
// then a single smooth line of the overall rate, then a grid with one row per habit and one
// cell per week, a single hue that deepens with completion (light to dark, the safe encoding
// for magnitude). Weeks before a habit started are left blank; the running week is outlined
// because it is not finished. Hover a cell or the line for the numbers; every cell carries its
// value as a label, so nothing hides behind a tooltip.
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { PhArrowDownRight, PhArrowUpRight } from '@phosphor-icons/vue'
import { trackerSeries } from '../../api/trackers'
import UiSegmented from '../ui/UiSegmented.vue'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { areaPath, shortDate, smoothPath } from '../../lib/chart'

const props = defineProps({ refreshKey: { type: [Number, String, Object], default: 0 } })

const phone = useMediaQuery('(max-width: 699px)')
// A phone fits about twelve cells across beside the names; the desktop goes to half a year.
const RANGES = computed(() =>
  phone.value
    ? [{ value: '4', label: '4w' }, { value: '8', label: '8w' }, { value: '12', label: '12w' }]
    : [{ value: '4', label: '4w' }, { value: '12', label: '12w' }, { value: '26', label: '26w' }],
)
const read = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d } catch { return d } }
const write = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)) } catch {} }

const range = ref(String(read('pozzy.consistency.range', '12')))
const data = ref(null)
const error = ref('')
watch(RANGES, (opts) => {
  if (!opts.some((o) => o.value === range.value)) range.value = '12'
}, { immediate: true })

async function load() {
  error.value = ''
  try {
    data.value = await trackerSeries(Number(range.value))
  } catch (err) {
    error.value = err.message
  }
}
watch(range, (v) => { write('pozzy.consistency.range', v); load() })
watch(() => props.refreshKey, load)
onMounted(load)

const round = (v) => (Math.abs(v) >= 100 ? Math.round(v) : Math.round(v * 10) / 10)

// Per habit and week: share of the target met (raw, may pass 100) and a readable sentence.
const series = computed(() => {
  if (!data.value) return []
  return data.value.series.map((s) => {
    const t = s.tracker
    let scaled = false
    let pct
    let label
    if (t.type === 'daily_bool') {
      pct = s.weekly.map((w) => (w.started && w.due_days ? (w.met_days / w.due_days) * 100 : null))
      label = (w) => (w.due_days ? `${w.met_days} of ${w.due_days} due days` : 'nothing due')
    } else if (t.type === 'weekly_count') {
      const target = t.target_value || null
      if (target) {
        pct = s.weekly.map((w) => (w.started ? (w.sum / target) * 100 : null))
        label = (w) => `${round(w.sum)} of ${target}`
      } else {
        scaled = true
        const best = Math.max(...s.weekly.map((w) => w.sum), 0) || 1
        pct = s.weekly.map((w) => (w.started ? (w.sum / best) * 100 : null))
        label = (w) => `${round(w.sum)}`
      }
    } else {
      const unit = t.unit ? ' ' + t.unit : ''
      const target = t.target_period === 'day' && t.target_value ? t.target_value : null
      if (target) {
        pct = s.weekly.map((w) => (!w.started ? null : w.count ? (w.avg / target) * 100 : 0))
        label = (w) => (w.count ? `average ${round(w.avg)}${unit} of ${target}${unit}` : 'nothing logged')
      } else {
        scaled = true
        const best = Math.max(...s.weekly.map((w) => w.avg || 0), 0) || 1
        pct = s.weekly.map((w) => (w.count ? (w.avg / best) * 100 : null))
        label = (w) => (w.count ? `average ${round(w.avg)}${unit}` : 'nothing logged')
      }
    }
    // The running week with nothing logged has not happened yet for a count or value habit.
    const last = s.weekly.length - 1
    if (t.type !== 'daily_bool' && last >= 0 && !s.weekly[last].count) pct[last] = null
    return { id: t.id, name: t.name, scaled, pct, label, weekly: s.weekly }
  })
})

// Start at the first week any habit had begun, so a young set of habits fills the width.
const first = computed(() => {
  const n = data.value?.weeks || 0
  for (let i = 0; i < n; i++) if (series.value.some((s) => s.pct[i] !== null)) return i
  return Math.max(0, n - 1)
})
const weeks = computed(() => (data.value?.series[0]?.weekly.map((w) => w.week_start) || []).slice(first.value))
const rows = computed(() => series.value.map((s) => ({ ...s, cells: s.pct.slice(first.value).map((p, i) => ({ pct: p, week: weeks.value[i], text: p === null ? null : s.label(s.weekly[i + first.value]) })) })))

// Overall rate per week: the mean of every habit with a target, each capped at 100%.
const overall = computed(() =>
  weeks.value.map((_, i) => {
    const vals = rows.value.filter((r) => !r.scaled).map((r) => r.cells[i].pct).filter((p) => p !== null)
    return vals.length ? vals.reduce((a, p) => a + Math.min(100, p), 0) / vals.length : null
  }),
)
const thisWeek = computed(() => overall.value[overall.value.length - 1] ?? null)
const lastWeek = computed(() => overall.value[overall.value.length - 2] ?? null)
const delta = computed(() => (thisWeek.value === null || lastWeek.value === null ? null : Math.round(thisWeek.value) - Math.round(lastWeek.value)))

// Five steps of one hue: nothing, a little, half, most, all of it.
function level(p) {
  if (p === null) return 'na'
  if (p <= 0) return 'l0'
  if (p < 34) return 'l1'
  if (p < 67) return 'l2'
  if (p < 100) return 'l3'
  return 'l4'
}

// ---- Trend line (finished weeks only) ----
const plot = ref(null)
const width = ref(600)
const HEIGHT = 132
const pad = { l: 34, r: 12, t: 12, b: 22 }
let observer = null
onMounted(() => {
  observer = new ResizeObserver((e) => {
    const w = e[0]?.contentRect?.width
    if (w) width.value = Math.max(240, Math.round(w))
  })
  if (plot.value) observer.observe(plot.value)
})
onBeforeUnmount(() => observer?.disconnect())
watch(plot, (el) => el && observer?.observe(el))

const trend = computed(() => {
  const done = overall.value.slice(0, -1)
  const n = done.length
  if (n < 2) return null
  const w = width.value - pad.l - pad.r
  const h = HEIGHT - pad.t - pad.b
  const sx = (i) => pad.l + (i / (n - 1)) * w
  const sy = (v) => pad.t + h - (v / 100) * h
  const pts = done.map((v, i) => (v === null ? null : { x: sx(i), y: sy(v), v, i })).filter(Boolean)
  if (pts.length < 2) return null
  const lastPt = pts[pts.length - 1]
  const labels = [0, Math.round((n - 1) / 2), n - 1].filter((v, i, a) => a.indexOf(v) === i).map((i) => ({ x: sx(i), text: shortDate(weeks.value[i]), anchor: i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle' }))
  return { pts, line: smoothPath(pts), area: areaPath(pts, sy(0)), grid: [0, 50, 100].map((v) => ({ v, y: sy(v) })), labels, lastPt }
})
const hover = ref(null)
function onMove(e) {
  const t = trend.value
  if (!t || !plot.value) return
  const rect = plot.value.getBoundingClientRect()
  const x = ((e.clientX - rect.left) / rect.width) * width.value
  let best = null
  let dist = Infinity
  for (const p of t.pts) {
    const d = Math.abs(p.x - x)
    if (d < dist) { dist = d; best = p }
  }
  hover.value = best
}
const hoverWeek = computed(() => (hover.value ? shortDate(weeks.value[hover.value.i]) : ''))

// Month names over the grid, only where a new month starts.
const monthMarks = computed(() => weeks.value.map((w, i) => (i === 0 || w.slice(5, 7) !== weeks.value[i - 1].slice(5, 7) ? new Date(w + 'T12:00:00').toLocaleDateString('en-GB', { month: 'short' }) : '')))
</script>

<template>
  <section class="card consistency">
    <div class="head">
      <div>
        <h2>Consistency</h2>
        <p class="sub">Share of each habit's target met per week</p>
      </div>
      <UiSegmented v-model="range" :options="RANGES" />
    </div>
    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="rows.length && weeks.length">
      <div class="hero">
        <span class="hero-label">This week so far</span>
        <span class="hero-value">{{ thisWeek === null ? '-' : Math.round(thisWeek) + '%' }}</span>
        <span v-if="delta !== null" class="delta">
          <PhArrowUpRight v-if="delta > 0" class="up" weight="bold" /><PhArrowDownRight v-else-if="delta < 0" class="down" weight="bold" />
          {{ delta === 0 ? 'Same as' : (delta > 0 ? '+' : '') + delta + ' pts vs' }} last week
        </span>
      </div>

      <div ref="plot" class="plot" @pointermove="onMove" @pointerleave="hover = null">
        <svg v-if="trend" :viewBox="`0 0 ${width} ${HEIGHT}`" :style="{ height: HEIGHT + 'px' }" role="img" :aria-label="`Overall completion per finished week, last week ${Math.round(trend.lastPt.v)}%`">
          <defs>
            <linearGradient id="consistency-wash" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stop-color="var(--brand)" stop-opacity="0.18" />
              <stop offset="1" stop-color="var(--brand)" stop-opacity="0" />
            </linearGradient>
          </defs>
          <g class="grid">
            <line v-for="g in trend.grid" :key="g.v" :x1="pad.l" :x2="width - pad.r" :y1="g.y" :y2="g.y" />
            <text v-for="g in trend.grid" :key="'t' + g.v" :x="pad.l - 8" :y="g.y + 3.5" text-anchor="end">{{ g.v }}%</text>
          </g>
          <path :d="trend.area" fill="url(#consistency-wash)" />
          <path :d="trend.line" class="line" />
          <line v-if="hover" class="cross" :x1="hover.x" :x2="hover.x" :y1="pad.t" :y2="HEIGHT - pad.b" />
          <circle :cx="(hover || trend.lastPt).x" :cy="(hover || trend.lastPt).y" r="4.5" class="dot" />
          <text v-for="l in trend.labels" :key="l.text" :x="l.x" :y="HEIGHT - 4" :text-anchor="l.anchor" class="axis">{{ l.text }}</text>
        </svg>
        <p v-else class="muted small few">The trend line appears after two finished weeks.</p>
        <div v-if="hover" class="tip" :style="{ left: `${(hover.x / width) * 100}%` }">
          <span class="tip-week">Week of {{ hoverWeek }}</span>
          <span class="tip-val">{{ Math.round(hover.v) }}%</span>
        </div>
      </div>

      <div class="grid-wrap" role="table" :aria-label="`Habits by week, last ${weeks.length} weeks`">
        <div class="gr months" role="row" :style="{ '--n': weeks.length }">
          <span role="columnheader" class="gname"></span>
          <span v-for="(m, i) in monthMarks" :key="i" role="columnheader" class="mcell">{{ m }}</span>
          <span role="columnheader" class="gval">Now</span>
        </div>
        <div v-for="r in rows" :key="r.id" class="gr" role="row" :style="{ '--n': weeks.length }">
          <RouterLink :to="{ name: 'habit', params: { id: r.id } }" role="rowheader" class="gname truncate">{{ r.name }}</RouterLink>
          <span
            v-for="(c, i) in r.cells"
            :key="c.week"
            role="cell"
            class="cell"
            :class="[level(c.pct), { now: i === weeks.length - 1 }]"
            :title="c.pct === null ? `${r.name}, week of ${shortDate(c.week)}: not started` : `${r.name}, week of ${shortDate(c.week)}: ${Math.round(c.pct)}% (${c.text})`"
            :aria-label="c.pct === null ? `Week of ${shortDate(c.week)}: not started` : `Week of ${shortDate(c.week)}: ${Math.round(c.pct)}%, ${c.text}`"
          ></span>
          <span role="cell" class="gval num">{{ r.cells[r.cells.length - 1].pct === null ? '' : Math.min(999, Math.round(r.cells[r.cells.length - 1].pct)) + '%' }}</span>
        </div>
      </div>

      <div class="scale" aria-hidden="true">
        <span>Less</span>
        <i class="cell l0"></i><i class="cell l1"></i><i class="cell l2"></i><i class="cell l3"></i><i class="cell l4"></i>
        <span>More</span>
        <i class="cell l2 now key"></i><span>This week, still running</span>
      </div>
    </template>
    <p v-else-if="data" class="muted small few">No habits to show yet.</p>
  </section>
</template>

<style scoped>
.consistency { --c: var(--brand); }
.head { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-3); flex-wrap: wrap; margin-bottom: var(--sp-4); }
.head h2 { margin: 0; }
.sub { margin: 2px 0 0; font-size: var(--fs-sm); color: var(--ink-3); }

.hero { display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px 12px; margin-bottom: var(--sp-2); }
.hero-label { flex-basis: 100%; font-size: var(--fs-sm); color: var(--ink-3); }
.hero-value { font-size: 2.5rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.05; color: var(--ink); }
.delta { display: inline-flex; align-items: center; gap: 4px; font-size: var(--fs-md); color: var(--ink-2); }
.delta :deep(svg) { width: 14px; height: 14px; }
.delta .up { color: var(--ok); }
.delta .down { color: var(--warn); }

.plot { position: relative; width: 100%; min-width: 0; touch-action: pan-y; margin-bottom: var(--sp-5); }
.plot svg { width: 100%; display: block; overflow: visible; }
.grid line { stroke: var(--line); stroke-width: 1; }
.grid text, .axis { font-size: 11px; fill: var(--ink-3); font-variant-numeric: tabular-nums; }
.line { fill: none; stroke: var(--c); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.dot { fill: var(--c); stroke: var(--surface); stroke-width: 2; }
.cross { stroke: var(--ink-4); stroke-width: 1; }
.tip { position: absolute; top: -6px; transform: translate(-50%, -100%); display: flex; flex-direction: column; align-items: center; padding: 6px 10px; border-radius: 10px; background: var(--surface); box-shadow: 0 4px 16px rgb(0 0 0 / 0.12), 0 0 0 0.5px var(--line-2); pointer-events: none; white-space: nowrap; }
.tip-week { font-size: var(--fs-xs); color: var(--ink-3); }
.tip-val { font-size: var(--fs-md); font-weight: 600; color: var(--ink); }
.few { padding: var(--sp-3) 0; }

/* The grid: names, one square per week, this week's number. */
.grid-wrap { display: flex; flex-direction: column; gap: 3px; }
.gr { display: grid; grid-template-columns: 180px repeat(var(--n), 22px) 52px; align-items: center; gap: 4px; }
.gname { padding-right: 8px; font-size: var(--fs-md); color: var(--ink); text-decoration: none; }
.gname:hover { color: var(--brand); text-decoration: none; }
.gval { text-align: right; font-size: var(--fs-sm); color: var(--ink-2); }
.months { margin-bottom: 2px; }
.mcell { font-size: 10px; overflow: visible; white-space: nowrap; width: 0; color: var(--ink-3); white-space: nowrap; overflow: visible; }
.months .gval { font-size: 10px; color: var(--ink-3); }
.cell { display: block; width: 100%; max-width: 26px; aspect-ratio: 1; border-radius: 5px; justify-self: center; background: var(--surface-2); }
.cell.na { background: transparent; }
.cell.l0 { background: var(--surface-2); }
.cell.l1 { background: color-mix(in srgb, var(--c) 28%, var(--surface)); }
.cell.l2 { background: color-mix(in srgb, var(--c) 52%, var(--surface)); }
.cell.l3 { background: color-mix(in srgb, var(--c) 76%, var(--surface)); }
.cell.l4 { background: var(--c); }
.cell.now { box-shadow: 0 0 0 1.5px var(--surface), 0 0 0 3px color-mix(in srgb, var(--c) 45%, transparent); }
.cell.na.now { box-shadow: none; }

.scale { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; margin-top: var(--sp-4); font-size: var(--fs-xs); color: var(--ink-3); }
.scale .cell { width: 12px; height: 12px; max-width: none; border-radius: 3px; }
.scale span { margin: 0 4px; }
.scale .key { margin-left: 12px; }

@media (max-width: 1023px) {
  .head :deep(.seg) { flex: none; }
  .hero-value { font-size: 2.125rem; }
  .gr { grid-template-columns: minmax(72px, 108px) repeat(var(--n), minmax(0, 1fr)) 38px; gap: 3px; }
  .gname { font-size: 0.9375rem; }
}
</style>
