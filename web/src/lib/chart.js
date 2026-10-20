// Small helpers for the hand-drawn SVG charts (no chart library).

// A smooth line through the points that never overshoots them (monotone cubic, Fritsch and
// Carlson): a week at 100% never draws a bump above 100. Points: [{ x, y }] sorted by x.
export function smoothPath(pts) {
  if (!pts.length) return ''
  if (pts.length === 1) return `M${pts[0].x},${pts[0].y}`
  const n = pts.length
  const dx = []
  const slope = []
  for (let i = 0; i < n - 1; i++) {
    dx[i] = pts[i + 1].x - pts[i].x
    slope[i] = dx[i] ? (pts[i + 1].y - pts[i].y) / dx[i] : 0
  }
  const m = [slope[0]]
  for (let i = 1; i < n - 1; i++) m[i] = slope[i - 1] * slope[i] <= 0 ? 0 : (slope[i - 1] + slope[i]) / 2
  m[n - 1] = slope[n - 2]
  for (let i = 0; i < n - 1; i++) {
    if (slope[i] === 0) {
      m[i] = 0
      m[i + 1] = 0
      continue
    }
    const a = m[i] / slope[i]
    const b = m[i + 1] / slope[i]
    const h = a * a + b * b
    if (h > 9) {
      const t = 3 / Math.sqrt(h)
      m[i] = t * a * slope[i]
      m[i + 1] = t * b * slope[i]
    }
  }
  let d = `M${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)}`
  for (let i = 0; i < n - 1; i++) {
    const c1x = pts[i].x + dx[i] / 3
    const c1y = pts[i].y + (m[i] * dx[i]) / 3
    const c2x = pts[i + 1].x - dx[i] / 3
    const c2y = pts[i + 1].y - (m[i + 1] * dx[i]) / 3
    d += ` C${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${pts[i + 1].x.toFixed(1)},${pts[i + 1].y.toFixed(1)}`
  }
  return d
}

// The same curve closed down to the baseline, for the area wash under a line.
export function areaPath(pts, baseY) {
  if (pts.length < 2) return ''
  return `${smoothPath(pts)} L${pts[pts.length - 1].x.toFixed(1)},${baseY} L${pts[0].x.toFixed(1)},${baseY} Z`
}

// "7 Sep" for an ISO date, the short label under a time axis.
export function shortDate(iso) {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

// Clean axis ticks for a value range: three round numbers covering [lo, hi].
export function niceTicks(lo, hi, count = 3) {
  const span = hi - lo || Math.abs(hi) || 1
  const raw = span / (count - 1)
  const mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map((s) => s * mag).find((s) => s >= raw) || raw
  const start = Math.floor(lo / step) * step
  const ticks = []
  for (let v = start; v <= hi + step * 0.001 && ticks.length < 8; v += step) ticks.push(Math.round(v * 1000) / 1000)
  if (ticks[ticks.length - 1] < hi) ticks.push(Math.round((ticks[ticks.length - 1] + step) * 1000) / 1000)
  return ticks
}
