<script setup>
import { computed, ref } from 'vue'
import { PhCaretRight, PhCheck, PhLightning, PhMagicWand, PhNotePencil, PhTrash, PhX } from '@phosphor-icons/vue'
import ProposalEditor from '../components/capture/ProposalEditor.vue'
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import SwipeRow from '../components/ios/SwipeRow.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import UiModal from '../components/ui/UiModal.vue'
import { useReady } from '../composables/useReady'
import { useContextMenu } from '../composables/useContextMenu'
import { useLongPress } from '../composables/useLongPress'
import { useMediaQuery } from '../composables/useMediaQuery'
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
// Below 1024px this is the iOS app: the inbox is a list with swipe actions and each capture
// opens in a sheet with its proposal as a form.
const phone = useMediaQuery('(max-width: 1023px)')
const menu = useContextMenu()
const openId = ref(null)
const opened = computed(() => store.open.find((c) => c.id === openId.value) || null)

const ready = useReady(() => store.load())

const busyId = ref(null) // the capture whose Propose or Confirm is in flight
async function run(fn, id = null) {
  error.value = ''
  busy.value = true
  busyId.value = id
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
    busyId.value = null
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
    if (openId.value === capture.id) openId.value = null
  }, capture.id)
}

function discard(capture) {
  run(async () => {
    await store.discard(capture.id)
    if (openId.value === capture.id) openId.value = null
  }, capture.id)
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

// One line under the raw text: what the proposal would create.
function proposalLine(c) {
  const p = c.proposal
  if (!p) return 'Not proposed yet'
  const f = p.fields || {}
  const name = f.title || f.tracker || ''
  const kind = p.type ? p.type[0].toUpperCase() + p.type.slice(1) : 'Item'
  return name ? `${kind}: ${name}` : kind
}

// Swipe right confirms the proposal as it stands (or asks for one), swipe left discards.
function leadingFor(c) {
  if (c.proposal) return [{ label: 'Confirm', icon: PhCheck, color: 'var(--ok)', action: () => confirm(c, {}) }]
  return [{ label: 'Propose', icon: PhMagicWand, color: 'var(--brand)', action: () => run(() => store.process(c.id), c.id) }]
}
const trailingFor = (c) => [{ label: 'Discard', icon: PhX, color: 'var(--danger)', action: () => discard(c) }]
const handledTrailing = (c) => [{ label: 'Delete', icon: PhTrash, color: 'var(--danger)', action: () => run(() => store.remove(c.id)) }]

const press = useLongPress((c, evt) => {
  menu.open(press.target() || evt?.currentTarget, [
    c.proposal ? { label: 'Confirm', icon: PhCheck, action: () => confirm(c, {}) } : { label: 'Propose', icon: PhMagicWand, action: () => run(() => store.process(c.id), c.id) },
    { label: 'Review', icon: PhNotePencil, action: () => (openId.value = c.id) },
    { label: 'Discard', icon: PhX, danger: true, action: () => discard(c) },
  ])
})
function openRow(c) {
  if (press.consumed()) return
  openId.value = c.id
}
</script>

<template>
  <component :is="phone ? PullToRefresh : 'div'" :action="phone ? () => store.load() : undefined">
  <div class="capture">
    <PageHeader title="Capture" />
    <form class="card entry" @submit.prevent="submit">
      <textarea v-model="text" :rows="phone ? 3 : 2" placeholder="Anything: 'call dentist tomorrow', 'note: ...', 'goal: run 3x next week', 'weight 82.4', 'event: standup tue 09:00'" aria-label="Capture text" @keydown.enter.exact.prevent="submit"></textarea>
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
    <template v-if="phone">
      <ul v-if="store.open.length" class="plate">
        <li v-for="c in store.open" :key="c.id" class="pli">
          <SwipeRow :leading="leadingFor(c)" :trailing="trailingFor(c)">
            <button type="button" class="crow pressable" :class="{ working: busyId === c.id }" v-bind="press.handlers(c)" @click="openRow(c)">
              <span class="cbody">
                <span class="craw">{{ c.raw_text }}</span>
                <span class="cmeta"><span class="cprop truncate" :class="{ none: !c.proposal }">{{ proposalLine(c) }}</span><span class="num">{{ formatDateTime(c.created_at) }}</span></span>
              </span>
              <PhCaretRight class="chev" weight="bold" aria-hidden="true" />
            </button>
          </SwipeRow>
        </li>
      </ul>
      <p v-if="store.open.length" class="pfoot">Swipe right to confirm, left to discard. Tap to review.</p>
    </template>
    <template v-else>
    <section v-for="c in store.open" :key="c.id" class="card item">
      <div class="raw">
        <span class="raw-text">{{ c.raw_text }}</span>
        <span class="muted xs num">{{ formatDateTime(c.created_at) }}</span>
      </div>
      <ProposalEditor v-if="c.proposal" :proposal="c.proposal" :busy="busyId === c.id" @confirm="(body) => confirm(c, body)" @discard="run(() => store.discard(c.id), c.id)" />
      <div v-else class="row">
        <UiButton variant="primary" :loading="busyId === c.id" :disabled="busy" @click="run(() => store.process(c.id), c.id)">Propose</UiButton>
        <UiButton variant="danger" :disabled="busy" @click="run(() => store.discard(c.id), c.id)">Discard</UiButton>
      </div>
    </section>
    </template>

    <div class="section-head">
      <h2>Handled</h2>
      <span class="muted small num">{{ store.handled.length }}</span>
      <button type="button" class="link-btn" @click="showHandled = !showHandled">{{ showHandled ? 'Hide' : 'Show' }}</button>
    </div>
    <div v-if="showHandled" class="card handled-card">
      <ul class="handled">
        <template v-if="phone">
          <li v-for="c in store.handled" :key="c.id" class="pli">
            <SwipeRow :trailing="handledTrailing(c)">
              <div class="hrow">
                <span class="cbody">
                  <span class="craw truncate">{{ c.raw_text }}</span>
                  <span class="cmeta">
                    <RouterLink v-if="c.status === 'processed' && resultLink(c.result_ref)" :to="resultLink(c.result_ref)" class="hlink">{{ c.parsed_type }}</RouterLink>
                    <span v-else>{{ c.status }}</span>
                    <span class="num">{{ formatDateTime(c.processed_at || c.updated_at) }}</span>
                  </span>
                </span>
                <button type="button" class="icon-btn rm" aria-label="Remove" @click="run(() => store.remove(c.id))"><PhX /></button>
              </div>
            </SwipeRow>
          </li>
        </template>
        <template v-else>
        <li v-for="c in store.handled" :key="c.id" class="list-row">
          <UiBadge :tone="c.status === 'processed' ? 'ok' : 'neutral'">{{ c.status }}</UiBadge>
          <span class="txt truncate">{{ c.raw_text }}</span>
          <RouterLink v-if="c.status === 'processed' && resultLink(c.result_ref)" :to="resultLink(c.result_ref)" class="small">{{ c.parsed_type }}</RouterLink>
          <span class="muted xs num">{{ formatDateTime(c.processed_at || c.updated_at) }}</span>
          <button type="button" class="icon-btn" aria-label="Remove" @click="run(() => store.remove(c.id))"><PhX /></button>
        </li>
        </template>
        <li v-if="!store.handled.length" class="muted small">Nothing handled yet.</li>
      </ul>
    </div>
    </UiLoadGate>

    <UiModal v-if="phone" :open="Boolean(opened)" title="Capture" size="md" @close="openId = null">
      <template v-if="opened">
        <blockquote class="squote">{{ opened.raw_text }}<span class="num">{{ formatDateTime(opened.created_at) }}</span></blockquote>
        <ProposalEditor v-if="opened.proposal" ios :proposal="opened.proposal" :busy="busyId === opened.id" @confirm="(body) => confirm(opened, body)" @discard="discard(opened)" />
        <div v-else class="snone">
          <p>No proposal yet. Ask for one, or discard the capture.</p>
          <UiButton variant="primary" block :loading="busyId === opened.id" :disabled="busy" @click="run(() => store.process(opened.id), opened.id)">Propose</UiButton>
          <button type="button" class="sdiscard" :disabled="busy" @click="discard(opened)">Discard</button>
        </div>
      </template>
    </UiModal>
  </div>
  </component>
</template>

<style scoped>
.capture { max-width: 820px; }
@media (max-width: 699px) { .entry textarea { font-size: var(--fs-base); } .entry-row .small { flex-basis: 100%; } }
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

/* iOS: the entry is a plate with a bare text view, the inbox an inset grouped list with
   footnote section headers. */
@media (max-width: 1023px) {
  .entry { gap: var(--sp-2); padding: 4px 16px 12px; }
  .entry textarea { padding: 10px 0; border: 0; background: transparent; box-shadow: none; resize: none; line-height: 1.4; }
  .entry textarea:focus-visible { box-shadow: none; }
  .entry-row { flex-direction: row-reverse; justify-content: space-between; align-items: flex-end; gap: var(--sp-3); }
  .entry-row .small { flex: 1; flex-basis: auto; font-size: var(--fs-xs); line-height: 1.35; }
  .entry-row :deep(.btn) { flex: none; }
  .section-head { margin: var(--sp-6) 16px 6px; }
  .section-head h2 { font-size: var(--fs-sm); font-weight: 400; text-transform: uppercase; color: var(--ink-3); }
  .section-head .link-btn { margin-left: auto; font-size: var(--fs-sm); }
  .created { margin: 0 4px var(--sp-2); }
  .plate, .handled-card { margin: 0; padding: 0; background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .pli { position: relative; }
  .pli + .pli::before { content: ''; position: absolute; z-index: 2; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line); pointer-events: none; }
  .crow, .hrow { display: flex; align-items: center; gap: var(--sp-3); width: 100%; min-height: 44px; padding: 10px 16px; border: 0; border-radius: 0; background: none; box-shadow: none; color: var(--ink); font: inherit; text-align: left; }
  .crow.working { opacity: 0.5; }
  .cbody { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
  .craw { font-size: 1.0625rem; line-height: 1.3; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; }
  .hrow .craw { display: block; }
  .cmeta { display: flex; align-items: baseline; gap: var(--sp-2); font-size: var(--fs-md); color: var(--ink-3); }
  .cprop { flex: 1; min-width: 0; color: var(--ink-2); }
  .cprop.none { color: var(--ink-3); font-style: italic; }
  .cmeta .num { flex: none; margin-left: auto; font-size: var(--fs-sm); }
  .hlink { text-transform: capitalize; }
  .chev { flex: none; width: 13px; height: 13px; color: var(--ink-4); }
  .pfoot { margin: 6px 16px 0; font-size: var(--fs-sm); color: var(--ink-3); }
  .handled > li.muted { padding: 12px 16px; }
  .rm { display: none; }
  .squote { display: flex; flex-direction: column; gap: 4px; margin: 0 0 var(--sp-4); padding: 10px 12px; border-radius: var(--r-md); background: var(--surface-2); font-size: 1.0625rem; line-height: 1.35; }
  .squote .num { font-size: var(--fs-sm); color: var(--ink-3); }
  .snone { display: flex; flex-direction: column; gap: var(--sp-3); }
  .snone p { font-size: var(--fs-md); color: var(--ink-3); }
  .sdiscard { height: 44px; border: 0; background: none; box-shadow: none; color: var(--danger); font: inherit; font-size: 1.0625rem; }
}
@media (max-width: 1023px) and (hover: hover) and (pointer: fine) { .rm { display: inline-flex; } }
</style>
