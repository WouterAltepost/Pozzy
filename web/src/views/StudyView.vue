<script setup>
import { reactive, ref } from 'vue'
import { PhGraduationCap, PhX } from '@phosphor-icons/vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiBadge from '../components/ui/UiBadge.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiField from '../components/ui/UiField.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import UiModal from '../components/ui/UiModal.vue'
import { useReady } from '../composables/useReady'
import { useMediaQuery } from '../composables/useMediaQuery'
import { daysUntil, formatDateTime, formatDay } from '../lib/dates'
import { APPLICATION_STATUSES, useStudyStore } from '../stores/study'

const store = useStudyStore()
const error = ref('')
const courseForm = reactive({ name: '', code: '', period: '', ects: null })
const deadlineForm = reactive({ course_id: '', title: '', due_date: '', due_time: '23:59', type: 'assignment' })
const appForm = reactive({ company: '', role: '', link: '' })
const editingApp = ref(null)
const dragOver = ref(null)
const lifting = ref(null)

const ready = useReady(() => store.load())
const phone = useMediaQuery('(max-width: 699px)')
const adding = ref(null) // 'deadline' | 'course' | 'application' on the phone

async function run(fn) {
  error.value = ''
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  }
}

function addCourse() {
  adding.value = null
  if (!courseForm.name.trim()) return
  run(async () => {
    await store.createCourse({ name: courseForm.name, code: courseForm.code || null, period: courseForm.period || null, ects: courseForm.ects || null })
    Object.assign(courseForm, { name: '', code: '', period: '', ects: null })
  })
}

function removeCourse(c) {
  if (window.confirm(`Delete course "${c.name}" and its deadlines?`)) run(() => store.removeCourse(c.id))
}

function addDeadline() {
  adding.value = null
  if (!deadlineForm.course_id || !deadlineForm.title.trim() || !deadlineForm.due_date) return
  const due = new Date(`${deadlineForm.due_date}T${deadlineForm.due_time || '23:59'}`)
  run(async () => {
    await store.createDeadline({ course_id: deadlineForm.course_id, title: deadlineForm.title, due_at: due.toISOString(), type: deadlineForm.type })
    Object.assign(deadlineForm, { title: '', due_date: '' })
  })
}

function dueTone(day) {
  const days = daysUntil(day)
  if (days === null) return 'neutral'
  if (days < 0) return 'danger'
  if (days <= 3) return 'warn'
  return 'neutral'
}

function addApplication() {
  adding.value = null
  if (!appForm.company.trim()) return
  run(async () => {
    await store.createApplication({ company: appForm.company, role: appForm.role || null, link: appForm.link || null })
    Object.assign(appForm, { company: '', role: '', link: '' })
  })
}

function onDragStart(a, event) {
  lifting.value = a.id
  event.dataTransfer.setData('text/plain', a.id)
}

function onDrop(status, event) {
  const id = event.dataTransfer.getData('text/plain')
  dragOver.value = null
  const current = store.applications.find((a) => a.id === id)
  if (!current || current.status === status) return
  run(() => store.updateApplication(id, { status }))
}

function saveApp() {
  const a = editingApp.value
  run(async () => {
    await store.updateApplication(a.id, { company: a.company, role: a.role || null, next_step: a.next_step || null, next_step_date: a.next_step_date || null, notes: a.notes || null, link: a.link || null, applied_at: a.applied_at || null })
    editingApp.value = null
  })
}

function removeApp(a) {
  if (window.confirm(`Delete application at ${a.company}?`)) run(() => store.removeApplication(a.id))
}
</script>

<template>
  <div class="study">
    <PageHeader v-if="!phone" title="Study" />
    <div v-else class="phead"><div><h1>Study</h1><span class="muted small num">{{ store.deadlines.filter((d) => !d.done).length }} open deadlines, {{ store.applications.length }} applications</span></div></div>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading study">

    <section class="card">
      <div class="card-head">
        <h2>Deadlines</h2>
        <UiButton v-if="phone" size="sm" class="padd" @click="adding = 'deadline'">Add</UiButton>
        <span class="meta"><label class="check"><input v-model="store.includeDoneDeadlines" type="checkbox" @change="store.load()" /> Show done</label></span>
      </div>
      <ul class="deadlines">
        <li v-if="!store.deadlines.length" class="muted small hint">No deadlines.</li>
        <li v-for="d in store.deadlines" :key="d.id" class="list-row" :class="{ done: d.done }">
          <input type="checkbox" :checked="d.done" :aria-label="d.title" @change="run(() => store.updateDeadline(d.id, { done: !d.done }))" />
          <UiBadge tone="info">{{ d.course_code || d.course_name }}</UiBadge>
          <span class="title">{{ d.title }} <span class="muted small">{{ d.type }}</span></span>
          <UiBadge :tone="dueTone(d.due_at.slice(0, 10))" class="num">{{ formatDateTime(d.due_at) }}</UiBadge>
          <RouterLink v-if="d.task_id" :to="{ name: 'tasks' }" class="muted small">task</RouterLink>
          <button type="button" class="icon-btn" aria-label="Remove deadline" @click="run(() => store.removeDeadline(d.id))"><PhX /></button>
        </li>
      </ul>
      <form v-if="!phone" class="inline" @submit.prevent="addDeadline">
        <UiField label="Course">
          <select v-model="deadlineForm.course_id" required>
            <option value="" disabled>Choose</option>
            <option v-for="c in store.courses" :key="c.id" :value="c.id">{{ c.code || c.name }}</option>
          </select>
        </UiField>
        <UiField label="Title" class="grow"><input v-model="deadlineForm.title" type="text" required /></UiField>
        <UiField label="Due"><input v-model="deadlineForm.due_date" type="date" required /></UiField>
        <UiField label="Time"><input v-model="deadlineForm.due_time" type="time" /></UiField>
        <UiField label="Type">
          <select v-model="deadlineForm.type">
            <option value="assignment">assignment</option>
            <option value="exam">exam</option>
            <option value="presentation">presentation</option>
            <option value="other">other</option>
          </select>
        </UiField>
        <UiButton type="submit" variant="primary" :disabled="!store.courses.length">Add deadline</UiButton>
        <span v-if="!store.courses.length" class="muted small">Add a course first.</span>
      </form>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Courses</h2>
        <UiButton v-if="phone" size="sm" class="padd" @click="adding = 'course'">Add</UiButton>
        <span class="meta"><label class="check"><input v-model="store.includeClosedCourses" type="checkbox" @change="store.load()" /> Show finished</label></span>
      </div>
      <div v-if="store.courses.length" class="table-wrap">
        <table class="ui courses">
          <thead><tr><th>Code</th><th>Name</th><th>Period</th><th class="num">ECTS</th><th>Status</th><th></th></tr></thead>
          <tbody>
            <tr v-for="c in store.courses" :key="c.id">
              <td class="num">{{ c.code }}</td>
              <td>{{ c.name }} <span class="muted small num">{{ c.deadlines?.length || 0 }} deadlines</span></td>
              <td>{{ c.period }}</td>
              <td class="num">{{ c.ects }}</td>
              <td>
                <select :value="c.status" aria-label="Status" @change="run(() => store.updateCourse(c.id, { status: $event.target.value }))">
                  <option v-for="s in ['planned', 'active', 'passed', 'failed', 'dropped']" :key="s" :value="s">{{ s }}</option>
                </select>
              </td>
              <td class="actions"><button type="button" class="icon-btn" aria-label="Remove course" @click="removeCourse(c)"><PhX /></button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <UiEmpty v-else compact title="No courses yet" hint="Add a course to attach deadlines to it.">
        <template #icon><PhGraduationCap /></template>
      </UiEmpty>
      <form v-if="!phone" class="inline" @submit.prevent="addCourse">
        <UiField label="Course name" class="grow"><input v-model="courseForm.name" type="text" required /></UiField>
        <UiField label="Code"><input v-model="courseForm.code" type="text" class="short" /></UiField>
        <UiField label="Period"><input v-model="courseForm.period" type="text" class="short" /></UiField>
        <UiField label="ECTS"><input v-model.number="courseForm.ects" type="number" min="0" step="0.5" class="short" /></UiField>
        <UiButton type="submit" variant="primary">Add course</UiButton>
      </form>
    </section>

    <section class="card">
      <div class="card-head"><h2>Internship applications</h2><UiButton v-if="phone" size="sm" class="padd" @click="adding = 'application'">Add</UiButton></div>
      <form v-if="!phone" class="inline" @submit.prevent="addApplication">
        <UiField label="Company" class="grow"><input v-model="appForm.company" type="text" required /></UiField>
        <UiField label="Role" class="grow"><input v-model="appForm.role" type="text" /></UiField>
        <UiField label="Link" class="grow"><input v-model="appForm.link" type="url" placeholder="https://" /></UiField>
        <UiButton type="submit" variant="primary">Add</UiButton>
      </form>
      <div v-if="phone" class="stages">
        <template v-for="status in APPLICATION_STATUSES" :key="status">
          <div v-if="store.applicationsByStatus(status).length" class="stage">
            <div class="stage-head"><span>{{ status }}</span><span class="muted small num">{{ store.applicationsByStatus(status).length }}</span></div>
            <button v-for="a in store.applicationsByStatus(status)" :key="a.id" type="button" class="srow" @click="editingApp = { ...a }">
              <span class="company">{{ a.company }}</span>
              <span v-if="a.role" class="muted small">{{ a.role }}</span>
              <span v-if="a.next_step" class="small next" :class="{ soon: daysUntil(a.next_step_date) !== null && daysUntil(a.next_step_date) <= 2 }">{{ a.next_step }}<span v-if="a.next_step_date">, {{ formatDay(a.next_step_date) }}</span></span>
            </button>
          </div>
        </template>
        <p v-if="!store.applications.length" class="muted small hint">No applications yet.</p>
      </div>
      <div v-else class="kanban">
        <div
          v-for="status in APPLICATION_STATUSES"
          :key="status"
          class="column"
          :class="{ over: dragOver === status }"
          @dragover.prevent="dragOver = status"
          @dragleave="dragOver = null"
          @drop.prevent="onDrop(status, $event)"
        >
          <header><span>{{ status }}</span> <span class="muted num">{{ store.applicationsByStatus(status).length }}</span></header>
          <button
            v-for="a in store.applicationsByStatus(status)"
            :key="a.id"
            type="button"
            class="app"
            :class="{ lifting: lifting === a.id }"
            draggable="true"
            @dragstart="onDragStart(a, $event)"
            @dragend="lifting = null"
            @click="editingApp = { ...a }"
          >
            <span class="company">{{ a.company }}</span>
            <span v-if="a.role" class="muted small">{{ a.role }}</span>
            <span v-if="a.next_step" class="small next" :class="{ soon: daysUntil(a.next_step_date) !== null && daysUntil(a.next_step_date) <= 2 }">
              {{ a.next_step }}<span v-if="a.next_step_date">, {{ formatDay(a.next_step_date) }}</span>
            </span>
          </button>
        </div>
      </div>

    </section>

    </UiLoadGate>

    <UiModal :open="adding === 'deadline'" title="New deadline" size="sm" @close="adding = null">
      <form class="pform" @submit.prevent="addDeadline">
        <UiField label="Course"><select v-model="deadlineForm.course_id" required><option value="" disabled>Choose</option><option v-for="c in store.courses" :key="c.id" :value="c.id">{{ c.name }}</option></select></UiField>
        <UiField label="Title"><input v-model="deadlineForm.title" type="text" required /></UiField>
        <div class="pair"><UiField label="Due"><input v-model="deadlineForm.due_date" type="date" required /></UiField><UiField label="Time"><input v-model="deadlineForm.due_time" type="time" /></UiField></div>
        <UiField label="Type"><select v-model="deadlineForm.type"><option value="assignment">assignment</option><option value="exam">exam</option><option value="presentation">presentation</option><option value="other">other</option></select></UiField>
        <p v-if="!store.courses.length" class="muted small">Add a course first.</p>
        <div class="actions"><UiButton type="submit" variant="primary" :disabled="!store.courses.length">Add deadline</UiButton><UiButton variant="ghost" @click="adding = null">Cancel</UiButton></div>
      </form>
    </UiModal>
    <UiModal :open="adding === 'course'" title="New course" size="sm" @close="adding = null">
      <form class="pform" @submit.prevent="addCourse">
        <UiField label="Course name"><input v-model="courseForm.name" type="text" required /></UiField>
        <div class="pair"><UiField label="Code"><input v-model="courseForm.code" type="text" /></UiField><UiField label="Period"><input v-model="courseForm.period" type="text" /></UiField></div>
        <UiField label="ECTS"><input v-model.number="courseForm.ects" type="number" min="0" step="0.5" /></UiField>
        <div class="actions"><UiButton type="submit" variant="primary">Add course</UiButton><UiButton variant="ghost" @click="adding = null">Cancel</UiButton></div>
      </form>
    </UiModal>
    <UiModal :open="adding === 'application'" title="New application" size="sm" @close="adding = null">
      <form class="pform" @submit.prevent="addApplication">
        <UiField label="Company"><input v-model="appForm.company" type="text" required /></UiField>
        <UiField label="Role"><input v-model="appForm.role" type="text" /></UiField>
        <UiField label="Link"><input v-model="appForm.link" type="url" placeholder="https://" /></UiField>
        <div class="actions"><UiButton type="submit" variant="primary">Add</UiButton><UiButton variant="ghost" @click="adding = null">Cancel</UiButton></div>
      </form>
    </UiModal>

    <UiModal :open="Boolean(editingApp)" :title="editingApp?.company || 'Application'" size="md" @close="editingApp = null">
      <form v-if="editingApp" class="app-form" @submit.prevent="saveApp">
        <UiField label="Company"><input v-model="editingApp.company" type="text" required /></UiField>
        <UiField label="Role"><input v-model="editingApp.role" type="text" /></UiField>
        <UiField label="Link"><input v-model="editingApp.link" type="url" /></UiField>
        <UiField label="Applied on"><input v-model="editingApp.applied_at" type="date" /></UiField>
        <UiField label="Next step"><input v-model="editingApp.next_step" type="text" /></UiField>
        <UiField label="Next step date"><input v-model="editingApp.next_step_date" type="date" /></UiField>
        <UiField label="Notes" class="wide"><textarea v-model="editingApp.notes" rows="3"></textarea></UiField>
        <div class="actions wide">
          <UiButton type="submit" variant="primary">Save</UiButton>
          <UiButton @click="editingApp = null">Cancel</UiButton>
          <a v-if="editingApp.link" :href="editingApp.link" target="_blank" rel="noopener" class="small">Open link</a>
          <UiButton variant="danger" class="push" @click="removeApp(editingApp); editingApp = null">Delete</UiButton>
        </div>
      </form>
    </UiModal>
  </div>
</template>

<style scoped>
.phead { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); margin-bottom: var(--sp-4); }
.phead h1 { font-size: var(--fs-title); }
.padd { margin-left: auto; }
.pform { display: flex; flex-direction: column; gap: var(--sp-3); }
.pform .pair { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-2); }
.pform .actions { display: flex; gap: var(--sp-2); }
.stages { margin-top: var(--sp-3); }
.stage { padding: 6px 0; }
.stage-head { display: flex; justify-content: space-between; align-items: baseline; font-weight: 600; font-size: var(--fs-md); text-transform: capitalize; padding: 6px 0 2px; }
.srow { display: flex; flex-direction: column; gap: 2px; width: 100%; text-align: left; background: none; border: 0; border-top: 1px solid var(--line); padding: 10px 0; color: inherit; font-size: var(--fs-base); }
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-md); }
.hint { padding: var(--sp-2) 0; }
.deadlines .title { flex: 1; min-width: 0; }
.inline { display: flex; flex-wrap: wrap; gap: var(--sp-3); align-items: end; margin-top: var(--sp-4); }
.grow { flex: 1 1 160px; min-width: 140px; }
.short { width: 96px; }
.courses .actions { text-align: right; }
.kanban { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--sp-2); margin-top: var(--sp-4); }
@media (min-width: 900px) { .kanban { grid-template-columns: repeat(5, minmax(0, 1fr)); } }
.column { background: var(--surface-2); border: 1px solid transparent; border-radius: var(--r-lg); padding: var(--sp-2); min-height: 140px; display: flex; flex-direction: column; gap: var(--sp-2); transition: background-color var(--dur-hover) ease, border-color var(--dur-hover) ease; }
.column.over { background: var(--surface-3); border-color: var(--ink); }
.column header { display: flex; justify-content: space-between; align-items: baseline; font-weight: 600; font-size: var(--fs-md); text-transform: capitalize; padding: 2px 4px; }
.app { display: flex; flex-direction: column; align-items: stretch; gap: 2px; text-align: left; width: 100%; background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-md); padding: var(--sp-2) var(--sp-3); cursor: grab; color: inherit; font-size: var(--fs-md); transition: box-shadow var(--dur-hover) var(--ease-out), transform var(--dur-hover) var(--ease-out), border-color var(--dur-hover) ease; }
.app:active { cursor: grabbing; }
.app.lifting { box-shadow: var(--shadow-2); transform: rotate(1.5deg) scale(1.02); }
@media (hover: hover) and (pointer: fine) { .app:hover { border-color: var(--line-2); box-shadow: var(--shadow-1); } }
.company { font-weight: 500; }
.next { color: var(--ink-2); margin-top: 2px; }
.next.soon { color: var(--warn); font-weight: 500; }
.app-form { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.wide { grid-column: 1 / -1; }
.actions { display: flex; gap: var(--sp-2); align-items: center; }
.push { margin-left: auto; }
@media (prefers-reduced-motion: reduce) { .app.lifting { transform: none; } }
</style>
