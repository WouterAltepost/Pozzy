<script setup>
import { onMounted, reactive, ref } from 'vue'
import { daysUntil, formatDateTime, formatDay } from '../lib/dates'
import { APPLICATION_STATUSES, useStudyStore } from '../stores/study'

const store = useStudyStore()
const error = ref('')
const courseForm = reactive({ name: '', code: '', period: '', ects: null })
const deadlineForm = reactive({ course_id: '', title: '', due_date: '', due_time: '23:59', type: 'assignment' })
const appForm = reactive({ company: '', role: '', link: '' })
const editingApp = ref(null)
const dragOver = ref(null)

onMounted(() => store.load())

async function run(fn) {
  error.value = ''
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  }
}

function addCourse() {
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
  if (!deadlineForm.course_id || !deadlineForm.title.trim() || !deadlineForm.due_date) return
  const due = new Date(`${deadlineForm.due_date}T${deadlineForm.due_time || '23:59'}`)
  run(async () => {
    await store.createDeadline({ course_id: deadlineForm.course_id, title: deadlineForm.title, due_at: due.toISOString(), type: deadlineForm.type })
    Object.assign(deadlineForm, { title: '', due_date: '' })
  })
}

function dueClass(d) {
  const days = daysUntil(d.due_at.slice(0, 10))
  if (days < 0) return 'overdue'
  if (days <= 3) return 'soon'
  return ''
}

function addApplication() {
  if (!appForm.company.trim()) return
  run(async () => {
    await store.createApplication({ company: appForm.company, role: appForm.role || null, link: appForm.link || null })
    Object.assign(appForm, { company: '', role: '', link: '' })
  })
}

function onDragStart(a, event) {
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
    <h1>Study</h1>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>

    <section class="card">
      <div class="row head">
        <h2>Deadlines</h2>
        <label class="check"><input v-model="store.includeDoneDeadlines" type="checkbox" @change="store.load()" /> show done</label>
      </div>
      <ul class="deadlines">
        <li v-if="!store.deadlines.length" class="muted">No deadlines.</li>
        <li v-for="d in store.deadlines" :key="d.id" :class="{ done: d.done }">
          <input type="checkbox" :checked="d.done" @change="run(() => store.updateDeadline(d.id, { done: !d.done }))" />
          <span class="course">{{ d.course_code || d.course_name }}</span>
          <span class="title">{{ d.title }} <span class="muted small">{{ d.type }}</span></span>
          <span :class="dueClass(d)">{{ formatDateTime(d.due_at) }}</span>
          <RouterLink v-if="d.task_id" :to="{ name: 'tasks' }" class="muted small">task</RouterLink>
          <button type="button" class="x" @click="run(() => store.removeDeadline(d.id))">&times;</button>
        </li>
      </ul>
      <form class="inline" @submit.prevent="addDeadline">
        <select v-model="deadlineForm.course_id" required>
          <option value="" disabled>course</option>
          <option v-for="c in store.courses" :key="c.id" :value="c.id">{{ c.code || c.name }}</option>
        </select>
        <input v-model="deadlineForm.title" type="text" placeholder="Deadline title" required />
        <input v-model="deadlineForm.due_date" type="date" required />
        <input v-model="deadlineForm.due_time" type="time" />
        <select v-model="deadlineForm.type">
          <option value="assignment">assignment</option>
          <option value="exam">exam</option>
          <option value="presentation">presentation</option>
          <option value="other">other</option>
        </select>
        <button type="submit" :disabled="!store.courses.length">Add deadline</button>
        <span v-if="!store.courses.length" class="muted small">Add a course first.</span>
      </form>
    </section>

    <section class="card">
      <div class="row head">
        <h2>Courses</h2>
        <label class="check"><input v-model="store.includeClosedCourses" type="checkbox" @change="store.load()" /> show finished</label>
      </div>
      <table class="courses">
        <thead><tr><th>Code</th><th>Name</th><th>Period</th><th>ECTS</th><th>Status</th><th></th></tr></thead>
        <tbody>
          <tr v-for="c in store.courses" :key="c.id">
            <td>{{ c.code }}</td>
            <td>{{ c.name }} <span class="muted small">{{ c.deadlines?.length || 0 }} deadlines</span></td>
            <td>{{ c.period }}</td>
            <td>{{ c.ects }}</td>
            <td>
              <select :value="c.status" @change="run(() => store.updateCourse(c.id, { status: $event.target.value }))">
                <option v-for="s in ['planned', 'active', 'passed', 'failed', 'dropped']" :key="s" :value="s">{{ s }}</option>
              </select>
            </td>
            <td><button type="button" class="x" @click="removeCourse(c)">&times;</button></td>
          </tr>
        </tbody>
      </table>
      <form class="inline" @submit.prevent="addCourse">
        <input v-model="courseForm.name" type="text" placeholder="Course name" required />
        <input v-model="courseForm.code" type="text" placeholder="code" class="short" />
        <input v-model="courseForm.period" type="text" placeholder="period" class="short" />
        <input v-model.number="courseForm.ects" type="number" min="0" step="0.5" placeholder="ECTS" class="short" />
        <button type="submit">Add course</button>
      </form>
    </section>

    <section class="card">
      <h2>Internship applications</h2>
      <form class="inline" @submit.prevent="addApplication">
        <input v-model="appForm.company" type="text" placeholder="Company" required />
        <input v-model="appForm.role" type="text" placeholder="Role" />
        <input v-model="appForm.link" type="url" placeholder="https://" />
        <button type="submit">Add</button>
      </form>
      <div class="kanban">
        <div
          v-for="status in APPLICATION_STATUSES"
          :key="status"
          class="column"
          :class="{ over: dragOver === status }"
          @dragover.prevent="dragOver = status"
          @dragleave="dragOver = null"
          @drop.prevent="onDrop(status, $event)"
        >
          <header>{{ status }} <span class="muted">{{ store.applicationsByStatus(status).length }}</span></header>
          <div v-for="a in store.applicationsByStatus(status)" :key="a.id" class="app" draggable="true" @dragstart="onDragStart(a, $event)" @click="editingApp = { ...a }">
            <strong>{{ a.company }}</strong>
            <div class="muted small">{{ a.role }}</div>
            <div v-if="a.next_step" class="small next" :class="{ soon: daysUntil(a.next_step_date) !== null && daysUntil(a.next_step_date) <= 2 }">
              {{ a.next_step }}<span v-if="a.next_step_date">, {{ formatDay(a.next_step_date) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="editingApp" class="app-edit">
        <h3>{{ editingApp.company }}</h3>
        <form @submit.prevent="saveApp">
          <label>Company <input v-model="editingApp.company" type="text" required /></label>
          <label>Role <input v-model="editingApp.role" type="text" /></label>
          <label>Link <input v-model="editingApp.link" type="url" /></label>
          <label>Applied on <input v-model="editingApp.applied_at" type="date" /></label>
          <label>Next step <input v-model="editingApp.next_step" type="text" /></label>
          <label>Next step date <input v-model="editingApp.next_step_date" type="date" /></label>
          <label class="wide">Notes <textarea v-model="editingApp.notes" rows="3"></textarea></label>
          <div class="actions wide">
            <button type="submit">Save</button>
            <button type="button" @click="editingApp = null">Cancel</button>
            <a v-if="editingApp.link" :href="editingApp.link" target="_blank" rel="noopener">open link</a>
            <button type="button" class="danger" @click="removeApp(editingApp); editingApp = null">Delete</button>
          </div>
        </form>
      </div>
    </section>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; }
h2 { font-size: 1rem; margin: 0 0 0.5rem; }
h3 { font-size: 0.95rem; margin: 0 0 0.4rem; }
.row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.check { display: flex; align-items: center; gap: 0.3rem; font-size: 0.85rem; }
.small { font-size: 0.78rem; }
ul { list-style: none; padding: 0; margin: 0 0 0.5rem; }
.deadlines li { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0; font-size: 0.9rem; }
.deadlines li.done .title { text-decoration: line-through; color: #9ca3af; }
.course { background: #e0e7ff; color: #3730a3; padding: 0 0.35rem; border-radius: 3px; font-size: 0.78rem; }
.title { flex: 1; }
.overdue { color: #b91c1c; font-weight: 600; }
.soon { color: #d97706; font-weight: 600; }
.x { border: none; background: none; color: #9ca3af; font-size: 1.1rem; }
.inline { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; margin-top: 0.5rem; }
.inline input, .inline select { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.inline .short { width: 90px; }
.courses { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.courses th { text-align: left; font-weight: 500; color: #6b7280; padding: 0.2rem 0.4rem; }
.courses td { padding: 0.25rem 0.4rem; border-top: 1px solid #f3f4f6; }
.kanban { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin-top: 0.75rem; }
@media (min-width: 900px) { .kanban { grid-template-columns: repeat(5, 1fr); } }
.column { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 0.4rem; min-height: 120px; }
.column.over { border-color: #2563eb; background: #eff6ff; }
.column header { font-weight: 600; text-transform: capitalize; font-size: 0.85rem; margin-bottom: 0.3rem; display: flex; justify-content: space-between; }
.app { background: #fff; border: 1px solid #e5e7eb; border-radius: 4px; padding: 0.4rem 0.5rem; margin-bottom: 0.3rem; cursor: grab; font-size: 0.85rem; }
.next { color: #374151; margin-top: 0.2rem; }
.next.soon { color: #d97706; font-weight: 600; }
.app-edit { border-top: 1px solid #e5e7eb; margin-top: 0.75rem; padding-top: 0.75rem; }
.app-edit form { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.app-edit label { display: flex; flex-direction: column; gap: 0.2rem; font-size: 0.82rem; color: #4b5563; }
.app-edit input, .app-edit textarea { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.wide { grid-column: 1 / -1; }
.actions { display: flex; gap: 0.5rem; align-items: center; }
.danger { color: #b91c1c; margin-left: auto; }
</style>
