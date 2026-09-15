<script setup>
import { ref } from 'vue'
import { PhLightning, PhX } from '@phosphor-icons/vue'
import ProposalEditor from '../components/capture/ProposalEditor.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useReady } from '../composables/useReady'
import UiBadge from '../components/ui/UiBadge.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import { formatDateTime } from '../lib/dates'
import { useCapturesStore } from '../stores/captures'

const store = useCapturesStore()
const text = ref('')
const busy = ref(false)
const error = ref('')
const showHandled = ref(false)
const lastCreated = ref(null)

const ready = useReady(() => store.load())

async function run(fn) {
  error.value = ''
  busy.value = true
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

function submit() {
  const t = text.value.trim()
  if (!t) return
  run(async () => {
    await store.submit(t)
    text.value = ''
  })
}

function confirm(capture, body) {
  run(async () => {
    const out = await store.confirm(capture.id, body)
    lastCreated.value = { type: out.capture.parsed_type, title: out.created.title || out.created.tracker || '', ref: out.capture.result_ref }
  })
}

function resultLink(ref) {
  if (!ref) return null
  const [kind, id] = ref.split(':')
  if (kind === 'task') return { name: 'tasks', query: { task: id } }
  if (kind === 'goal') return { name: 'goals' }
  if (kind === 'note') return { name: 'notes' }
  if (kind === 'tracker_entry') return { name: 'trackers' }
  return null
}
</script>

<template>
  <div class="capture">
    <PageHeader title="Capture" />
    <form class="card entry" @submit.prevent="submit">
      <textarea v-model="text" rows="2" placeholder="Anything: 'call dentist tomorrow', 'note: ...', 'goal: run 3x next week', 'weight 82.4', 'event: standup tue 09:00'" aria-label="Capture text" @keydown.enter.exact.prevent="submit"></textarea>
      <div class="entry-row">
        <UiButton type="submit" variant="primary" :loading="busy" :disabled="!text.trim()">Capture</UiButton>
        <span class="muted small">Stored first, then Claude (or the rule parser) proposes what it is. Nothing is created until you confirm.</span>
      </div>
    </form>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading inbox">
    <p v-if="lastCreated" class="ok small created">
      Created {{ lastCreated.type }} "{{ lastCreated.title }}".
      <RouterLink v-if="resultLink(lastCreated.ref)" :to="resultLink(lastCreated.ref)">Open</RouterLink>
    </p>

    <div class="section-head"><h2>Inbox</h2><span class="muted small num">{{ store.open.length }}</span></div>
    <div v-if="!store.open.length" class="card">
      <UiEmpty compact title="Nothing waiting" hint="Captured items appear here until you confirm or discard them.">
        <template #icon><PhLightning /></template>
      </UiEmpty>
    </div>
    <section v-for="c in store.open" :key="c.id" class="card item">
      <div class="raw">
        <span class="raw-text">{{ c.raw_text }}</span>
        <span class="muted xs num">{{ formatDateTime(c.created_at) }}</span>
      </div>
      <ProposalEditor v-if="c.proposal" :proposal="c.proposal" @confirm="(body) => confirm(c, body)" @discard="run(() => store.discard(c.id))" />
      <div v-else class="row">
        <UiButton variant="primary" :loading="busy" @click="run(() => store.process(c.id))">Propose</UiButton>
        <UiButton variant="danger" @click="run(() => store.discard(c.id))">Discard</UiButton>
      </div>
    </section>

    <div class="section-head">
      <h2>Handled</h2>
      <span class="muted small num">{{ store.handled.length }}</span>
      <button type="button" class="link-btn" @click="showHandled = !showHandled">{{ showHandled ? 'Hide' : 'Show' }}</button>
    </div>
    <div v-if="showHandled" class="card">
      <ul class="handled">
        <li v-for="c in store.handled" :key="c.id" class="list-row">
          <UiBadge :tone="c.status === 'processed' ? 'ok' : 'neutral'">{{ c.status }}</UiBadge>
          <span class="txt truncate">{{ c.raw_text }}</span>
          <RouterLink v-if="c.status === 'processed' && resultLink(c.result_ref)" :to="resultLink(c.result_ref)" class="small">{{ c.parsed_type }}</RouterLink>
          <span class="muted xs num">{{ formatDateTime(c.processed_at || c.updated_at) }}</span>
          <button type="button" class="icon-btn" aria-label="Remove" @click="run(() => store.remove(c.id))"><PhX /></button>
        </li>
        <li v-if="!store.handled.length" class="muted small">Nothing handled yet.</li>
      </ul>
    </div>
    </UiLoadGate>
  </div>
</template>

<style scoped>
.capture { max-width: 820px; }
.entry { display: flex; flex-direction: column; gap: var(--sp-3); }
.entry textarea { width: 100%; }
.entry-row { display: flex; flex-wrap: wrap; gap: var(--sp-3); align-items: center; }
.created { margin: calc(var(--sp-2) * -1) 0 var(--sp-3); }
.section-head { display: flex; align-items: baseline; gap: var(--sp-2); margin: var(--sp-5) 0 var(--sp-3); }
.section-head h2 { font-size: var(--fs-lg); }
.item { display: flex; flex-direction: column; gap: var(--sp-3); }
.raw { display: flex; justify-content: space-between; gap: var(--sp-3); align-items: baseline; }
.raw-text { font-weight: 500; }
.row { display: flex; gap: var(--sp-2); }
.txt { flex: 1; min-width: 0; }
</style>
