<script setup>
// The More tab: a bottom sheet with every destination that is not on the bar as an inset grouped
// list, then Settings, appearance and log out. Rows are 44pt with a tinted symbol and a chevron.
import { PhCaretRight, PhGearSix, PhMoon, PhSignOut, PhSun } from '@phosphor-icons/vue'
import { useTheme } from '../composables/useTheme'
import UiSheet from './ui/UiSheet.vue'

defineProps({ open: { type: Boolean, default: false }, items: { type: Array, default: () => [] }, current: { type: String, default: '' }, email: { type: String, default: '' } })
const emit = defineEmits(['close', 'logout'])
const theme = useTheme()
</script>

<template>
  <UiSheet :open="open" title="More" @close="emit('close')">
    <ul class="group">
      <li v-for="item in items" :key="item.name">
        <RouterLink :to="{ name: item.name }" class="grow" :class="{ active: current === item.name }" :aria-current="current === item.name ? 'page' : undefined" @click="emit('close')">
          <span class="sym"><component :is="item.icon" aria-hidden="true" /></span>
          <span class="lbl">{{ item.label }}</span>
          <PhCaretRight class="chev" weight="bold" aria-hidden="true" />
        </RouterLink>
      </li>
    </ul>
    <ul class="group">
      <li>
        <RouterLink :to="{ name: 'settings' }" class="grow" :class="{ active: current === 'settings' }" @click="emit('close')">
          <span class="sym"><PhGearSix aria-hidden="true" /></span>
          <span class="lbl">Settings</span>
          <PhCaretRight class="chev" weight="bold" aria-hidden="true" />
        </RouterLink>
      </li>
      <li>
        <button type="button" class="grow" role="switch" :aria-checked="theme.isDark.value" @click="theme.toggle()">
          <span class="sym"><PhMoon v-if="theme.isDark.value" aria-hidden="true" /><PhSun v-else aria-hidden="true" /></span>
          <span class="lbl">Dark mode</span>
          <span class="switch" :class="{ on: theme.isDark.value }" aria-hidden="true"><span class="knob"></span></span>
        </button>
      </li>
    </ul>
    <ul class="group">
      <li>
        <button type="button" class="grow" @click="emit('logout')">
          <span class="sym danger"><PhSignOut aria-hidden="true" /></span>
          <span class="lbl danger">Log out</span>
          <span class="muted small truncate email">{{ email }}</span>
        </button>
      </li>
    </ul>
  </UiSheet>
</template>

<style scoped>
.group { background: var(--surface-2); border-radius: var(--r-lg); overflow: hidden; margin-bottom: var(--sp-4); box-shadow: var(--inset); }
.group:last-child { margin-bottom: 0; }
.grow { display: flex; align-items: center; gap: var(--sp-3); width: 100%; min-height: 48px; padding: 0 var(--sp-3) 0 var(--sp-4); border: 0; background: none; color: var(--ink); text-decoration: none; font: inherit; font-size: var(--fs-base); font-weight: 500; text-align: left; }
.grow:hover { text-decoration: none; }
.grow:active { background: var(--surface-3); }
li + li .grow { border-top: 1px solid var(--line); }
.sym { display: inline-flex; width: 30px; height: 30px; align-items: center; justify-content: center; border-radius: 9px; background: var(--surface); color: var(--brand); flex: none; box-shadow: inset 0 1px 0 var(--edge), 0 1px 2px rgb(14 17 32 / 0.06); }
.sym :deep(svg) { width: 17px; height: 17px; }
.sym.danger { color: var(--danger); }
.lbl { flex: 1; min-width: 0; }
.lbl.danger { color: var(--danger); }
.chev { width: 14px; height: 14px; color: var(--ink-4); flex: none; }
.grow.active .lbl { color: var(--brand); }
.email { max-width: 45%; }
/* An iOS-style switch for appearance: a track that fills with the accent, the knob slides. */
.switch { position: relative; width: 44px; height: 26px; border-radius: 13px; background: var(--surface-3); box-shadow: var(--inset); flex: none; transition: background-color var(--dur-ui) ease; }
.switch.on { background: var(--brand); }
.knob { position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgb(14 17 32 / 0.3); transition: transform var(--dur-ui) var(--ease-spring); }
.switch.on .knob { transform: translateX(18px); }
</style>
