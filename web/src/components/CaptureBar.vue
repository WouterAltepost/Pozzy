<script setup>
// Top-bar quick input. Submit stores the text immediately; the proposal shows in a
// popover under the field with Confirm / Edit / Discard.
import { ref } from 'vue'
import { PhLightning, PhX } from '@phosphor-icons/vue'
import { useCapturesStore } from '../stores/captures'
import UiButton from './ui/UiButton.vue'

const store = useCapturesStore()
const text = ref('')
const busy = ref(false)
const current = ref(null)
const message = ref('')

function summary(p) {
  if (!p) return ''
  const f = p.fields || {}
  const bits = [p.type, f.title || f.tracker]
  if (f.due_date) bits.push('due ' + f.due_date)
  if (f.start) bits.push(new Date(f.start).toLocaleString('en-GB', { weekday: 'short', hour: '2-digit', minute: '2-digit' }))
  if (f.area) bits.push(f.area)
  if (p.type === 'tracker') bits.push(String(f.value))
  return bits.filter(Boolean).join(', ')
}

async function submit() {
  const t = text.value.trim()
  if (!t || busy.value) return
  busy.value = true
  message.value = ''
  try {
    current.value = await store.submit(t)
    text.value = ''
    if (!current.value.proposal) message.value = 'Saved to the capture inbox.'
  } catch (err) {
    message.value = err.message
  } finally {
    busy.value = false
  }
}

async function confirm() {
  if (!current.value) return
  busy.value = true
  try {
    const out = await store.confirm(current.value.id)
    message.value = `Created ${out.capture.parsed_type}.`
    current.value = null
  } catch (err) {
    message.value = err.message
  } finally {
    busy.value = false
  }
}

async function discard() {
  if (!current.value) return
  try {
    await store.discard(current.value.id)
  } catch (err) {
    message.value = err.message
  }
  current.value = null
}

function dismiss() {
  current.value = null
  message.value = ''
}
</script>

<template>
  <div class="capture-bar">
    <form class="field" @submit.prevent="submit">
      <PhLightning class="bolt" aria-hidden="true" />
      <input v-model="text" type="text" placeholder="Capture anything" aria-label="Capture" :disabled="busy" @keydown.esc="dismiss" />
    </form>
    <Transition name="pop">
      <div v-if="current?.proposal || message" class="panel" role="status">
        <template v-if="current?.proposal">
          <div class="summary">{{ summary(current.proposal) }}</div>
          <div class="actions">
            <UiButton size="sm" variant="primary" :loading="busy" @click="confirm">Confirm</UiButton>
            <RouterLink :to="{ name: 'capture' }" class="link-btn" @click="dismiss">Edit</RouterLink>
            <UiButton size="sm" variant="ghost" :disabled="busy" @click="discard">Discard</UiButton>
          </div>
        </template>
        <div v-else class="summary msg">{{ message }} <button type="button" class="icon-btn" aria-label="Dismiss" @click="dismiss"><PhX /></button></div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.capture-bar { position: relative; width: 100%; max-width: 480px; }
.field { position: relative; display: flex; align-items: center; }
.bolt { position: absolute; left: 12px; width: 15px; height: 15px; color: var(--ink-3); pointer-events: none; }
.capture-bar input { width: 100%; height: 34px; padding-left: 34px; border-radius: var(--r-pill); background: var(--surface-2); border-color: transparent; }
.capture-bar input:hover { border-color: var(--line-2); }
.capture-bar input:focus-visible { background: var(--surface); border-color: var(--line-2); }
.panel { position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: var(--z-sheet); background: var(--surface); color: var(--ink); border: 1px solid var(--line); border-radius: var(--r-lg); padding: var(--sp-3); box-shadow: var(--shadow-2); font-size: var(--fs-md); transform-origin: top center; }
.summary { margin-bottom: var(--sp-2); }
.summary.msg { margin: 0; display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); }
.actions { display: flex; gap: var(--sp-2); align-items: center; }
.pop-enter-active { transition: opacity var(--dur-ui) var(--ease-out), transform var(--dur-ui) var(--ease-out); }
.pop-leave-active { transition: opacity var(--dur-hover) ease, transform var(--dur-hover) ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: scale(0.97); }
@media (prefers-reduced-motion: reduce) { .pop-enter-from, .pop-leave-to { transform: none; } }
</style>
