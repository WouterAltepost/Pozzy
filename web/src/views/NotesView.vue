<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { PhCaretRight, PhMagnifyingGlass, PhNote, PhPlus, PhPushPin, PhPushPinSlash, PhTrash } from '@phosphor-icons/vue'
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import SwipeRow from '../components/ios/SwipeRow.vue'
import UiConfirm from '../components/ui/UiConfirm.vue'
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
// Below 1024px this is the iOS app: a Notes style list, the editor in a sheet.
const phone = useMediaQuery('(max-width: 1023px)')
const route = useRoute()
const deleting = ref(null) // the note waiting for the delete confirmation

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
  if (selected.value) deleting.value = selected.value
}
function confirmRemove() {
  const note = deleting.value
  deleting.value = null
  if (!note) return
  run(async () => {
    await store.remove(note.id)
    if (selectedId.value === note.id) selectedId.value = null
  })
}
const leadingFor = (n) => [{ label: n.pinned ? 'Unpin' : 'Pin', icon: n.pinned ? PhPushPinSlash : PhPushPin, color: 'var(--warn)', action: () => run(() => store.update(n.id, { pinned: !n.pinned })) }]
const trailingFor = (n) => [{ label: 'Delete', icon: PhTrash, color: 'var(--danger)', action: () => (deleting.value = n) }]
// The second line of a row, like Notes: the date, then the start of the text without markup.
function previewOf(n) {
  const line = (n.body || '').split('\n').map((l) => l.replace(/^\s*(#{1,3}|[-*])\s+/, '').replace(/[*`]/g, '').trim()).find(Boolean)
  return line || 'No additional text'
}
function shortDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'numeric', year: '2-digit' })
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
  <component :is="phone ? PullToRefresh : 'div'" :action="phone ? () => store.load() : undefined">
  <div class="notes">
    <Teleport v-if="phone && route.name === 'notes'" defer to="#nav-trailing">
      <button type="button" class="icon-btn" aria-label="New note" @click="startNew"><PhPlus weight="regular" /></button>
    </Teleport>
    <div v-if="phone" class="phead">
      <h1>Notes</h1><span class="sub num">{{ store.items.length }} {{ store.items.length === 1 ? 'note' : 'notes' }}</span>
    </div>
    <div v-if="phone" class="pfilters">
      <label class="psearch">
        <PhMagnifyingGlass class="glass" weight="bold" aria-hidden="true" />
        <input v-model="store.filters.q" type="search" enterkeyhint="search" placeholder="Search" aria-label="Search notes" @change="store.load()" />
      </label>
      <AreaSelect v-model="store.filters.area_id" aria-label="Area" class="pf" @update:model-value="store.load()" />
      <select v-model="store.filters.tag" aria-label="Tag" class="pf" @change="store.load()">
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

    <ul v-if="phone" class="plate">
      <li v-if="!store.items.length" class="pempty">
        <UiEmpty title="No notes" hint="Deliberately minimal: an area, tags and markdown.">
          <template #icon><PhNote /></template>
        </UiEmpty>
      </li>
      <li v-for="n in store.items" :key="n.id" class="pli">
        <SwipeRow :leading="leadingFor(n)" :trailing="trailingFor(n)">
          <button type="button" class="nrow pressable" @click="open(n)">
            <span class="nbody">
              <span class="ntitle"><PhPushPin v-if="n.pinned" class="pin" weight="fill" aria-label="Pinned" /><span class="truncate">{{ n.title }}</span></span>
              <span class="nsub"><span class="num">{{ shortDate(n.updated_at) }}</span><span class="truncate">{{ previewOf(n) }}</span></span>
              <span v-if="n.area_id || n.tags.length" class="nmeta"><AreaDot :area-id="n.area_id" label /><span v-for="t in n.tags" :key="t" class="tag">{{ t }}</span></span>
            </span>
            <PhCaretRight class="chev" weight="bold" aria-hidden="true" />
          </button>
        </SwipeRow>
      </li>
    </ul>
    <div v-else class="layout">
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
        <div class="grp">
          <label class="frow"><input v-model="form.title" type="text" class="fin ftitle" placeholder="Title" aria-label="Title" required maxlength="200" /></label>
        </div>
        <div class="grp">
          <label class="frow"><span class="flabel">Area</span><AreaSelect v-model="form.area_id" class="fval" /></label>
          <label class="frow"><span class="flabel">Tags</span><TagsInput v-model="form.tags" class="fval" placeholder="None" /></label>
          <label class="frow"><span class="flabel">Pinned</span><input v-model="form.pinned" type="checkbox" role="switch" /></label>
        </div>
        <div class="grp"><textarea v-model="form.body" rows="10" class="farea" placeholder="Body (markdown)" aria-label="Body"></textarea></div>
        <UiButton type="submit" variant="primary" block class="psave">{{ creating ? 'Create note' : 'Save' }}</UiButton>
        <button v-if="selected" type="button" class="pdelete" @click="remove">Delete note</button>
      </form>
    </UiModal>
    <UiConfirm :open="Boolean(deleting)" title="Delete this note?" :message="deleting ? `“${deleting.title}” is removed for good.` : ''" confirm-label="Delete note" danger @confirm="confirmRemove" @cancel="deleting = null" />
  </div>
  </component>
</template>

<style scoped>
.search { width: 160px; }
.layout { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-4); align-items: start; }
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
/* iOS: large title, a filled search field with the area and tag menus under it, the notes as
   one inset grouped list, the editor as a grouped form in a sheet. */
@media (max-width: 1023px) {
  .phead { margin: 4px 0 var(--sp-3); }
  .sub { display: block; margin-top: 2px; font-size: var(--fs-sm); color: var(--ink-3); }
  .pfilters { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-2); margin-bottom: var(--sp-4); }
  .psearch { position: relative; display: block; grid-column: 1 / -1; }
  .psearch .glass { position: absolute; left: 8px; top: 50%; width: 17px; height: 17px; margin-top: -8.5px; color: var(--ink-3); pointer-events: none; }
  .psearch input { width: 100%; height: 36px; padding: 0 8px 0 31px; border-radius: var(--r-md); }
  .pfilters .pf { width: 100%; min-width: 0; height: 36px; font-size: var(--fs-md); }
  .plate { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .pli { position: relative; }
  .pli + .pli::before { content: ''; position: absolute; z-index: 2; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line); pointer-events: none; }
  .nrow { display: flex; align-items: center; gap: var(--sp-3); width: 100%; min-height: 44px; padding: 10px 16px; border: 0; border-radius: 0; background: none; box-shadow: none; color: var(--ink); font: inherit; text-align: left; }
  .nbody { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
  .ntitle { display: flex; align-items: center; gap: 6px; min-width: 0; font-size: 1.0625rem; font-weight: 600; }
  .ntitle .pin { flex: none; width: 14px; height: 14px; color: var(--warn); }
  .nsub { display: flex; gap: var(--sp-2); min-width: 0; font-size: var(--fs-md); color: var(--ink-3); }
  .nsub .num { flex: none; color: var(--ink-2); }
  .nmeta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 2px; font-size: var(--fs-sm); color: var(--ink-3); }
  .chev { flex: none; width: 13px; height: 13px; color: var(--ink-4); }
  .pform { display: flex; flex-direction: column; gap: var(--sp-4); }
  .grp { background: var(--surface-2); border-radius: var(--r-lg); overflow: hidden; }
  .frow { position: relative; display: flex; align-items: center; gap: var(--sp-3); min-height: 44px; padding: 0 16px; font-size: 1.0625rem; }
  .frow + .frow::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .flabel { flex: 1 0 auto; }
  .frow .fin, .frow .fval, .grp .farea { border: 0; background-color: transparent; box-shadow: none; }
  .frow .fin { flex: 1; min-width: 0; height: 44px; padding: 0; }
  .frow .ftitle { font-weight: 600; }
  .frow .fval { flex: 1 1 0; min-width: 0; height: 44px; padding: 0; color: var(--ink-3); text-align: right; text-align-last: right; }
  .frow select.fval { padding-right: 22px; background-position: right 2px center; }
  .grp .farea { display: block; width: 100%; padding: 11px 16px; font-family: inherit; line-height: 1.45; resize: vertical; }
  .frow .fin:focus-visible, .frow .fval:focus-visible, .grp .farea:focus-visible { box-shadow: none; }
  .psave { height: 50px; font-size: 1.0625rem; margin-top: var(--sp-1); }
  .pdelete { height: 44px; border: 0; background: none; box-shadow: none; color: var(--danger); font: inherit; font-size: 1.0625rem; }
}
</style>
