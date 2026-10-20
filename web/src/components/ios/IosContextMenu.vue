<script setup>
// The iOS context menu: the page blurs and dims, the pressed element is lifted out of it with a
// shadow, and a menu of actions opens below it (above when there is no room). Rows are 44pt
// with the label on the left and the symbol on the right; destructive rows are red.
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { contextMenuState as state } from '../../composables/useContextMenu'

const lifted = ref(null)
const MENU_W = 250

const place = computed(() => {
  const r = state.rect
  if (!r) return {}
  const vw = window.innerWidth
  const vh = window.innerHeight
  const rows = state.items.length * 44 + (state.title ? 36 : 0)
  const below = r.bottom + 8 + rows < vh - 24
  const left = r.left + MENU_W > vw - 12 ? Math.max(12, r.right - MENU_W) : Math.max(12, r.left)
  // When neither side has room, the lifted element slides up so the menu fits under it.
  const shift = !below && r.top - 8 - rows < 24 ? Math.min(0, vh - 24 - rows - 8 - r.bottom) : 0
  return {
    menu: below || shift ? { top: `${r.bottom + 8 + shift}px`, left: `${left}px`, transformOrigin: 'top left' } : { bottom: `${vh - r.top + 8}px`, left: `${left}px`, transformOrigin: 'bottom left' },
    lift: { top: `${r.top + shift}px`, left: `${r.left}px`, width: `${r.width}px`, height: `${r.height}px` },
  }
})

watch(
  () => state.open,
  async (on) => {
    if (!on) return
    await nextTick()
    if (!lifted.value || !state.anchor) return
    lifted.value.replaceChildren(state.anchor.cloneNode(true))
  },
)

function choose(item) {
  state.open = false
  setTimeout(() => item.action?.(), 120)
}
function onKey(e) {
  if (e.key === 'Escape') state.open = false
}
watch(() => state.open, (on) => (on ? document.addEventListener('keydown', onKey) : document.removeEventListener('keydown', onKey)))
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <Transition name="cm">
      <div v-if="state.open" class="cm-root" role="menu" :aria-label="state.title || 'Actions'" @contextmenu.prevent>
        <div class="cm-scrim" @click="state.open = false"></div>
        <div ref="lifted" class="cm-lift" :style="place.lift" aria-hidden="true"></div>
        <div class="cm-menu" :style="place.menu">
          <div v-if="state.title" class="cm-title">{{ state.title }}</div>
          <button v-for="(item, i) in state.items" :key="i" type="button" role="menuitem" class="cm-item" :class="{ danger: item.danger }" @click="choose(item)">
            <span class="cm-label">{{ item.label }}</span>
            <component :is="item.icon" v-if="item.icon" class="cm-icon" weight="regular" aria-hidden="true" />
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.cm-root { position: fixed; inset: 0; z-index: calc(var(--z-sheet) + 1); }
.cm-scrim { position: absolute; inset: 0; background: rgb(0 0 0 / 0.18); -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px); }
.cm-lift { position: fixed; overflow: hidden; border-radius: 12px; background: var(--surface); box-shadow: 0 10px 40px rgb(0 0 0 / 0.22); pointer-events: none; transform: scale(1.03); }
.cm-lift > :deep(*) { margin: 0 !important; padding-left: 12px; padding-right: 12px; border: 0 !important; }
.cm-menu { position: fixed; width: 250px; border-radius: 13px; overflow: hidden; background: var(--material); -webkit-backdrop-filter: blur(30px) saturate(180%); backdrop-filter: blur(30px) saturate(180%); box-shadow: 0 10px 40px rgb(0 0 0 / 0.2); }
.cm-title { padding: 10px 16px; font-size: 0.8125rem; color: var(--ink-3); border-bottom: 0.5px solid var(--line-2); }
.cm-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; width: 100%; height: 44px; padding: 0 16px; border: 0; background: transparent; color: var(--ink); font: inherit; font-size: 1.0625rem; text-align: left; }
.cm-item + .cm-item { border-top: 0.5px solid var(--line-2); }
.cm-item:active { background: var(--surface-3); }
.cm-item.danger { color: var(--danger); }
.cm-icon { width: 20px; height: 20px; flex: none; }
.cm-enter-active { transition: opacity 220ms ease; }
.cm-enter-active .cm-menu { transition: transform 380ms cubic-bezier(0.2, 1.3, 0.4, 1), opacity 200ms ease; }
.cm-enter-active .cm-lift { transition: transform 380ms cubic-bezier(0.2, 1.3, 0.4, 1); }
.cm-leave-active { transition: opacity 180ms ease; }
.cm-enter-from, .cm-leave-to { opacity: 0; }
.cm-enter-from .cm-menu { transform: scale(0.6); opacity: 0; }
.cm-enter-from .cm-lift { transform: scale(1); }
@media (prefers-reduced-motion: reduce) { .cm-enter-from .cm-menu { transform: none; } }
</style>
