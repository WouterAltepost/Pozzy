// Pointer drag with capture, a movement threshold before it commits to an axis, and a short
// velocity history so the release speed can be handed to a spring. Returns handlers to spread on
// the element (v-bind) and a `dragging` flag. Callbacks get pixels and pixels per second.
//
//   const drag = useDrag({ axis: 'x', onMove: ({ dx }) => ..., onEnd: ({ dx, vx }) => ... })
//   <div v-bind="drag.handlers" />
import { ref } from 'vue'

const THRESHOLD = 8
const HISTORY_MS = 100

export function useDrag({ axis = 'x', onStart, onMove, onEnd, onCancel, enabled = () => true } = {}) {
  const dragging = ref(false)
  let active = null

  function velocityFrom(history, key) {
    const now = performance.now()
    // A finger that stopped and held has no velocity, however fast it moved before.
    if (!history.length || now - history[history.length - 1].t > 60) return 0
    const recent = history.filter((h) => now - h.t <= HISTORY_MS)
    if (recent.length < 2) return 0
    const a = recent[0]
    const b = recent[recent.length - 1]
    const dt = (b.t - a.t) / 1000
    return dt > 0 ? (b[key] - a[key]) / dt : 0
  }

  function down(e) {
    if (!enabled(e) || (e.pointerType === 'mouse' && e.button !== 0)) return
    active = { id: e.pointerId, x0: e.clientX, y0: e.clientY, committed: false, history: [{ t: performance.now(), x: e.clientX, y: e.clientY }], target: e.currentTarget }
  }
  function move(e) {
    if (!active || e.pointerId !== active.id) return
    const dx = e.clientX - active.x0
    const dy = e.clientY - active.y0
    if (!active.committed) {
      const main = axis === 'x' ? Math.abs(dx) : Math.abs(dy)
      const cross = axis === 'x' ? Math.abs(dy) : Math.abs(dx)
      if (main < THRESHOLD) return
      if (cross > main) {
        // The user is scrolling the other way; let the browser have it.
        active = null
        return
      }
      active.committed = true
      dragging.value = true
      try {
        active.target.setPointerCapture(active.id)
      } catch {}
      onStart?.({ x: e.clientX, y: e.clientY })
    }
    active.history.push({ t: performance.now(), x: e.clientX, y: e.clientY })
    if (active.history.length > 12) active.history.shift()
    onMove?.({ dx, dy, x: e.clientX, y: e.clientY })
    if (active.committed) e.preventDefault()
  }
  function up(e) {
    if (!active || e.pointerId !== active.id) return
    const a = active
    active = null
    if (!a.committed) return
    dragging.value = false
    const dx = e.clientX - a.x0
    const dy = e.clientY - a.y0
    onEnd?.({ dx, dy, vx: velocityFrom(a.history, 'x'), vy: velocityFrom(a.history, 'y') })
  }
  function cancel(e) {
    if (!active || (e && e.pointerId !== active.id)) return
    const a = active
    active = null
    if (!a.committed) return
    dragging.value = false
    onCancel?.() ?? onEnd?.({ dx: 0, dy: 0, vx: 0, vy: 0 })
  }

  return {
    dragging,
    handlers: { onPointerdown: down, onPointermove: move, onPointerup: up, onPointercancel: cancel },
    // A click that follows a drag must not count as a tap.
    wasDrag: () => dragging.value,
  }
}
