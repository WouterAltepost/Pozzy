<script setup>
// Capture lives behind one button in the top bar (or Cmd/Ctrl plus K). The dialog holds the
// whole flow: write, Pozzy proposes what it is, adjust, confirm. Nothing is created until
// Confirm. Stored first, so the text is safe even if the proposal fails.
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { PhLightning } from '@phosphor-icons/vue'
import { useCapturesStore } from '../stores/captures'
import { useToast } from '../composables/useToast'
import ProposalEditor from './capture/ProposalEditor.vue'
import UiButton from './ui/UiButton.vue'
import UiModal from './ui/UiModal.vue'

const store = useCapturesStore()
const toast = useToast()
const open = ref(false)
const text = ref('')
const busy = ref(false)
const current = ref(null)
const message = ref('')
const modKey = /Mac|iPhone|iPad/.test(navigator.platform) ? '\u2318' : 'Ctrl'

function show() {
  open.value = true
  current.value = null
  message.value = ''
}
function close() {
  open.value = false
}

async function submit() {
  const t = text.value.trim()
  if (!t || busy.value) return
  busy.value = true
  message.value = ''
  try {
    current.value = await store.submit(t)
    text.value = ''
    if (!current.value.proposal) message.value = 'Saved to the capture inbox. AI is off or did not answer, so decide there what it is.'
  } catch (err) {
    message.value = err.message
  } finally {
    busy.value = false
  }
}

async function confirm(body) {
  if (!current.value) return
  busy.value = true
  try {
    const out = await store.confirm(current.value.id, body)
    toast.success(`Created ${out.capture.parsed_type}: ${out.created.title || out.created.tracker || ''}`.trim())
    current.value = null
    close()
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

function onKey(e) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    open.value ? close() : show()
  }
}
onMounted(() => document.addEventListener('keydown', onKey))
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="capture-bar">
    <button type="button" class="capture-btn" title="Capture anything (Cmd or Ctrl plus K)" @click="show">
      <PhLightning class="bolt" weight="fill" aria-hidden="true" />
      <span class="label">Capture</span>
      <span class="label-long">Capture anything</span>
      <kbd class="kbd" aria-hidden="true">{{ modKey }} K</kbd>
    </button>

    <UiModal :open="open" title="Capture" size="md" @close="close">
      <form v-if="!current?.proposal" class="entry" @submit.prevent="submit">
        <textarea v-model="text" rows="3" placeholder="Anything: 'call dentist tomorrow', 'note: ...', 'goal: run 3x next week', 'weight 82.4', 'event: standup tue 09:00'" aria-label="Capture text" :disabled="busy" @keydown.enter.exact.prevent="submit"></textarea>
        <div class="entry-row">
          <UiButton type="submit" variant="primary" :loading="busy" :disabled="!text.trim()">Capture</UiButton>
          <span class="muted small">Stored first, then Pozzy proposes what it is. Nothing is created until you confirm.</span>
        </div>
      </form>
      <div v-else class="proposal">
        <p class="raw">"{{ current.raw_text }}"</p>
        <ProposalEditor :proposal="current.proposal" @confirm="confirm" @discard="discard" />
      </div>
      <p v-if="message" class="msg small" role="status">
        {{ message }} <RouterLink :to="{ name: 'capture' }" @click="close">Open inbox</RouterLink>
      </p>
    </UiModal>
  </div>
</template>

<style scoped>
.capture-bar { display: flex; justify-content: center; }
.capture-btn {
  display: inline-flex; align-items: center; gap: 8px;
  height: 34px; padding: 0 12px 0 12px;
  border: 1px solid transparent; border-radius: var(--r-pill);
  background: var(--surface-2); color: var(--ink-2); font: inherit; font-size: var(--fs-md); font-weight: 500;
  cursor: pointer;
  transition: background-color var(--dur-hover) ease, border-color var(--dur-hover) ease, color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out);
}
.capture-btn:active { transform: scale(0.97); }
@media (hover: hover) and (pointer: fine) { .capture-btn:hover { border-color: var(--line-2); color: var(--ink); } }
.bolt { width: 15px; height: 15px; color: var(--brand); }
.kbd { font: inherit; font-size: var(--fs-xs); color: var(--ink-3); border: 1px solid var(--line-2); border-radius: 4px; padding: 0 5px; line-height: 16px; }
.label-long { display: none; }
@media (max-width: 720px) {
  .capture-bar { width: 100%; max-width: none; }
  .label, .kbd { display: none; }
  .label-long { display: inline; color: var(--ink-3); font-weight: 400; }
  .capture-btn { width: 100%; justify-content: flex-start; padding-left: 12px; }
}
.entry { display: flex; flex-direction: column; gap: var(--sp-3); }
.entry textarea { width: 100%; font-size: var(--fs-base); }
.entry-row { display: flex; flex-wrap: wrap; gap: var(--sp-3); align-items: center; }
.raw { font-weight: 500; margin-bottom: var(--sp-3); color: var(--ink-2); }
.msg { margin-top: var(--sp-3); color: var(--ink-2); }
</style>
