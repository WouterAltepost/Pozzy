<script setup>
// The iOS tab bar: a translucent material bar across the bottom edge with a hairline on top,
// four tabs with a symbol over a 10pt label. The selected tab is tinted and its symbol filled.
// Tapping the selected tab again pops to its root, or scrolls to the top when already there.
// The bar steps aside while a text field has the keyboard.
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhChartLineUp, PhCheckCircle, PhDotsThreeCircle, PhSquaresFour } from '@phosphor-icons/vue'
import { navState, tabOf } from '../../lib/nav'
import { tick } from '../../lib/haptics'

const props = defineProps({ current: { type: String, default: '' } })
const router = useRouter()

const tabs = [
  { name: 'home', label: 'Today', icon: PhCheckCircle },
  { name: 'trackers', label: 'Habits', icon: PhChartLineUp },
  { name: 'overview', label: 'Overview', icon: PhSquaresFour },
  { name: 'more', label: 'More', icon: PhDotsThreeCircle },
]

function go(tab) {
  const active = tabOf(props.current)
  if (tab.name === active) {
    if (props.current === tab.name) window.scrollTo({ top: 0, behavior: 'smooth' })
    else {
      navState.forcePop = true
      router.push({ name: tab.name })
    }
    return
  }
  tick()
  router.push({ name: tab.name })
}

// Hide while typing: the keyboard covers the bottom edge anyway and the bar would ride on it.
const typing = ref(false)
function onFocus(e) {
  typing.value = e.target.matches?.('input:not([type=checkbox]):not([type=radio]), textarea, select, [contenteditable]') ?? false
}
function onBlur() {
  typing.value = false
}
onMounted(() => {
  document.addEventListener('focusin', onFocus)
  document.addEventListener('focusout', onBlur)
})
onBeforeUnmount(() => {
  document.removeEventListener('focusin', onFocus)
  document.removeEventListener('focusout', onBlur)
})
</script>

<template>
  <nav class="tabbar" :class="{ typing }" aria-label="Tabs">
    <button
      v-for="t in tabs"
      :key="t.name"
      type="button"
      class="tab"
      :class="{ on: tabOf(current) === t.name }"
      :aria-current="tabOf(current) === t.name ? 'page' : undefined"
      @click="go(t)"
    >
      <component :is="t.icon" class="sym" :weight="tabOf(current) === t.name ? 'fill' : 'regular'" aria-hidden="true" />
      <span class="lbl">{{ t.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: var(--z-bar);
  display: none;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  height: var(--tab-h);
  padding-bottom: env(safe-area-inset-bottom);
  background: var(--material);
  -webkit-backdrop-filter: var(--material-blur);
  backdrop-filter: var(--material-blur);
  box-shadow: 0 -0.5px 0 var(--bar-line);
  transition: transform 250ms ease;
}
@media (max-width: 1023px) { .tabbar { display: grid; } }
@media (prefers-reduced-transparency: reduce) { .tabbar { background: var(--surface); backdrop-filter: none; -webkit-backdrop-filter: none; } }
.tabbar.typing { transform: translateY(100%); }
.tab { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; gap: 1px; padding-top: 6px; border: 0; background: none; color: #999; font: inherit; -webkit-tap-highlight-color: transparent; }
:root[data-theme='dark'] .tab { color: #8E8E93; }
.tab.on { color: var(--brand); }
.sym { width: 26px; height: 26px; }
.lbl { font-size: 10px; font-weight: 500; letter-spacing: 0.01em; line-height: 1.2; }
.tab:active .sym { opacity: 0.6; }
</style>
