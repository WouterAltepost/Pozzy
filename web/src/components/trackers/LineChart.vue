<script setup>
import { computed } from 'vue'

// Tiny inline SVG line chart. points: [{ date, value }]. No library, per BUILD.md.
// Geometry is unchanged from v1; only colours moved to tokens.
const props = defineProps({
  points: { type: Array, default: () => [] },
  target: { type: Number, default: null },
  unit: { type: String, default: '' },
  width: { type: Number, default: 520 },
  height: { type: Number, default: 140 },
})

const pad = { l: 36, r: 8, t: 8, b: 20 }

const geometry = computed(() => {
  const pts = props.points.filter((p) => typeof p.value === 'number')
  if (!pts.length) return null
  const xs = pts.map((p) => new Date(p.date).getTime())
  const ys = pts.map((p) => p.value)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  let minY = Math.min(...ys, props.target ?? Infinity)
  let maxY = Math.max(...ys, props.target ?? -Infinity)
  if (minY === maxY) { minY -= 1; maxY += 1 }
  const span = maxY - minY
  minY -= span * 0.1
  maxY += span * 0.1
  const w = props.width - pad.l - pad.r
  const h = props.height - pad.t - pad.b
  const sx = (x) => pad.l + (maxX === minX ? w / 2 : ((x - minX) / (maxX - minX)) * w)
  const sy = (y) => pad.t + h - ((y - minY) / (maxY - minY)) * h
  const coords = pts.map((p, i) => ({ x: sx(xs[i]), y: sy(p.value), ...p }))
  const path = coords.map((c, i) => `${i ? 'L' : 'M'}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' ')
  const ticks = [minY + span * 0.1, (minY + maxY) / 2, maxY - span * 0.1].map((v) => ({ v, y: sy(v) }))
  return { coords, path, targetY: props.target != null ? sy(props.target) : null, ticks, first: pts[0].date, last: pts[pts.length - 1].date }
})

const fmt = (v) => (Math.abs(v) >= 100 ? Math.round(v) : Math.round(v * 10) / 10)
</script>

<template>
  <svg :viewBox="`0 0 ${width} ${height}`" class="chart" preserveAspectRatio="none" role="img" :aria-label="points.length ? `${points.length} entries` : 'No entries yet'">
    <template v-if="geometry">
      <g class="grid">
        <line v-for="t in geometry.ticks" :key="t.v" :x1="pad.l" :x2="width - pad.r" :y1="t.y" :y2="t.y" />
        <text v-for="t in geometry.ticks" :key="'l' + t.v" :x="pad.l - 4" :y="t.y + 3" text-anchor="end">{{ fmt(t.v) }}</text>
      </g>
      <line v-if="geometry.targetY != null" class="target" :x1="pad.l" :x2="width - pad.r" :y1="geometry.targetY" :y2="geometry.targetY" />
      <path :d="geometry.path" class="line" />
      <circle v-for="c in geometry.coords" :key="c.date" :cx="c.x" :cy="c.y" r="2.5" class="dot">
        <title>{{ c.date }}: {{ c.value }} {{ unit }}</title>
      </circle>
      <text :x="pad.l" :y="height - 4" class="axis">{{ geometry.first }}</text>
      <text :x="width - pad.r" :y="height - 4" class="axis" text-anchor="end">{{ geometry.last }}</text>
    </template>
    <text v-else :x="width / 2" :y="height / 2" text-anchor="middle" class="axis">No entries yet</text>
  </svg>
</template>

<style scoped>
.chart { width: 100%; height: 140px; display: block; }
.grid line { stroke: var(--line); stroke-width: 1; }
.grid text, .axis { font-size: 10px; fill: var(--ink-3); font-variant-numeric: tabular-nums; }
.target { stroke: var(--brand); stroke-dasharray: 4 3; stroke-width: 1; }
.line { fill: none; stroke: var(--ink); stroke-width: 1.5; }
.dot { fill: var(--ink); }
</style>
