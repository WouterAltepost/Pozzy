<script setup>
// The briefing plus a reply box. Wouter writes a note, Claude rewrites the briefing and proposes
// changes to his data; nothing is applied until he ticks the ones he wants. Reply column sits on the
// right from 900px, and opens as a sheet below that.
import { computed, onMounted, ref } from 'vue'
import { PhChatCircleText, PhPaperPlaneRight } from '@phosphor-icons/vue'
import { addBriefingNote, applyBriefingActions, getBriefing, regenerateBriefing } from '../../api/ai'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { useToast } from '../../composables/useToast'
import { formatDateTime } from '../../lib/dates'
import UiButton from '../ui/UiButton.vue'
import UiSheet from '../ui/UiSheet.vue'

const data = ref(null)
const failed = ref(false)
const loaded = ref(false)
const busy = ref(false)
const error = ref('')
const draft = ref('')
const sending = ref(false)
const applying = ref(false)
const sheetOpen = ref(false)
const ticked = ref({})
const wide = useMediaQuery('(min-width: 900px)')
const toast = useToast()

const paragraphs = computed(() => (data.value?.text || '').split(/\n{2,}/).map((p) => p.trim()).filter(Boolean))
const notes = computed(() => data.value?.notes || [])
const lastIndex = computed(() => notes.value.length - 1)
const last = computed(() => (lastIndex.value >= 0 ? notes.value[lastIndex.value] : null))
const pending = computed(() => (last.value?.actions || []).filter((a) => !a.applied))
const tickedCount = computed(() => pending.value.filter((a) => ticked.value[a.index]).length)

async function load() {
  try {
    data.value = await getBriefing()
    failed.value = false
    for (const a of pending.value) ticked.value[a.index] = true
  } catch {
    failed.value = true
  } finally {
    loaded.value = true
  }
}

async function regenerate() {
  busy.value = true
  error.value = ''
  try {
    data.value = await regenerateBriefing()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

function openReply() {
  if (!wide.value) sheetOpen.value = true
}

async function send() {
  const text = draft.value.trim()
  if (!text || sending.value) return
  sending.value = true
  error.value = ''
  try {
    data.value = await addBriefingNote(text)
    draft.value = ''
    ticked.value = {}
    for (const a of pending.value) ticked.value[a.index] = true
  } catch (err) {
    error.value = err.message
  } finally {
    sending.value = false
  }
}

async function apply() {
  const indexes = pending.value.filter((a) => ticked.value[a.index]).map((a) => a.index)
  if (!indexes.length || applying.value) return
  applying.value = true
  error.value = ''
  try {
    const res = await applyBriefingActions(lastIndex.value, indexes)
    data.value = res.briefing
    const bad = res.results.filter((r) => !r.ok)
    if (bad.length) toast.error(`${bad.length} of ${res.results.length} changes failed: ${bad[0].message}`)
    else toast.success(res.results.length === 1 ? 'Applied 1 change.' : `Applied ${res.results.length} changes.`)
    ticked.value = {}
  } catch (err) {
    error.value = err.message
  } finally {
    applying.value = false
  }
}

function onKey(e) {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send()
}

onMounted(load)
</script>

<template>
  <section v-if="!failed && loaded" class="card widget" :class="{ wide }">
    <div class="main">
      <div class="card-head">
        <h2>Briefing</h2>
        <span class="meta">
          <template v-if="data">{{ data.source === 'claude' ? 'Claude' : 'Rules' }}, {{ formatDateTime(data.generated_at) }}</template>
          <UiButton size="sm" variant="ghost" :loading="busy" @click="regenerate">{{ data ? 'Regenerate' : 'Generate' }}</UiButton>
          <UiButton v-if="data && !wide" size="sm" variant="ghost" @click="openReply">
            <PhChatCircleText :size="16" weight="bold" aria-hidden="true" />
            Reply<template v-if="pending.length"> ({{ pending.length }})</template>
          </UiButton>
        </span>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <div v-if="data" class="prose">
        <p v-for="(p, i) in paragraphs" :key="i">{{ p }}</p>
      </div>
      <p v-else class="muted">No briefing for today yet. It is generated at the time set in Settings, or on demand.</p>
    </div>

    <aside v-if="data && wide" class="reply">
      <h3>Reply</h3>
      <div v-if="notes.length" class="thread">
        <div v-for="(n, i) in notes" :key="i" class="turn">
          <p class="you">{{ n.text }}</p>
          <p class="pozzy">{{ n.reply }}</p>
        </div>
      </div>
      <p v-else class="muted small">Tell Pozzy what changed: "the deploy is fixed", "that email is not my concern", "I am off this week". It rewrites the briefing and proposes changes to your data.</p>

      <div v-if="pending.length" class="proposals">
        <p class="label">Proposed changes</p>
        <label v-for="a in pending" :key="a.index" class="proposal">
          <input v-model="ticked[a.index]" type="checkbox" />
          <span><span class="title">{{ a.label }}</span><span v-if="a.reason" class="why">{{ a.reason }}</span></span>
        </label>
        <UiButton size="sm" :disabled="!tickedCount" :loading="applying" @click="apply">Apply {{ tickedCount || '' }}</UiButton>
      </div>

      <form class="composer" @submit.prevent="send">
        <textarea v-model="draft" rows="3" placeholder="Add a note to today's briefing" :disabled="sending" aria-label="Reply to the briefing" @keydown="onKey"></textarea>
        <UiButton type="submit" size="sm" :disabled="!draft.trim()" :loading="sending" aria-label="Send note">
          <PhPaperPlaneRight :size="16" weight="bold" aria-hidden="true" />
        </UiButton>
      </form>
    </aside>

    <UiSheet v-if="!wide" :open="sheetOpen" title="Reply to the briefing" @close="sheetOpen = false">
      <div class="reply in-sheet">
        <div v-if="notes.length" class="thread">
          <div v-for="(n, i) in notes" :key="i" class="turn">
            <p class="you">{{ n.text }}</p>
            <p class="pozzy">{{ n.reply }}</p>
          </div>
        </div>
        <p v-else class="muted small">Tell Pozzy what changed. It rewrites the briefing and proposes changes to your data.</p>
        <div v-if="pending.length" class="proposals">
          <p class="label">Proposed changes</p>
          <label v-for="a in pending" :key="a.index" class="proposal">
            <input v-model="ticked[a.index]" type="checkbox" />
            <span><span class="title">{{ a.label }}</span><span v-if="a.reason" class="why">{{ a.reason }}</span></span>
          </label>
          <UiButton size="sm" :disabled="!tickedCount" :loading="applying" @click="apply">Apply {{ tickedCount || '' }}</UiButton>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <form class="composer" @submit.prevent="send">
          <textarea v-model="draft" rows="3" placeholder="Add a note to today's briefing" :disabled="sending" aria-label="Reply to the briefing" @keydown="onKey"></textarea>
          <UiButton type="submit" size="sm" :disabled="!draft.trim()" :loading="sending" aria-label="Send note">
            <PhPaperPlaneRight :size="16" weight="bold" aria-hidden="true" />
          </UiButton>
        </form>
      </div>
    </UiSheet>
  </section>
</template>

<style scoped>
.widget.wide { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(280px, 1fr); gap: var(--sp-5); }
.main { min-width: 0; }
.meta { display: inline-flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.prose { max-width: 68ch; }
.prose p { font-size: var(--fs-base); line-height: 1.6; margin-bottom: var(--sp-3); }
.prose p:last-child { margin-bottom: 0; }

.reply { display: flex; flex-direction: column; gap: var(--sp-3); min-width: 0; }
.widget.wide .reply { border-left: 1px solid var(--line); padding-left: var(--sp-5); }
.reply h3 { font-size: var(--fs-sm); font-weight: 500; color: var(--ink-2); letter-spacing: 0.02em; }
.small { font-size: var(--fs-sm); line-height: 1.5; }
.thread { display: flex; flex-direction: column; gap: var(--sp-2); max-height: 240px; overflow-y: auto; }
.turn p { font-size: var(--fs-sm); line-height: 1.5; padding: var(--sp-2) var(--sp-3); border-radius: var(--r-md); }
.you { background: var(--ink); color: var(--surface); border-bottom-right-radius: 4px; margin-left: var(--sp-5); }
.pozzy { background: var(--surface-2); color: var(--ink); border-bottom-left-radius: 4px; margin-right: var(--sp-5); margin-top: 4px; }
.proposals { display: flex; flex-direction: column; gap: var(--sp-2); padding: var(--sp-3); border: 1px dashed var(--line-2); border-radius: var(--r-md); }
.label { font-size: var(--fs-xs); font-weight: 500; color: var(--ink-2); letter-spacing: 0.02em; }
.proposal { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: var(--sp-2); align-items: start; font-size: var(--fs-sm); cursor: pointer; }
.proposal input { margin-top: 3px; }
.proposal .title { display: block; }
.proposal .why { display: block; color: var(--ink-3); font-size: var(--fs-xs); }
.composer { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--sp-2); align-items: end; }
.composer textarea { resize: vertical; min-height: 64px; font-size: var(--fs-sm); }
.in-sheet { padding-top: var(--sp-2); }
</style>
