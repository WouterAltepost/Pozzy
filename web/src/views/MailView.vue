<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { PhArrowsClockwise, PhFunnelSimple, PhMagnifyingGlass, PhTray } from '@phosphor-icons/vue'
import EmailDetail from '../components/mail/EmailDetail.vue'
import EmailRow from '../components/mail/EmailRow.vue'
import MailFilters from '../components/mail/MailFilters.vue'
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import UiModal from '../components/ui/UiModal.vue'
import UiSegmented from '../components/ui/UiSegmented.vue'
import { useReady } from '../composables/useReady'
import { useMediaQuery } from '../composables/useMediaQuery'
import { accountName } from '../lib/mail'
import { useAreasStore } from '../stores/areas'
import { useMailStore } from '../stores/mail'

const store = useMailStore()
const areas = useAreasStore()
const route = useRoute()
const error = ref('')
const notice = ref('')
const busy = ref(false)
const ready = useReady(() => Promise.all([store.load(), store.loadAccounts(), areas.load()]))
// Below 1024px this is the iOS app: large title, bar buttons, grouped list, filter sheet.
const phone = useMediaQuery('(max-width: 1023px)')
const filtersOpen = ref(false)
const PAGE = 40
const shown = ref(PAGE)
const visibleItems = computed(() => (phone.value ? store.items.slice(0, shown.value) : store.items))
// The handled mode is the segmented control on the phone, so the badge counts the rest.
const activeFilters = computed(() => ['account_id', 'category', 'area_id', 'priority', 'needs_reply'].filter((k) => store.filters[k]).length)
const MODES = [
  { value: '0', label: 'Inbox' },
  { value: '1', label: 'Handled' },
  { value: 'all', label: 'All' },
]
const mode = computed({
  get: () => store.filters.handled,
  set: (v) => {
    store.filters.handled = v
    shown.value = PAGE
    store.load()
  },
})

const pending = ref('') // which detail action is in flight: update | task | reclassify
async function run(fn, name = '') {
  error.value = ''
  busy.value = true
  pending.value = name
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
    pending.value = ''
  }
}

function open(email) {
  run(() => store.open(email.id))
}

function setHandled(email, handled) {
  run(() => store.markHandled(email.id, handled))
}

function update(body) {
  if (!store.selected) return
  run(() => store.update(store.selected.id, body), 'update')
}

function createTask(body) {
  if (!store.selected) return
  run(async () => {
    const result = await store.createTask(store.selected.id, body)
    notice.value = result.created ? `Task "${result.task.title}" created.` : 'A task already existed for this email.'
  }, 'task')
}

// The swipe and the context menu make a task straight from the list, without a due date.
function taskFromRow(email) {
  notice.value = ''
  run(async () => {
    const result = await store.createTask(email.id, {})
    notice.value = result.created ? `Task "${result.task.title}" created.` : 'A task already existed for this email.'
  })
}

function reclassify() {
  if (!store.selected) return
  run(() => store.reclassify(store.selected.id), 'reclassify')
}

function sync() {
  notice.value = ''
  run(async () => {
    const result = await store.sync()
    const inserted = result.accounts.reduce((n, a) => n + (a.inserted || 0), 0)
    const failed = result.accounts.filter((a) => a.error).map((a) => a.label)
    notice.value = `Synced: ${inserted} new, ${result.classified.classified} classified (${result.classified.by}).` + (failed.length ? ` Failed: ${failed.join(', ')}.` : '')
  })
}

// Pull to refresh reloads what is stored; it never syncs (that is the bar button).
function refresh() {
  return Promise.all([store.load(), store.loadAccounts()])
}
</script>

<template>
  <component :is="phone ? PullToRefresh : 'div'" :action="phone ? refresh : undefined">
  <div class="mail">
    <Teleport v-if="phone && route.name === 'mail'" defer to="#nav-trailing">
      <button type="button" class="icon-btn" :class="{ lit: activeFilters }" :aria-label="activeFilters ? `Filters, ${activeFilters} on` : 'Filters'" @click="filtersOpen = true"><PhFunnelSimple :weight="activeFilters ? 'fill' : 'regular'" /></button>
      <button type="button" class="icon-btn" aria-label="Sync now" :disabled="store.syncing" @click="sync"><PhArrowsClockwise weight="regular" :class="{ turning: store.syncing }" /></button>
    </Teleport>
    <PageHeader v-if="!phone" title="Mail">
      <template #meta><span class="num">{{ store.counts.unhandled }} unhandled, {{ store.counts.needs_reply }} need a reply</span></template>
      <UiButton :loading="store.syncing" @click="sync">Sync now</UiButton>
      <RouterLink :to="{ name: 'settings' }" class="link-btn">Accounts</RouterLink>
    </PageHeader>
    <template v-else>
      <header class="phead">
        <h1>Mail</h1>
        <p class="sub num">{{ store.syncing ? 'Checking for mail…' : `${store.counts.unhandled} unhandled, ${store.counts.needs_reply} need a reply` }}</p>
      </header>
      <label class="psearch">
        <PhMagnifyingGlass class="glass" weight="bold" aria-hidden="true" />
        <input v-model="store.filters.q" type="search" enterkeyhint="search" placeholder="Search" aria-label="Search mail" @change="store.load()" />
      </label>
      <UiSegmented v-model="mode" :options="MODES" class="pmode" />
      <p v-if="activeFilters" class="pfiltered">
        <span>{{ activeFilters }} {{ activeFilters === 1 ? 'filter' : 'filters' }} on</span>
        <button type="button" class="link-btn" @click="store.resetFilters()">Clear</button>
      </p>
    </template>
    <MailFilters v-if="!phone" :filters="store.filters" :accounts="store.accounts" @change="store.load()" @reset="store.resetFilters()" />
    <p v-if="error || store.error" class="error notice">{{ error || store.error }}</p>
    <p v-if="notice" class="muted small notice">{{ notice }}</p>

    <UiLoadGate :ready="ready" label="Loading mail">
      <ul class="list" :class="{ plate: phone }">
        <li v-if="!store.items.length">
          <UiEmpty title="No emails match" :hint="store.accounts.length ? 'Change the filters or sync.' : 'No mail accounts are configured (MAIL_ACCOUNTS_JSON).'">
            <template #icon><PhTray /></template>
          </UiEmpty>
        </li>
        <EmailRow
          v-for="e in visibleItems"
          :key="e.id"
          :email="e"
          :ios="phone"
          :active="e.id === store.selected?.id"
          @open="open"
          @handled="setHandled"
          @task="taskFromRow"
        />
        <li v-if="phone && store.items.length > shown" class="more"><button type="button" class="more-btn pressable" @click="shown += PAGE">Show {{ Math.min(PAGE, store.items.length - shown) }} more <span class="num">({{ store.items.length - shown }} left)</span></button></li>
      </ul>
    </UiLoadGate>

    <UiModal v-if="phone" :open="filtersOpen" title="Filters" size="sm" @close="filtersOpen = false">
      <MailFilters ios :filters="store.filters" :accounts="store.accounts" @change="store.load()" @reset="store.resetFilters()" />
    </UiModal>

    <UiModal :open="Boolean(store.selected)" :title="phone && store.selected ? store.selected.account?.label || accountName(store.selected.account) : ''" size="lg" @close="store.close()">
      <EmailDetail v-if="store.selected" :email="store.selected" :ios="phone" :busy="busy" :pending="pending" @close="store.close()" @update="update" @task="createTask" @reclassify="reclassify" />
    </UiModal>
  </div>
  </component>
</template>

<style scoped>
.notice { margin-top: var(--sp-3); }
.more { padding-top: var(--sp-2); }
.list { display: flex; flex-direction: column; gap: var(--sp-2); min-width: 0; margin-top: var(--sp-4); }

/* iOS: large title with a footnote under it, a filled search field, the mode as a segmented
   control and the messages as one inset grouped plate. */
@media (max-width: 1023px) {
  .phead { margin: 4px 0 var(--sp-3); }
  .sub { margin-top: 2px; font-size: var(--fs-sm); color: var(--ink-3); }
  .psearch { position: relative; display: block; }
  .psearch .glass { position: absolute; left: 8px; top: 50%; width: 17px; height: 17px; margin-top: -8.5px; color: var(--ink-3); pointer-events: none; }
  .psearch input { width: 100%; height: 36px; padding: 0 8px 0 31px; border-radius: var(--r-md); }
  .pmode { margin-top: var(--sp-3); }
  .pmode { display: flex; width: 100%; }
  .pmode :deep(.seg-item) { flex: 1; }
  .pfiltered { display: flex; align-items: baseline; gap: var(--sp-2); margin-top: var(--sp-2); padding: 0 4px; font-size: var(--fs-sm); color: var(--ink-3); }
  .pfiltered .link-btn { font-size: var(--fs-sm); }
  .list.plate { gap: 0; margin-top: var(--sp-4); background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .list.plate .more { position: relative; padding: 0; }
  .list.plate .more::before { content: ''; position: absolute; top: 0; left: 28px; right: 0; height: 0.5px; background: var(--line); }
  .more-btn { display: flex; align-items: center; justify-content: center; gap: 4px; width: 100%; min-height: 44px; border: 0; border-radius: 0; background: none; box-shadow: none; color: var(--brand); font: inherit; font-size: 1.0625rem; }
  .more-btn .num { color: var(--ink-3); font-size: var(--fs-md); }
  .icon-btn.lit { color: var(--brand); }
  .icon-btn:disabled { opacity: 1; }
  .turning { animation: turning 0.9s linear infinite; }
  @keyframes turning { to { transform: rotate(360deg); } }
}
@media (max-width: 1023px) and (prefers-reduced-motion: reduce) { .turning { animation: none; opacity: 0.4; } }
</style>
