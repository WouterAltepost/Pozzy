<script setup>
// The More tab: a sheet with the remaining destinations as an inset grouped list, then
// appearance and sign out. Rows are 44 pt with a tinted symbol and a trailing chevron.
import { PhCaretRight, PhMoon, PhSignOut, PhSun } from '@phosphor-icons/vue'
import { useTheme } from '../composables/useTheme'
import UiModal from './ui/UiModal.vue'

defineProps({ open: { type: Boolean, default: false }, items: { type: Array, default: () => [] }, current: { type: String, default: '' }, email: { type: String, default: '' } })
const emit = defineEmits(['close', 'logout'])
const theme = useTheme()
</script>

<template>
  <UiModal :open="open" title="More" size="sm" @close="emit('close')">
    <ul class="group">
      <li v-for="item in items" :key="item.name">
        <RouterLink :to="{ name: item.name }" class="grow" :class="{ active: current === item.name }" @click="emit('close')">
          <span class="sym"><component :is="item.icon" aria-hidden="true" /></span>
          <span class="lbl">{{ item.label }}</span>
          <PhCaretRight class="chev" weight="bold" aria-hidden="true" />
        </RouterLink>
      </li>
    </ul>
    <ul class="group">
      <li>
        <button type="button" class="grow" @click="theme.toggle()">
          <span class="sym"><PhSun v-if="theme.isDark.value" aria-hidden="true" /><PhMoon v-else aria-hidden="true" /></span>
          <span class="lbl">{{ theme.isDark.value ? 'Light appearance' : 'Dark appearance' }}</span>
        </button>
      </li>
      <li>
        <button type="button" class="grow" @click="emit('logout')">
          <span class="sym danger"><PhSignOut aria-hidden="true" /></span>
          <span class="lbl danger">Sign out</span>
          <span class="muted small truncate">{{ email }}</span>
        </button>
      </li>
    </ul>
  </UiModal>
</template>

<style scoped>
.group { background: var(--surface-2); border-radius: var(--r-md); overflow: hidden; margin-bottom: var(--sp-4); }
.group:last-child { margin-bottom: 0; }
.grow { display: flex; align-items: center; gap: var(--sp-3); width: 100%; min-height: 44px; padding: 0 var(--sp-3) 0 var(--sp-4); border: 0; background: none; color: var(--ink); text-decoration: none; font: inherit; font-size: var(--fs-base); text-align: left; }
.grow:active { background: var(--surface-3); }
li + li .grow { border-top: 0.5px solid var(--line); }
.sym { display: inline-flex; width: 28px; height: 28px; align-items: center; justify-content: center; border-radius: 7px; background: var(--brand); color: #fff; flex: none; }
.sym :deep(svg) { width: 17px; height: 17px; }
.sym.danger { background: var(--danger); }
.lbl { flex: 1; min-width: 0; }
.lbl.danger { color: var(--danger); }
.chev { width: 14px; height: 14px; color: var(--ink-4); flex: none; }
.grow.active .lbl { color: var(--brand); }
</style>
