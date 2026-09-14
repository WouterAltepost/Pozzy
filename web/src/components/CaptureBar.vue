<script setup>
// Top-bar quick input. Stream E mounts this in App.vue inside the authenticated part of the header.
// Submit stores the text immediately; the proposal shows in a small panel with Confirm / Edit / Discard.
import { ref } from 'vue'
import { useCapturesStore } from '../stores/captures'

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
  return bits.filter(Boolean).join(' · ')
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
    <form @submit.prevent="submit">
      <input v-model="text" type="text" placeholder="Capture..." :disabled="busy" @keydown.esc="dismiss" />
    </form>
    <div v-if="current?.proposal || message" class="panel">
      <template v-if="current?.proposal">
        <div class="summary">{{ summary(current.proposal) }}</div>
        <div class="actions">
          <button type="button" :disabled="busy" @click="confirm">Confirm</button>
          <RouterLink :to="{ name: 'capture' }" class="link" @click="dismiss">Edit</RouterLink>
          <button type="button" :disabled="busy" @click="discard">Discard</button>
        </div>
      </template>
      <div v-else class="summary">{{ message }} <button type="button" class="x" @click="dismiss">x</button></div>
    </div>
  </div>
</template>

<style scoped>
.capture-bar { position: relative; flex: 1; max-width: 420px; margin: 0 1rem; }
.capture-bar input { width: 100%; font: inherit; font-size: 0.9rem; padding: 0.3rem 0.5rem; border: 1px solid #4b5563; border-radius: 4px; background: #1f2937; color: #f9fafb; }
.capture-bar input::placeholder { color: #9ca3af; }
.panel { position: absolute; top: 110%; left: 0; right: 0; z-index: 20; background: #fff; color: #1f2937; border: 1px solid #e5e7eb; border-radius: 6px; padding: 0.6rem 0.75rem; box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12); font-size: 0.88rem; }
.summary { margin-bottom: 0.4rem; }
.actions { display: flex; gap: 0.5rem; align-items: center; }
.actions button { padding: 0.25rem 0.6rem; font-size: 0.85rem; }
.link { font-size: 0.85rem; }
.x { padding: 0 0.35rem; font-size: 0.75rem; margin-left: 0.5rem; }
</style>
