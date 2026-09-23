<script setup>
// Phone navigation: a dark floating pill above the home indicator. Four destinations plus
// More. Thin icons; the current one is lit.
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
</script>

<template>
  <nav class="tabbar" aria-label="Main">
    <RouterLink v-for="t in TABS" :key="t.name" :to="{ name: t.name }" class="tab" :class="{ active: current === t.name }" :aria-current="current === t.name ? 'page' : undefined">
      <component :is="t.icon" class="glyph" :weight="current === t.name ? 'fill' : 'light'" aria-hidden="true" />
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
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(env(safe-area-inset-bottom) + 12px);
  z-index: var(--z-bar);
  width: min(calc(100% - 32px), 420px);
  height: 62px;
  display: flex;
  align-items: stretch;
  padding: 5px;
  border-radius: var(--r-pill);
  background: var(--chrome);
  box-shadow: var(--shadow-float);
}
.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  min-width: 0;
  border: 0;
  border-radius: var(--r-pill);
  background: transparent;
  color: var(--on-chrome);
  text-decoration: none;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.02em;
  padding: 0;
  transition: color var(--dur-hover) ease, background-color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out);
}
.tab:hover { text-decoration: none; }
.tab:active { transform: scale(0.94); }
.tab.active { color: #fff; background: rgb(255 255 255 / 0.1); box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.08); }
.glyph { width: 22px; height: 22px; }
.label { line-height: 1; }
</style>
