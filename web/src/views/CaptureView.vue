<script setup>
import { onMounted, ref } from 'vue'
import ProposalEditor from '../components/capture/ProposalEditor.vue'
import { formatDateTime } from '../lib/dates'
import { useCapturesStore } from '../stores/captures'

const store = useCapturesStore()
const text = ref('')
const busy = ref(false)
const error = ref('')
const showHandled = ref(false)
const lastCreated = ref(null)

onMounted(() => store.load())

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
    <h1>Capture</h1>
    <form class="card entry" @submit.prevent="submit">
      <textarea v-model="text" rows="2" placeholder="Anything: 'call dentist tomorrow', 'note: ...', 'goal: run 3x next week', 'weight 82.4', 'event: standup tue 09:00'" @keydown.enter.exact.prevent="submit"></textarea>
      <div class="row">
        <button type="submit" :disabled="busy || !text.trim()">{{ busy ? 'Working' : 'Capture' }}</button>
        <span class="muted small">Stored first, then Claude (or the rule parser) proposes what it is. Nothing is created until you confirm.</span>
      </div>
    </form>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <p v-if="lastCreated" class="ok small">
      Created {{ lastCreated.type }} "{{ lastCreated.title }}".
      <RouterLink v-if="resultLink(lastCreated.ref)" :to="resultLink(lastCreated.ref)">Open</RouterLink>
    </p>

    <h2>Inbox <span class="muted small">{{ store.open.length }}</span></h2>
    <p v-if="!store.open.length" class="muted">Nothing waiting.</p>
    <section v-for="c in store.open" :key="c.id" class="card item">
      <div class="raw">
        <span>{{ c.raw_text }}</span>
        <span class="muted small">{{ formatDateTime(c.created_at) }}</span>
      </div>
      <ProposalEditor v-if="c.proposal" :proposal="c.proposal" @confirm="(body) => confirm(c, body)" @discard="run(() => store.discard(c.id))" />
      <div v-else class="row">
        <button type="button" :disabled="busy" @click="run(() => store.process(c.id))">Propose</button>
        <button type="button" class="danger" @click="run(() => store.discard(c.id))">Discard</button>
      </div>
    </section>

    <h2 class="toggle" @click="showHandled = !showHandled">Handled <span class="muted small">{{ store.handled.length }} {{ showHandled ? '(hide)' : '(show)' }}</span></h2>
    <ul v-if="showHandled" class="handled">
      <li v-for="c in store.handled" :key="c.id">
        <span :class="['badge', c.status]">{{ c.status }}</span>
        <span class="txt">{{ c.raw_text }}</span>
        <RouterLink v-if="c.status === 'processed' && resultLink(c.result_ref)" :to="resultLink(c.result_ref)" class="small">{{ c.parsed_type }}</RouterLink>
        <span class="muted small">{{ formatDateTime(c.processed_at || c.updated_at) }}</span>
        <button type="button" class="tiny" @click="run(() => store.remove(c.id))">x</button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; margin: 0 0 0.75rem; }
h2 { font-size: 1rem; margin: 1rem 0 0.5rem; }
h2.toggle { cursor: pointer; }
.entry { display: flex; flex-direction: column; gap: 0.5rem; }
.entry textarea { font: inherit; width: 100%; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; }
.row { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.small { font-size: 0.8rem; }
.item { display: flex; flex-direction: column; gap: 0.6rem; }
.raw { display: flex; justify-content: space-between; gap: 0.5rem; font-weight: 600; font-size: 0.95rem; }
.handled { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.25rem; }
.handled li { display: flex; align-items: center; gap: 0.5rem; font-size: 0.88rem; }
.handled .txt { flex: 1; }
.badge { font-size: 0.7rem; padding: 0 0.35rem; border-radius: 3px; background: #f3f4f6; }
.badge.processed { background: #d1fae5; }
.badge.discarded { background: #fee2e2; }
.tiny { padding: 0 0.4rem; font-size: 0.75rem; }
.danger { color: #b91c1c; }
</style>
