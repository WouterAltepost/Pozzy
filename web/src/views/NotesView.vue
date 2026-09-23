<script setup>
import { computed, reactive, ref } from 'vue'
import { PhNote, PhPushPin } from '@phosphor-icons/vue'
import AreaDot from '../components/shared/AreaDot.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import TagsInput from '../components/shared/TagsInput.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useReady } from '../composables/useReady'
import { useMediaQuery } from '../composables/useMediaQuery'
import UiModal from '../components/ui/UiModal.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiField from '../components/ui/UiField.vue'
import { formatDateTime } from '../lib/dates'
import { useNotesStore } from '../stores/notes'

const store = useNotesStore()
const error = ref('')
const selectedId = ref(null)
const creating = ref(false)
const form = reactive({ title: '', body: '', area_id: null, tags: [], pinned: false })

const selected = computed(() => store.items.find((n) => n.id === selectedId.value) || null)

const ready = useReady(() => store.load())
const phone = useMediaQuery('(max-width: 699px)')

async function run(fn) {
  error.value = ''
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  }
}

function open(note) {
  selectedId.value = note.id
  creating.value = false
  Object.assign(form, { title: note.title, body: note.body, area_id: note.area_id, tags: [...note.tags], pinned: note.pinned })
}

function startNew() {
  creating.value = true
  selectedId.value = null
  Object.assign(form, { title: '', body: '', area_id: null, tags: [], pinned: false })
}

function save() {
  const body = { title: form.title, body: form.body, area_id: form.area_id || null, tags: form.tags, pinned: form.pinned }
  run(async () => {
    if (creating.value) {
      const note = await store.create(body)
      creating.value = false
      selectedId.value = note.id
    } else if (selected.value) {
      await store.update(selected.value.id, body)
    }
  })
}

function remove() {
  if (!selected.value || !window.confirm('Delete this note?')) return
  run(async () => {
    await store.remove(selected.value.id)
    selectedId.value = null
  })
}

// Minimal markdown: headings, bold, italic, code, lists, links, paragraphs. Escapes HTML first.
function renderMarkdown(text) {
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const lines = esc(text || '').split('\n')
  const out = []
  let inList = false
  const inline = (s) =>
    s
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
  for (const line of lines) {
    const list = line.match(/^\s*[-*]\s+(.*)/)
    if (list) {
      if (!inList) { out.push('<ul>'); inList = true }
      out.push(`<li>${inline(list[1])}</li>`)
      continue
    }
    if (inList) { out.push('</ul>'); inList = false }
    const h = line.match(/^(#{1,3})\s+(.*)/)
    if (h) out.push(`<h${h[1].length + 2}>${inline(h[2])}</h${h[1].length + 2}>`)
    else if (line.trim() === '') out.push('')
    else out.push(`<p>${inline(line)}</p>`)
  }
  if (inList) out.push('</ul>')
  return out.join('\n')
}
</script>

<template>
  <div class="notes">
    <div v-if="phone" class="phead">
      <div><h1>Notes</h1><span class="muted small num">{{ store.items.length }} {{ store.items.length === 1 ? 'note' : 'notes' }}</span></div>
      <UiButton variant="primary" size="sm" @click="startNew">New note</UiButton>
    </div>
    <div v-if="phone" class="pfilters">
      <input v-model="store.filters.q" type="search" placeholder="Search" aria-label="Search notes" class="psearch" @change="store.load()" />
      <AreaSelect v-model="store.filters.area_id" aria-label="Area" @update:model-value="store.load()" />
      <select v-model="store.filters.tag" aria-label="Tag" @change="store.load()">
        <option value="">All tags</option>
        <option v-for="t in store.allTags" :key="t" :value="t">{{ t }}</option>
      </select>
    </div>
    <PageHeader v-else title="Notes">
      <input v-model="store.filters.q" type="search" placeholder="Search" aria-label="Search notes" class="search" @change="store.load()" />
      <AreaSelect v-model="store.filters.area_id" aria-label="Area" @update:model-value="store.load()" />
      <select v-model="store.filters.tag" aria-label="Tag" @change="store.load()">
        <option value="">All tags</option>
        <option v-for="t in store.allTags" :key="t" :value="t">{{ t }}</option>
      </select>
      <UiButton variant="primary" @click="startNew">New note</UiButton>
    </PageHeader>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading notes">

    <div class="layout">
      <ul class="list">
        <li v-if="!store.items.length" class="empty-item">
          <UiEmpty compact title="No notes" hint="Deliberately minimal: an area, tags and markdown.">
            <template #icon><PhNote /></template>
          </UiEmpty>
        </li>
        <li v-for="n in store.items" :key="n.id" class="note-item" :class="{ active: n.id === selectedId }">
          <button type="button" class="note-btn" @click="open(n)">
            <span class="title"><PhPushPin v-if="n.pinned" class="pin" weight="fill" aria-label="Pinned" /> {{ n.title }}</span>
            <span class="meta"><AreaDot :area-id="n.area_id" label /> <span v-for="t in n.tags" :key="t" class="tag">{{ t }}</span> <span class="muted xs num">{{ formatDateTime(n.updated_at) }}</span></span>
          </button>
        </li>
      </ul>

      <div v-if="(creating || selected) && !phone" class="card editor">
        <form @submit.prevent="save">
          <UiField label="Title"><input v-model="form.title" type="text" required maxlength="200" /></UiField>
          <div class="row">
            <UiField label="Area"><AreaSelect v-model="form.area_id" /></UiField>
            <UiField label="Tags" class="grow"><TagsInput v-model="form.tags" /></UiField>
            <label class="check"><input v-model="form.pinned" type="checkbox" /> Pinned</label>
          </div>
          <UiField label="Body" hint="Markdown: headings, lists, bold, links"><textarea v-model="form.body" rows="14" class="body"></textarea></UiField>
          <div class="actions">
            <UiButton type="submit" variant="primary">{{ creating ? 'Create' : 'Save' }}</UiButton>
            <UiButton v-if="selected" variant="danger" class="push" @click="remove">Delete</UiButton>
          </div>
        </form>
        <div v-if="form.body" class="preview" v-html="renderMarkdown(form.body)"></div>
      </div>
      <div v-else-if="!phone" class="card placeholder">
        <UiEmpty title="Select a note or create one" hint="Pinned notes stay on top of the list.">
          <template #icon><PhNote /></template>
        </UiEmpty>
      </div>
    </div>
    </UiLoadGate>

    <UiModal v-if="phone" :open="Boolean(creating || selected)" :title="creating ? 'New note' : 'Note'" size="lg" @close="creating = false; selectedId = null">
      <form class="pform" @submit.prevent="save">
        <UiField label="Title"><input v-model="form.title" type="text" required maxlength="200" /></UiField>
        <div class="pair">
          <UiField label="Area"><AreaSelect v-model="form.area_id" /></UiField>
          <label class="check"><input v-model="form.pinned" type="checkbox" /> Pinned</label>
        </div>
        <UiField label="Tags"><TagsInput v-model="form.tags" /></UiField>
        <UiField label="Body" hint="Markdown"><textarea v-model="form.body" rows="10" class="body"></textarea></UiField>
        <div class="actions">
          <UiButton type="submit" variant="primary">{{ creating ? 'Create' : 'Save' }}</UiButton>
          <UiButton v-if="selected" variant="danger" class="push" @click="remove">Delete</UiButton>
        </div>
      </form>
    </UiModal>
  </div>
</template>

<style scoped>
.search { width: 160px; }
.layout { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-4); align-items: start; }
.phead { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.phead h1 { font-size: var(--fs-title); }
.pfilters { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: var(--sp-2); margin-bottom: var(--sp-4); }
.psearch { min-width: 0; }
.pform { display: flex; flex-direction: column; gap: var(--sp-3); }
.pform .pair { display: grid; grid-template-columns: 1fr auto; gap: var(--sp-3); align-items: end; }
.pform .actions { display: flex; gap: var(--sp-2); }
@media (max-width: 699px) {
  .list { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); box-shadow: var(--shadow-1); padding: 4px 16px; }
  .list :deep(.note-item) { border: 0; border-top: 1px solid var(--line); border-radius: 0; box-shadow: none; }
  .list :deep(.note-item:first-child) { border-top: 0; }
}
@media (min-width: 900px) { .layout { grid-template-columns: 300px minmax(0, 1fr); gap: var(--sp-5); } }
.list { display: flex; flex-direction: column; gap: var(--sp-2); }
.note-btn { display: flex; flex-direction: column; align-items: stretch; gap: 4px; width: 100%; text-align: left; padding: var(--sp-2) var(--sp-3); border: 1px solid var(--line); border-radius: var(--r-md); background: var(--surface); color: inherit; transition: border-color var(--dur-hover) ease, box-shadow var(--dur-hover) ease; }
.note-item.active .note-btn { border-color: var(--ink); box-shadow: 0 0 0 1px var(--ink) inset; }
@media (hover: hover) and (pointer: fine) { .note-item:not(.active) .note-btn:hover { border-color: var(--line-2); box-shadow: var(--shadow-1); } }
.title { display: flex; align-items: center; gap: 6px; font-weight: 500; }
.pin { width: 13px; height: 13px; color: var(--brand); }
.meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.editor form { display: flex; flex-direction: column; gap: var(--sp-3); }
.editor .body { font-family: ui-monospace, 'SF Mono', Menlo, monospace; font-size: var(--fs-md); line-height: 1.6; }
.row { display: flex; flex-wrap: wrap; gap: var(--sp-3); align-items: end; }
.grow { flex: 1 1 160px; }
.check { display: flex; align-items: center; gap: 6px; height: var(--control-h); }
.actions { display: flex; gap: var(--sp-2); }
.push { margin-left: auto; }
.placeholder { margin: 0; }
.preview { border-top: 1px solid var(--line); margin-top: var(--sp-4); padding-top: var(--sp-4); max-width: 68ch; font-size: var(--fs-base); line-height: 1.6; }
.preview :deep(h3) { font-size: var(--fs-xl); margin: var(--sp-4) 0 var(--sp-2); }
.preview :deep(h4) { font-size: var(--fs-lg); margin: var(--sp-3) 0 var(--sp-1); }
.preview :deep(h5) { font-size: var(--fs-base); margin: var(--sp-3) 0 var(--sp-1); }
.preview :deep(p) { margin: 0 0 var(--sp-2); }
.preview :deep(ul) { list-style: disc; padding-left: 1.2em; margin: 0 0 var(--sp-2); }
</style>
