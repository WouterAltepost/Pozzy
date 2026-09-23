<script setup>
// Phone navigation: a floating tab bar on chrome material at the bottom edge (iOS). Four
// destinations plus More, which opens a sheet with the rest. Filled symbols, the selected
// item in the tint, everything else monochrome.
import { PhCalendarBlank, PhCheckSquare, PhDotsThree, PhEnvelopeSimple, PhHouse } from '@phosphor-icons/vue'

defineProps({ current: { type: String, default: '' }, moreActive: { type: Boolean, default: false } })
const emit = defineEmits(['more'])

const TABS = [
  { name: 'home', label: 'Home', icon: PhHouse },
  { name: 'agenda', label: 'Agenda', icon: PhCalendarBlank },
  { name: 'tasks', label: 'Tasks', icon: PhCheckSquare },
  { name: 'mail', label: 'Mail', icon: PhEnvelopeSimple },
]
const MAIN = new Set(TABS.map((t) => t.name))
defineExpose({ MAIN })
</script>

<template>
  <nav class="tabbar" aria-label="Main">
    <RouterLink v-for="t in TABS" :key="t.name" :to="{ name: t.name }" class="tab" :class="{ active: current === t.name }" :aria-current="current === t.name ? 'page' : undefined">
      <component :is="t.icon" class="glyph" :weight="current === t.name ? 'fill' : 'regular'" aria-hidden="true" />
      <span class="label">{{ t.label }}</span>
    </RouterLink>
    <button type="button" class="tab" :class="{ active: moreActive || !MAIN.has(current) }" :aria-expanded="moreActive" @click="emit('more')">
      <PhDotsThree class="glyph" weight="bold" aria-hidden="true" />
      <span class="label">More</span>
    </button>
  </nav>
</template>

<style scoped>
.tabbar {
  position: fixed;
  left: 16px;
  right: 16px;
  bottom: calc(env(safe-area-inset-bottom) + 10px);
  z-index: var(--z-bar);
  height: 60px;
  display: flex;
  align-items: stretch;
  padding: 4px;
  border-radius: var(--r-pill);
  background: var(--material);
  -webkit-backdrop-filter: var(--material-blur);
  backdrop-filter: var(--material-blur);
  box-shadow: var(--shadow-float), inset 0 1px 0 var(--material-edge);
}
@media (prefers-reduced-transparency: reduce) { .tabbar { background: var(--surface); -webkit-backdrop-filter: none; backdrop-filter: none; } }
.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-width: 0;
  border: 0;
  border-radius: var(--r-pill);
  background: transparent;
  color: var(--ink-3);
  text-decoration: none;
  font-size: 10px;
  font-weight: 500;
  padding: 0;
  transition: color var(--dur-hover) ease, background-color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out);
}
.tab:active { transform: scale(0.94); }
.tab.active { color: var(--brand); background: color-mix(in srgb, var(--surface) 70%, transparent); }
.glyph { width: 24px; height: 24px; }
.label { line-height: 1; }
</style>
