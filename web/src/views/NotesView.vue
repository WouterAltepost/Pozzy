<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AreaDot from '../components/shared/AreaDot.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import TagsInput from '../components/shared/TagsInput.vue'
import { formatDateTime } from '../lib/dates'
import { useNotesStore } from '../stores/notes'

const store = useNotesStore()
const error = ref('')
const selectedId = ref(null)
const creating = ref(false)
const form = reactive({ title: '', body: '', area_id: null, tags: [], pinned: false })

const selected = computed(() => store.items.find((n) => n.id === selectedId.value) || null)

onMounted(() => store.load())

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
    <div class="head">
      <h1>Notes</h1>
      <input v-model="store.filters.q" type="search" placeholder="Search" @change="store.load()" />
      <AreaSelect v-model="store.filters.area_id" @update:model-value="store.load()" />
      <select v-model="store.filters.tag" @change="store.load()">
        <option value="">All tags</option>
        <option v-for="t in store.allTags" :key="t" :value="t">{{ t }}</option>
      </select>
      <button type="button" @click="startNew">New note</button>
    </div>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>

    <div class="layout">
      <ul class="list">
        <li v-if="!store.items.length" class="muted">No notes.</li>
        <li v-for="n in store.items" :key="n.id" :class="{ active: n.id === selectedId }" @click="open(n)">
          <div class="title"><span v-if="n.pinned" title="pinned">&#9733;</span> {{ n.title }}</div>
          <div class="meta"><AreaDot :area-id="n.area_id" label /> <span v-for="t in n.tags" :key="t" class="tag">{{ t }}</span> <span class="muted">{{ formatDateTime(n.updated_at) }}</span></div>
        </li>
      </ul>

      <div v-if="creating || selected" class="card editor">
        <form @submit.prevent="save">
          <input v-model="form.title" type="text" placeholder="Title" required maxlength="200" />
          <div class="row">
            <AreaSelect v-model="form.area_id" />
            <TagsInput v-model="form.tags" />
            <label class="check"><input v-model="form.pinned" type="checkbox" /> pinned</label>
          </div>
          <textarea v-model="form.body" rows="14" placeholder="Markdown body"></textarea>
          <div class="actions">
            <button type="submit">{{ creating ? 'Create' : 'Save' }}</button>
            <button v-if="selected" type="button" class="danger" @click="remove">Delete</button>
          </div>
        </form>
        <div v-if="form.body" class="preview" v-html="renderMarkdown(form.body)"></div>
      </div>
      <p v-else class="muted">Select a note or create one.</p>
    </div>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; margin: 0; }
.head { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin-bottom: 1rem; }
.head input, .head select { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.layout { display: grid; grid-template-columns: 1fr; gap: 1rem; }
@media (min-width: 860px) { .layout { grid-template-columns: 280px 1fr; } }
.list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.3rem; }
.list li { background: #fff; border: 1px solid #e5e7eb; border-radius: 4px; padding: 0.45rem 0.6rem; cursor: pointer; }
.list li.active { border-color: #2563eb; }
.title { font-size: 0.92rem; }
.meta { display: flex; flex-wrap: wrap; gap: 0.4rem; font-size: 0.75rem; margin-top: 0.15rem; }
.tag { background: #f3f4f6; padding: 0 0.35rem; border-radius: 3px; }
.editor form { display: flex; flex-direction: column; gap: 0.5rem; }
.editor input[type='text'], .editor textarea { font: inherit; padding: 0.4rem; border: 1px solid #d1d5db; border-radius: 4px; width: 100%; }
.editor textarea { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85rem; }
.row { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.row :deep(input[type='text']), .row select { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.check { display: flex; align-items: center; gap: 0.3rem; font-size: 0.85rem; }
.actions { display: flex; gap: 0.5rem; }
.danger { color: #b91c1c; margin-left: auto; }
.preview { border-top: 1px solid #e5e7eb; margin-top: 1rem; padding-top: 0.5rem; font-size: 0.92rem; }
.preview :deep(h3) { font-size: 1.1rem; margin: 0.6rem 0 0.2rem; }
.preview :deep(h4), .preview :deep(h5) { font-size: 1rem; margin: 0.5rem 0 0.2rem; }
.preview :deep(p) { margin: 0.3rem 0; }
.preview :deep(code) { background: #f3f4f6; padding: 0 0.25rem; border-radius: 3px; }
</style>
