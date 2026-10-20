<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { PhBriefcase, PhCalendarPlus, PhCaretRight, PhGraduationCap, PhPlus, PhTrash, PhX } from '@phosphor-icons/vue'
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import SwipeRow from '../components/ios/SwipeRow.vue'
import UiConfirm from '../components/ui/UiConfirm.vue'
import UiSegmented from '../components/ui/UiSegmented.vue'
import { useContextMenu } from '../composables/useContextMenu'
import { tick } from '../lib/haptics'
import PageHeader from '../components/ui/PageHeader.vue'
import UiBadge from '../components/ui/UiBadge.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiField from '../components/ui/UiField.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import UiModal from '../components/ui/UiModal.vue'
import { useReady } from '../composables/useReady'
import { useMediaQuery } from '../composables/useMediaQuery'
import { daysUntil, formatDateTime, formatDay, formatTime } from '../lib/dates'
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
const route = useRoute()
const menu = useContextMenu()

// Phone: one + in the navigation bar opens a menu of the three things that can be added.
function openAdd(event) {
  menu.open(event.currentTarget, [
    { label: 'New deadline', icon: PhCalendarPlus, action: () => (adding.value = 'deadline') },
    { label: 'New course', icon: PhGraduationCap, action: () => (adding.value = 'course') },
    { label: 'New application', icon: PhBriefcase, action: () => (adding.value = 'application') },
  ])
}

// Every delete asks first through UiConfirm (an action sheet on the phone).
const confirm = ref(null) // { title, message, label, action }
function confirmed() {
  const c = confirm.value
  confirm.value = null
  if (c) {
    tick()
    c.action()
  }
}
function askDeadline(d) {
  confirm.value = { title: `Delete "${d.title}"?`, message: '', label: 'Delete deadline', action: () => run(() => store.removeDeadline(d.id)) }
}

// Phone: the kanban becomes a status filter over one list. It opens on the first status that
// has applications.
const appStatus = ref('')
const statusOptions = APPLICATION_STATUSES.map((s) => ({ value: s, label: s[0].toUpperCase() + s.slice(1) }))
watch(
  () => store.applications.length,
  () => {
    if (!appStatus.value || !store.applicationsByStatus(appStatus.value).length) appStatus.value = APPLICATION_STATUSES.find((s) => store.applicationsByStatus(s).length) || appStatus.value || 'found'
  },
  { immediate: true },
)
const appsShown = computed(() => store.applicationsByStatus(appStatus.value))
function toggleDone() {
  store.includeDoneDeadlines = !store.includeDoneDeadlines
  store.load()
}
function toggleFinished() {
  store.includeClosedCourses = !store.includeClosedCourses
  store.load()
}
function courseMeta(c) {
  const n = c.deadlines?.length || 0
  return [c.code, c.period, c.ects ? `${c.ects} ECTS` : null, `${n} deadline${n === 1 ? '' : 's'}`].filter(Boolean).join(', ')
}
function soon(day) {
  const d = daysUntil(day)
  return d !== null && d <= 2
}

async function run(fn) {
  error.value = ''
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  }
}

function setDeadlineDone(d) {
  tick()
  run(() => store.updateDeadline(d.id, { done: !d.done }))
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
  confirm.value = { title: `Delete course "${c.name}"?`, message: 'Its deadlines are deleted too.', label: 'Delete course', action: () => run(() => store.removeCourse(c.id)) }
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
    // The phone has no kanban to drag between, so its editor also carries the status.
    await store.updateApplication(a.id, { company: a.company, role: a.role || null, next_step: a.next_step || null, next_step_date: a.next_step_date || null, notes: a.notes || null, link: a.link || null, applied_at: a.applied_at || null, ...(phone.value ? { status: a.status } : {}) })
    editingApp.value = null
  })
}

function removeApp(a) {
  confirm.value = { title: `Delete application at ${a.company}?`, message: '', label: 'Delete application', action: () => run(() => store.removeApplication(a.id)) }
}
</script>

<template>
  <PullToRefresh :action="() => store.load()">
  <div class="study">
    <PageHeader v-if="!phone" title="Study" />
    <div v-else class="phead"><h1>Study</h1><span class="psub num">{{ store.deadlines.filter((d) => !d.done).length }} open deadlines, {{ store.applications.length }} applications</span></div>
    <Teleport v-if="phone && route.name === 'study'" defer to="#nav-trailing">
      <button type="button" class="icon-btn" aria-label="Add" @click="openAdd"><PhPlus weight="regular" /></button>
    </Teleport>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading study">

    <template v-if="phone">
      <section class="grp">
        <div class="ghead"><h2>Deadlines</h2><button type="button" class="hlink" @click="toggleDone">{{ store.includeDoneDeadlines ? 'Hide done' : 'Show done' }}</button></div>
        <ul v-if="store.deadlines.length" class="plate">
          <li v-for="d in store.deadlines" :key="d.id">
            <SwipeRow :trailing="[{ label: 'Delete', icon: PhTrash, color: 'var(--danger)', action: () => askDeadline(d) }]">
              <div class="row dl" :class="{ done: d.done }">
                <input type="checkbox" :checked="d.done" :aria-label="d.title" @change="setDeadlineDone(d)" />
                <span class="txt">
                  <span class="t">{{ d.title }}</span>
                  <span class="s">{{ d.course_code || d.course_name }}, {{ d.type }}<template v-if="d.task_id">, <RouterLink :to="{ name: 'tasks' }">task</RouterLink></template></span>
                </span>
                <span class="due num" :class="d.done ? '' : dueTone(d.due_at.slice(0, 10))"><span>{{ formatDay(d.due_at.slice(0, 10)) }}</span><span class="dt">{{ formatTime(d.due_at) }}</span></span>
              </div>
            </SwipeRow>
          </li>
        </ul>
        <p v-else class="plate row empty">No deadlines</p>
      </section>

      <section class="grp">
        <div class="ghead"><h2>Courses</h2><button type="button" class="hlink" @click="toggleFinished">{{ store.includeClosedCourses ? 'Hide finished' : 'Show finished' }}</button></div>
        <ul v-if="store.courses.length" class="plate">
          <li v-for="c in store.courses" :key="c.id">
            <SwipeRow :trailing="[{ label: 'Delete', icon: PhTrash, color: 'var(--danger)', action: () => removeCourse(c) }]">
              <div class="row">
                <span class="txt"><span class="t">{{ c.name }}</span><span class="s num">{{ courseMeta(c) }}</span></span>
                <select :value="c.status" class="pick status" :aria-label="'Status of ' + c.name" @change="tick(); run(() => store.updateCourse(c.id, { status: $event.target.value }))">
                  <option v-for="st in ['planned', 'active', 'passed', 'failed', 'dropped']" :key="st" :value="st">{{ st[0].toUpperCase() + st.slice(1) }}</option>
                </select>
              </div>
            </SwipeRow>
          </li>
        </ul>
        <template v-else>
          <p class="plate row empty">No courses yet</p>
          <p class="foot">Add a course with + to attach deadlines to it.</p>
        </template>
      </section>

      <section class="grp">
        <div class="ghead"><h2>Internship applications</h2></div>
        <div class="seg-full"><UiSegmented v-model="appStatus" :options="statusOptions" /></div>
        <ul v-if="appsShown.length" class="plate">
          <li v-for="a in appsShown" :key="a.id">
            <button type="button" class="row app-row pressable" @click="editingApp = { ...a }">
              <span class="txt">
                <span class="t">{{ a.company }}</span>
                <span v-if="a.role" class="s">{{ a.role }}</span>
                <span v-if="a.next_step" class="s next-p" :class="{ soon: soon(a.next_step_date) }">{{ a.next_step }}<span v-if="a.next_step_date">, {{ formatDay(a.next_step_date) }}</span></span>
              </span>
              <PhCaretRight class="chev" weight="bold" aria-hidden="true" />
            </button>
          </li>
        </ul>
        <p v-else class="plate row empty">{{ store.applications.length ? 'Nothing in ' + appStatus : 'No applications yet' }}</p>
      </section>
    </template>

    <template v-else>

    <section class="card">
      <div class="card-head">
        <h2>Deadlines</h2>
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
      <form class="inline" @submit.prevent="addDeadline">
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
      <form class="inline" @submit.prevent="addCourse">
        <UiField label="Course name" class="grow"><input v-model="courseForm.name" type="text" required /></UiField>
        <UiField label="Code"><input v-model="courseForm.code" type="text" class="short" /></UiField>
        <UiField label="Period"><input v-model="courseForm.period" type="text" class="short" /></UiField>
        <UiField label="ECTS"><input v-model.number="courseForm.ects" type="number" min="0" step="0.5" class="short" /></UiField>
        <UiButton type="submit" variant="primary">Add course</UiButton>
      </form>
    </section>

    <section class="card">
      <div class="card-head"><h2>Internship applications</h2></div>
      <form class="inline" @submit.prevent="addApplication">
        <UiField label="Company" class="grow"><input v-model="appForm.company" type="text" required /></UiField>
        <UiField label="Role" class="grow"><input v-model="appForm.role" type="text" /></UiField>
        <UiField label="Link" class="grow"><input v-model="appForm.link" type="url" placeholder="https://" /></UiField>
        <UiButton type="submit" variant="primary">Add</UiButton>
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
    </template>

    </UiLoadGate>

    <UiModal :open="adding === 'deadline'" title="New deadline" size="sm" @close="adding = null">
      <form class="sheet-form" @submit.prevent="addDeadline">
        <div class="plate">
          <label class="row"><input v-model="deadlineForm.title" type="text" required placeholder="Title" aria-label="Title" class="bare" /></label>
          <label class="row"><span class="lbl">Course</span><select v-model="deadlineForm.course_id" required class="pick"><option value="" disabled>Choose</option><option v-for="c in store.courses" :key="c.id" :value="c.id">{{ c.code || c.name }}</option></select></label>
          <label class="row"><span class="lbl">Type</span><select v-model="deadlineForm.type" class="pick"><option value="assignment">assignment</option><option value="exam">exam</option><option value="presentation">presentation</option><option value="other">other</option></select></label>
        </div>
        <div class="plate">
          <label class="row"><span class="lbl">Due</span><input v-model="deadlineForm.due_date" type="date" required class="pill" /></label>
          <label class="row"><span class="lbl">Time</span><input v-model="deadlineForm.due_time" type="time" class="pill" /></label>
        </div>
        <p v-if="!store.courses.length" class="foot">Add a course first.</p>
        <UiButton type="submit" variant="primary" block class="big" :disabled="!store.courses.length">Add deadline</UiButton>
      </form>
    </UiModal>
    <UiModal :open="adding === 'course'" title="New course" size="sm" @close="adding = null">
      <form class="sheet-form" @submit.prevent="addCourse">
        <div class="plate">
          <label class="row"><input v-model="courseForm.name" type="text" required placeholder="Course name" aria-label="Course name" class="bare" /></label>
          <label class="row"><span class="lbl">Code</span><input v-model="courseForm.code" type="text" placeholder="Optional" class="side" /></label>
          <label class="row"><span class="lbl">Period</span><input v-model="courseForm.period" type="text" placeholder="Optional" class="side" /></label>
          <label class="row"><span class="lbl">ECTS</span><input v-model.number="courseForm.ects" type="number" min="0" step="0.5" class="pill num" /></label>
        </div>
        <UiButton type="submit" variant="primary" block class="big">Add course</UiButton>
      </form>
    </UiModal>
    <UiModal :open="adding === 'application'" title="New application" size="sm" @close="adding = null">
      <form class="sheet-form" @submit.prevent="addApplication">
        <div class="plate">
          <label class="row"><input v-model="appForm.company" type="text" required placeholder="Company" aria-label="Company" class="bare" /></label>
          <label class="row"><input v-model="appForm.role" type="text" placeholder="Role" aria-label="Role" class="bare" /></label>
          <label class="row"><input v-model="appForm.link" type="url" placeholder="Link" aria-label="Link" class="bare" /></label>
        </div>
        <UiButton type="submit" variant="primary" block class="big">Add application</UiButton>
      </form>
    </UiModal>

    <UiModal :open="Boolean(editingApp)" :title="editingApp?.company || 'Application'" size="md" @close="editingApp = null">
      <form v-if="editingApp && phone" class="sheet-form" @submit.prevent="saveApp">
        <div class="plate">
          <label class="row"><input v-model="editingApp.company" type="text" required placeholder="Company" aria-label="Company" class="bare" /></label>
          <label class="row"><input v-model="editingApp.role" type="text" placeholder="Role" aria-label="Role" class="bare" /></label>
          <label class="row"><input v-model="editingApp.link" type="url" placeholder="Link" aria-label="Link" class="bare" /></label>
        </div>
        <div class="plate">
          <label class="row"><span class="lbl">Status</span><select v-model="editingApp.status" class="pick"><option v-for="st in statusOptions" :key="st.value" :value="st.value">{{ st.label }}</option></select></label>
          <label class="row"><span class="lbl">Applied on</span><input v-model="editingApp.applied_at" type="date" class="pill" /></label>
        </div>
        <div class="plate">
          <label class="row"><input v-model="editingApp.next_step" type="text" placeholder="Next step" aria-label="Next step" class="bare" /></label>
          <label class="row"><span class="lbl">Date</span><input v-model="editingApp.next_step_date" type="date" class="pill" /></label>
        </div>
        <div class="plate"><textarea v-model="editingApp.notes" rows="3" placeholder="Notes" aria-label="Notes" class="bare-area"></textarea></div>
        <UiButton type="submit" variant="primary" block class="big">Save</UiButton>
        <div class="plate">
          <a v-if="editingApp.link" :href="editingApp.link" target="_blank" rel="noopener" class="row act">Open link</a>
          <button type="button" class="row act danger" @click="removeApp(editingApp); editingApp = null">Delete application</button>
        </div>
      </form>
      <form v-else-if="editingApp" class="app-form" @submit.prevent="saveApp">
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
    <UiConfirm :open="Boolean(confirm)" :title="confirm?.title" :message="confirm?.message" :confirm-label="confirm?.label" danger @confirm="confirmed" @cancel="confirm = null" />
  </div>
  </PullToRefresh>
</template>

<style scoped>
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

/* iOS layer (phone layout, under 700px). Inset grouped plates of 44pt rows with separators
   from the text, footnote headers with a tint action on the right, swipe to delete, and the
   kanban as a status filter over one list. Sheets read as grouped form rows. */
@media (max-width: 699px) {
  .phead { margin: 4px 0 var(--sp-5); }
  .psub { display: block; margin-top: 2px; font-size: 0.9375rem; color: var(--ink-3); }
  .grp { margin-bottom: var(--sp-8); }
  .ghead { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 0 16px 6px; }
  .ghead h2 { font-size: 0.8125rem; font-weight: 400; text-transform: uppercase; color: var(--ink-3); }
  .hlink { border: 0; background: none; padding: 0; color: var(--brand); font: inherit; font-size: 0.9375rem; }
  .plate { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .plate > li, .plate > .row { position: relative; }
  .plate > li + li::before, .plate > .row + .row::before { content: ''; position: absolute; z-index: 2; top: 0; left: var(--sep, 16px); right: 0; height: 0.5px; background: var(--line-2); }
  .plate:has(.dl) { --sep: 50px; }
  .row { display: flex; align-items: center; gap: 12px; width: 100%; min-height: 44px; padding: 6px 16px; border: 0; background: none; font: inherit; font-size: 1.0625rem; color: var(--ink); text-align: left; text-decoration: none; }
  .row.empty { margin: 0; color: var(--ink-3); }
  .lbl { flex: 1; min-width: 0; }
  .foot { margin: 6px 16px 0; font-size: 0.8125rem; line-height: 1.4; color: var(--ink-3); }
  .txt { flex: 1; min-width: 0; display: flex; flex-direction: column; padding: 4px 0; }
  .txt .t { font-size: 1.0625rem; }
  .txt .s { font-size: 0.9375rem; color: var(--ink-3); }
  .dl.done .t { color: var(--ink-3); }
  .due { flex: none; display: flex; flex-direction: column; align-items: flex-end; font-size: 0.9375rem; color: var(--ink-3); }
  .due .dt { font-size: 0.8125rem; }
  .due.warn { color: var(--warn); }
  .due.danger { color: var(--danger); }
  .chev { flex: none; width: 14px; height: 14px; color: var(--ink-4); }
  .next-p.soon { color: var(--warn); }
  .app-row { min-height: 60px; }
  .seg-full { margin-bottom: var(--sp-3); }
  .grp .seg-full :deep(.seg) { display: flex; width: 100%; }
  .grp .seg-full :deep(.seg-item) { flex: 1; padding-left: 0; padding-right: 0; }
  .pick { flex: none; width: auto; max-width: 50%; height: 32px; padding: 0 20px 0 0; background: transparent url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256' fill='none' stroke='%238E8E93' stroke-width='22' stroke-linecap='round' stroke-linejoin='round'><polyline points='80 96 128 48 176 96'/><polyline points='80 160 128 208 176 160'/></svg>") right center / 13px no-repeat; color: var(--ink-3); text-align: right; text-align-last: right; }
  .pick:focus-visible { box-shadow: none; color: var(--ink); }
  .pick.status { max-width: 96px; }
  .row .pill { flex: none; width: auto; min-width: 64px; max-width: 160px; height: 34px; padding: 0 10px; border-radius: 8px; text-align: center; }
  .row .bare, .row .side { flex: 1; width: 100%; height: 32px; padding: 0; background: transparent; border-radius: 0; }
  .row .side { text-align: right; color: var(--ink-3); }
  .row .bare:focus-visible, .row .side:focus-visible, .bare-area:focus-visible { box-shadow: none; }
  .bare-area { display: block; width: 100%; padding: 11px 16px; background: transparent; border-radius: 0; resize: none; }
  .act { color: var(--brand); }
  .act.danger { color: var(--danger); }
  .act:active { background: var(--surface-3); }
  .sheet-form { display: flex; flex-direction: column; gap: var(--sp-5); }
  .sheet-form .plate { background: var(--surface-2); }
  .sheet-form .plate .pill { background: var(--surface-3); }
  .sheet-form .big { height: 50px; min-height: 50px; border-radius: 12px; font-size: 1.0625rem; }
  .sheet-form .foot { margin-top: calc(var(--sp-3) * -1); }
}
</style>
