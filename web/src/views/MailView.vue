<script setup>
import { computed, ref } from 'vue'
import { PhTray } from '@phosphor-icons/vue'
import EmailDetail from '../components/mail/EmailDetail.vue'
import EmailRow from '../components/mail/EmailRow.vue'
import MailFilters from '../components/mail/MailFilters.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import UiModal from '../components/ui/UiModal.vue'
import { useReady } from '../composables/useReady'
import { useMediaQuery } from '../composables/useMediaQuery'
import { PhFunnelSimple } from '@phosphor-icons/vue'
import { useAreasStore } from '../stores/areas'
import { useMailStore } from '../stores/mail'

const store = useMailStore()
const areas = useAreasStore()
const error = ref('')
const notice = ref('')
const busy = ref(false)
const ready = useReady(() => Promise.all([store.load(), store.loadAccounts(), areas.load()]))
const phone = useMediaQuery('(max-width: 699px)')
const filtersOpen = ref(false)
const PAGE = 40
const shown = ref(PAGE)
const visibleItems = computed(() => (phone.value ? store.items.slice(0, shown.value) : store.items))
const activeFilters = computed(() => ['account_id', 'category', 'area_id', 'priority', 'needs_reply'].filter((k) => store.filters[k]).length + (store.filters.handled !== '0' ? 1 : 0))

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

function open(email) {
  run(() => store.open(email.id))
}

function setHandled(email, handled) {
  run(() => store.markHandled(email.id, handled))
}

function update(body) {
  if (!store.selected) return
  run(() => store.update(store.selected.id, body))
}

function createTask(body) {
  if (!store.selected) return
  run(async () => {
    const result = await store.createTask(store.selected.id, body)
    notice.value = result.created ? `Task "${result.task.title}" created.` : 'A task already existed for this email.'
  })
}

function reclassify() {
  if (!store.selected) return
  run(() => store.reclassify(store.selected.id))
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
</script>

<template>
  <div class="mail">
    <PageHeader v-if="!phone" title="Mail">
      <template #meta><span class="num">{{ store.counts.unhandled }} unhandled, {{ store.counts.needs_reply }} need a reply</span></template>
      <UiButton :loading="store.syncing" @click="sync">Sync now</UiButton>
      <RouterLink :to="{ name: 'settings' }" class="link-btn">Accounts</RouterLink>
    </PageHeader>
    <div v-else class="phead">
      <div><h1>Mail</h1><span class="muted small num">{{ store.counts.unhandled }} unhandled, {{ store.counts.needs_reply }} need a reply</span></div>
      <UiButton size="sm" :loading="store.syncing" @click="sync">Sync now</UiButton>
    </div>
    <template v-if="phone">
      <div class="pfilters">
        <input v-model="store.filters.q" type="search" placeholder="Search mail" aria-label="Search mail" class="psearch" @change="store.load()" />
        <button type="button" class="fbtn" :class="{ on: filtersOpen || activeFilters }" :aria-expanded="filtersOpen" @click="filtersOpen = !filtersOpen"><PhFunnelSimple :size="16" weight="bold" />Filters<span v-if="activeFilters" class="num"> {{ activeFilters }}</span></button>
      </div>
      <MailFilters v-if="filtersOpen" class="pfilters-body" :filters="store.filters" :accounts="store.accounts" @change="store.load()" @reset="store.resetFilters()" />
    </template>
    <MailFilters v-else :filters="store.filters" :accounts="store.accounts" @change="store.load()" @reset="store.resetFilters()" />
    <p v-if="error || store.error" class="error notice">{{ error || store.error }}</p>
    <p v-if="notice" class="muted small notice">{{ notice }}</p>

    <UiLoadGate :ready="ready" label="Loading mail">
      <ul class="list">
        <li v-if="!store.items.length">
          <UiEmpty title="No emails match" :hint="store.accounts.length ? 'Change the filters or sync.' : 'No mail accounts are configured (MAIL_ACCOUNTS_JSON).'">
            <template #icon><PhTray /></template>
          </UiEmpty>
        </li>
        <EmailRow
          v-for="e in visibleItems"
          :key="e.id"
          :email="e"
          :active="e.id === store.selected?.id"
          @open="open"
          @handled="setHandled"
        />
        <li v-if="phone && store.items.length > shown" class="more"><UiButton size="sm" block @click="shown += PAGE">Show more ({{ store.items.length - shown }} left)</UiButton></li>
      </ul>
    </UiLoadGate>

    <UiModal :open="Boolean(store.selected)" size="lg" @close="store.close()">
      <EmailDetail v-if="store.selected" :email="store.selected" :busy="busy" @close="store.close()" @update="update" @task="createTask" @reclassify="reclassify" />
    </UiModal>
  </div>
</template>

<style scoped>
.notice { margin-top: var(--sp-3); }
.phead { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.phead h1 { font-size: var(--fs-2xl); }
.pfilters { display: flex; gap: var(--sp-2); }
.psearch { flex: 1; min-width: 0; }
.fbtn { display: inline-flex; align-items: center; gap: 6px; height: var(--control-h); padding: 0 12px; border: 1px solid var(--line-2); border-radius: var(--r-md); background: var(--surface); color: var(--ink-2); font-size: var(--fs-md); font-weight: 500; }
.fbtn.on { background: var(--surface-3); color: var(--ink); border-color: transparent; }
.pfilters-body { margin-top: var(--sp-2); }
.pfilters-body :deep(.search) { display: none; }
.more { padding-top: var(--sp-2); }
.list { display: flex; flex-direction: column; gap: var(--sp-2); min-width: 0; margin-top: var(--sp-4); }
</style>
