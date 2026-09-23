<script setup>
// Phone navigation: a floating glass pill above the home indicator, icons only. Home, Tasks,
// Tracking and More. One tinted disc sits behind the current icon and slides to the next one on
// a spring. The bar drops out of the way while a text field has focus (the keyboard is up).
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { PhChartLineUp, PhCheckSquare, PhDotsThree, PhHouse } from '@phosphor-icons/vue'

const props = defineProps({ current: { type: String, default: '' }, moreActive: { type: Boolean, default: false } })
const emit = defineEmits(['more'])

const TABS = [
  { name: 'home', label: 'Home', icon: PhHouse },
  { name: 'tasks', label: 'Tasks', icon: PhCheckSquare },
  { name: 'trackers', label: 'Tracking', icon: PhChartLineUp },
]
const MAIN = new Set(TABS.map((t) => t.name))
// Every route that is not on the bar lives under More, so More is lit while you are there.
const moreLit = computed(() => props.moreActive || !MAIN.has(props.current))
const activeIndex = computed(() => (moreLit.value ? TABS.length : TABS.findIndex((t) => t.name === props.current)))

const typing = ref(false)
let settle = null
function isTextField(el) {
  if (!el || el === document.body) return false
  if (el.isContentEditable) return true
  const tag = el.tagName
  if (tag === 'TEXTAREA' || tag === 'SELECT') return true
  return tag === 'INPUT' && !['checkbox', 'radio', 'button', 'submit', 'range', 'color', 'file'].includes(el.type)
}
function onFocusIn(e) {
  clearTimeout(settle)
  if (isTextField(e.target)) typing.value = true
}
function onFocusOut() {
  clearTimeout(settle)
  settle = setTimeout(() => (typing.value = isTextField(document.activeElement)), 80)
}
onMounted(() => {
  document.addEventListener('focusin', onFocusIn)
  document.addEventListener('focusout', onFocusOut)
})
onBeforeUnmount(() => {
  clearTimeout(settle)
  document.removeEventListener('focusin', onFocusIn)
  document.removeEventListener('focusout', onFocusOut)
})
</script>

<template>
  <nav class="tabbar" :class="{ typing }" aria-label="Main">
    <span class="puck" :style="{ transform: `translateX(${activeIndex * 100}%)` }" aria-hidden="true"></span>
    <RouterLink v-for="t in TABS" :key="t.name" :to="{ name: t.name }" class="tab" :class="{ active: !moreLit && current === t.name }" :aria-label="t.label" :title="t.label" :aria-current="current === t.name ? 'page' : undefined">
      <component :is="t.icon" class="glyph" :weight="!moreLit && current === t.name ? 'fill' : 'regular'" aria-hidden="true" />
    </RouterLink>
    <button type="button" class="tab" :class="{ active: moreLit }" aria-label="More" title="More" :aria-expanded="moreActive" @click="emit('more')">
      <PhDotsThree class="glyph" weight="bold" aria-hidden="true" />
    </button>
  </nav>
</template>

<style scoped>
.tabbar {
  position: fixed;
  left: 50%;
  bottom: calc(env(safe-area-inset-bottom) + 14px);
  transform: translate3d(-50%, 0, 0);
  z-index: var(--z-bar);
  display: flex;
  align-items: center;
  padding: 6px;
  border-radius: var(--r-pill);
  /* Glass: the page shows through, blurred and a little brighter; a light rim on top. */
  background: color-mix(in srgb, var(--surface) 62%, transparent);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  backdrop-filter: blur(28px) saturate(180%);
  box-shadow:
    inset 0 0 0 1px var(--material-edge),
    inset 0 1px 0 var(--edge),
    0 2px 6px rgb(14 17 32 / 0.06),
    0 14px 36px -10px rgb(14 17 32 / 0.28);
  transition: transform var(--dur-ui) var(--ease-out), opacity var(--dur-ui) ease;
  -webkit-user-select: none;
  user-select: none;
}
.tabbar.typing { transform: translate3d(-50%, calc(100% + 40px), 0); opacity: 0; pointer-events: none; }
@media (min-width: 1024px) { .tabbar { display: none; } }
@media (prefers-reduced-transparency: reduce) { .tabbar { background: var(--surface); -webkit-backdrop-filter: none; backdrop-filter: none; } }

/* The disc that marks the current tab: one element, translated to the active slot on a spring. */
.puck {
  position: absolute;
  top: 6px;
  left: 6px;
  width: 62px;
  height: 50px;
  border-radius: var(--r-pill);
  background: var(--brand-soft);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.35);
  transition: transform 360ms var(--ease-spring);
  pointer-events: none;
}
.tab {
  position: relative;
  width: 62px;
  height: 50px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: var(--r-pill);
  background: transparent;
  color: var(--ink-2);
  text-decoration: none;
  transition: color var(--dur-hover) ease;
}
.tab:hover { text-decoration: none; }
.tab.active { color: var(--brand); }
.glyph { width: 24px; height: 24px; transition: transform var(--dur-press) var(--ease-out); }
.tab:active .glyph { transform: scale(0.88); }
.tab:focus-visible { outline: 2px solid var(--brand); outline-offset: -2px; }
@media (prefers-reduced-motion: reduce) {
  .puck { transition: none; }
  .tab:active .glyph { transform: none; }
}
</style>
