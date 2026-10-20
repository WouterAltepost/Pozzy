// iOS navigation model for the phone shell: four tabs, each the root of its own stack, pages
// pushed on top of a tab, and which way the next page change should animate.
//
// Today, Habits and Overview are tabs; every other module is pushed from More. A pushed page
// slides in from the right and leaves to the right on Back; switching tabs does not animate.
import { reactive } from 'vue'
import { NAV } from '../router'

export const TABS = ['home', 'trackers', 'overview', 'more']
const ROOTS = new Set(TABS)

export const LABELS = Object.fromEntries([...NAV.map((n) => [n.name, n.label]), ['more', 'More'], ['habit', 'Habit']])

export function isRoot(name) {
  return ROOTS.has(String(name))
}

// The tab a route belongs to (lit in the tab bar).
export function tabOf(name) {
  const n = String(name || '')
  if (n === 'habit') return 'trackers'
  return ROOTS.has(n) ? n : 'more'
}

// Where Back goes when there is no history to pop (a deep link, a reload): the root of the
// route's own tab.
export function parentOf(name) {
  return tabOf(name)
}

// direction: 'push' | 'pop' | 'none' for the page change in flight. instant: the swipe-back
// gesture already moved the pages, so the router change must not animate again.
export const navState = reactive({ direction: 'none', instant: false, forcePop: false })

let lastPosition = typeof window !== 'undefined' ? window.history.state?.position ?? 0 : 0

// Called from router.afterEach: decides the animation from the history position and the
// kind of route on each side.
export function track(to, from) {
  const position = window.history.state?.position ?? lastPosition + 1
  const back = position < lastPosition
  lastPosition = position
  if (!from.name || to.name === from.name) {
    navState.direction = 'none'
  } else if (navState.forcePop || back) {
    navState.direction = isRoot(from.name) && isRoot(to.name) ? 'none' : 'pop'
  } else if (isRoot(to.name)) {
    navState.direction = 'none' // tab switch, or a link to another tab
  } else {
    navState.direction = 'push'
  }
  navState.forcePop = false
}
