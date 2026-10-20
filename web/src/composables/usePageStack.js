// iOS page stack for the phone shell: push and pop transitions between routes, and the
// interactive swipe back from the left edge.
//
// Transitions run both pages at once. The leaving page is frozen in place (position fixed at
// the spot it occupied) so the router can scroll the arriving page to its own position
// underneath without the old one jumping. A push slides the new page in from the right over
// the old one, which drifts a third to the left and dims; a pop is the reverse.
//
// Swipe back needs the previous page on screen while the finger drags, but that page is gone.
// So on every push a static copy of the leaving page is kept (keyed by its history position).
// The drag shows that copy underneath, moved by the finger like UINavigationController does;
// past half the width or on a flick, the gesture finishes the slide and the router goes back
// without a second animation, and the real page renders exactly where the copy was.
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createSpring, reducedMotion } from '../lib/spring'
import { isRoot, navState } from '../lib/nav'
import { isStandalone } from '../lib/push'
import { tick } from '../lib/haptics'

const EDGE = 24
const snapshots = new Map() // history position -> { node, rect }

function position() {
  return window.history.state?.position ?? 0
}

export function usePageStack(phone) {
  const router = useRouter()

  const transitionName = computed(() => {
    if (!phone.value) return 'route'
    if (navState.instant || reducedMotion()) return 'ios-none'
    if (navState.direction === 'push') return 'ios-push'
    if (navState.direction === 'pop') return 'ios-pop'
    return 'ios-none'
  })
  const mode = computed(() => (phone.value ? undefined : 'out-in'))

  function onBeforeLeave(el) {
    if (!phone.value || !(el instanceof HTMLElement)) return
    const rect = el.getBoundingClientRect()
    if (navState.direction === 'push') {
      const copy = el.cloneNode(true)
      copy.removeAttribute('id')
      snapshots.set(position() - 1, { node: copy, rect: { top: rect.top, left: rect.left, width: rect.width } })
      for (const key of [...snapshots.keys()]) if (key < position() - 8 || key >= position()) snapshots.delete(key)
    }
    el.dataset.leaving = '1'
    Object.assign(el.style, { position: 'fixed', top: `${rect.top}px`, left: `${rect.left}px`, width: `${rect.width}px`, margin: '0', pointerEvents: 'none', zIndex: navState.direction === 'pop' ? '3' : '1' })
  }

  // ---- Swipe back ------------------------------------------------------------------------
  let gesture = null
  const enabled = () => phone.value && (isStandalone() || localStorage.getItem('pozzy.swipeBack') === '1')

  function currentPage() {
    return document.querySelector('main.page > :not([data-leaving])')
  }

  function start(e) {
    if (gesture || !enabled() || e.touches.length !== 1) return
    const t = e.touches[0]
    if (t.clientX > EDGE || isRoot(router.currentRoute.value.name) || !window.history.state?.back) return
    if (document.documentElement.classList.contains('sheet-open')) return
    gesture = { x0: t.clientX, y0: t.clientY, active: false, samples: [] }
  }

  function begin() {
    const page = currentPage()
    if (!page) return false
    const width = window.innerWidth
    const snap = snapshots.get(position() - 1)
    let under = null
    if (snap) {
      under = snap.node.cloneNode(true)
      under.setAttribute('aria-hidden', 'true')
      under.classList.add('ios-under')
      Object.assign(under.style, { position: 'fixed', top: `${snap.rect.top}px`, left: `${snap.rect.left}px`, width: `${snap.rect.width}px`, margin: '0', zIndex: '0', pointerEvents: 'none' })
      page.parentElement.insertBefore(under, page)
    }
    page.classList.add('ios-dragging')
    gesture.page = page
    gesture.under = under
    gesture.width = width
    gesture.spring = createSpring({ value: 0, damping: 1, response: 0.35, onUpdate: paint })
    return true
  }

  function paint(x) {
    const g = gesture
    if (!g?.page) return
    const p = Math.max(0, Math.min(1, x / g.width))
    g.page.style.transform = `translate3d(${x}px, 0, 0)`
    if (g.under) {
      g.under.style.transform = `translate3d(${-0.3 * g.width * (1 - p)}px, 0, 0)`
      g.under.style.filter = `brightness(${0.94 + 0.06 * p})`
    }
  }

  function move(e) {
    if (!gesture) return
    const t = e.touches[0]
    const dx = t.clientX - gesture.x0
    const dy = t.clientY - gesture.y0
    if (!gesture.active) {
      if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return
      if (Math.abs(dy) > Math.abs(dx) || dx < 0 || !begin()) {
        gesture = null
        return
      }
      gesture.active = true
    }
    e.preventDefault()
    const now = performance.now()
    gesture.samples.push({ t: now, x: t.clientX })
    gesture.samples = gesture.samples.filter((s) => now - s.t < 100)
    gesture.spring.jump(Math.max(0, dx))
  }

  function finish(commit, velocity) {
    const g = gesture
    g.spring.set(commit ? g.width : 0, { velocity })
    const done = () => {
      if (commit) {
        tick()
        navState.instant = true
        router.back()
        // The real page renders where the copy is; drop the copy once it has painted.
        setTimeout(() => {
          g.under?.remove()
          navState.instant = false
        }, 120)
      } else {
        g.under?.remove()
        g.page.classList.remove('ios-dragging')
        g.page.style.transform = ''
      }
      gesture = null
    }
    if (reducedMotion()) return done()
    const check = () => (Math.abs(g.spring.value - (commit ? g.width : 0)) < 1 && !g.spring.running ? done() : requestAnimationFrame(check))
    requestAnimationFrame(check)
  }

  function end() {
    if (!gesture) return
    if (!gesture.active) {
      gesture = null
      return
    }
    const s = gesture.samples
    const v = s.length > 1 ? ((s[s.length - 1].x - s[0].x) / Math.max(1, s[s.length - 1].t - s[0].t)) * 1000 : 0
    const x = gesture.spring.value
    const commit = v > 300 || (x > gesture.width / 2 && v > -200)
    finish(commit, v)
  }

  onMounted(() => {
    document.addEventListener('touchstart', start, { passive: true })
    document.addEventListener('touchmove', move, { passive: false })
    document.addEventListener('touchend', end)
    document.addEventListener('touchcancel', end)
  })
  onBeforeUnmount(() => {
    document.removeEventListener('touchstart', start)
    document.removeEventListener('touchmove', move)
    document.removeEventListener('touchend', end)
    document.removeEventListener('touchcancel', end)
  })

  return { transitionName, mode, onBeforeLeave }
}
