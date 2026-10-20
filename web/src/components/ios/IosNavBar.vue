<script setup>
// The iOS navigation bar. At the top of a page it is see-through and carries no title: the
// page's own large title (its first h1) sits below it. Once that title scrolls under the bar,
// the bar takes the material, a hairline appears and the title shows small and centred.
// Pushed pages get a Back button with the chevron and the previous page's name. Views put
// their own buttons on the right through <Teleport to="#nav-trailing">.
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhCaretLeft } from '@phosphor-icons/vue'
import CaptureBar from '../CaptureBar.vue'
import { LABELS, isRoot, navState, parentOf } from '../../lib/nav'

const route = useRoute()
const router = useRouter()
const bar = ref(null)
const back = ref(null) // { label, history }
const title = ref('')
const condensed = ref(false)
const scrolled = ref(false)
let heading = null

function backTarget() {
  if (isRoot(route.name)) return null
  const path = window.history.state?.back
  if (path) {
    const name = router.resolve(path).name
    if (name && name !== route.name) return { label: LABELS[name] || 'Back', history: true }
  }
  return { label: LABELS[parentOf(route.name)] || 'Back', history: false }
}

function goBack() {
  if (back.value?.history) router.back()
  else {
    navState.forcePop = true
    router.push({ name: parentOf(route.name) })
  }
}

// The page's large title: the first h1 of the page that is arriving, not the one leaving.
function findHeading() {
  heading = document.querySelector('main.page > :not([data-leaving]) h1')
  title.value = heading?.textContent?.trim() || LABELS[route.name] || ''
  update()
}

function update() {
  scrolled.value = window.scrollY > 1
  const barBottom = bar.value?.getBoundingClientRect().bottom ?? 0
  condensed.value = heading?.isConnected ? heading.getBoundingClientRect().bottom <= barBottom + 2 : window.scrollY > 40
}

let observer = null
watch(
  // The name too: on first load the path is already "/" before the route resolves to Today.
  () => [route.fullPath, route.name],
  () => {
    back.value = backTarget()
    // The arriving page renders on the next tick; its title may change after its data loads.
    nextTick(findHeading)
    setTimeout(findHeading, 350)
  },
  { immediate: true },
)
onMounted(() => {
  window.addEventListener('scroll', update, { passive: true })
  // Titles that change after load (a habit's name, Today versus a past day).
  observer = new MutationObserver(() => {
    if (heading?.isConnected) title.value = heading.textContent.trim()
    else findHeading()
  })
  const main = document.querySelector('main.page')
  if (main) observer.observe(main, { childList: true, subtree: true, characterData: true })
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', update)
  observer?.disconnect()
})
</script>

<template>
  <header ref="bar" class="navbar" :class="{ scrolled, condensed }">
    <div class="lead">
      <button v-if="back" type="button" class="back" :aria-label="`Back to ${back.label}`" @click="goBack">
        <PhCaretLeft weight="bold" class="chev" aria-hidden="true" /><span class="truncate">{{ back.label }}</span>
      </button>
    </div>
    <span class="title truncate" aria-hidden="true">{{ title }}</span>
    <div id="nav-trailing" class="trail"></div>
    <CaptureBar icon class="capture" />
  </header>
</template>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: var(--z-bar);
  display: none;
  align-items: center;
  height: calc(44px + env(safe-area-inset-top));
  padding: env(safe-area-inset-top) 4px 0 4px;
  background: transparent;
  transition: background-color 200ms ease, box-shadow 200ms ease;
}
@media (max-width: 1023px) { .navbar { display: flex; } }
.navbar.condensed { background: var(--material); -webkit-backdrop-filter: var(--material-blur); backdrop-filter: var(--material-blur); box-shadow: 0 0.5px 0 var(--bar-line); }
@media (prefers-reduced-transparency: reduce) { .navbar.condensed { background: var(--bg); backdrop-filter: none; -webkit-backdrop-filter: none; } }
.lead { flex: 1; min-width: 0; display: flex; }
.back { display: inline-flex; align-items: center; gap: 2px; max-width: 100%; height: 44px; padding: 0 8px 0 2px; border: 0; background: none; color: var(--brand); font: inherit; font-size: 1.0625rem; }
.back:active { opacity: 0.4; }
.chev { width: 24px; height: 24px; flex: none; }
.title { position: absolute; left: 50%; bottom: 0; transform: translateX(-50%); max-width: 56%; line-height: 44px; font-size: 1.0625rem; font-weight: 600; color: var(--ink); opacity: 0; transition: opacity 180ms ease; pointer-events: none; }
.condensed .title { opacity: 1; }
.trail { display: flex; align-items: center; flex: none; }
.trail :deep(.icon-btn) { width: 44px; height: 44px; }
.trail :deep(.icon-btn svg) { width: 24px; height: 24px; }
.trail :deep(.nav-text) { height: 44px; padding: 0 8px; border: 0; background: none; color: var(--brand); font: inherit; font-size: 1.0625rem; }
.trail :deep(.nav-text:active) { opacity: 0.4; }
.capture { flex: none; }
</style>
