<script setup>
import { onMounted, ref } from 'vue'
import { PhTray } from '@phosphor-icons/vue'
import EmailDetail from '../components/mail/EmailDetail.vue'
import EmailRow from '../components/mail/EmailRow.vue'
import MailFilters from '../components/mail/MailFilters.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiSheet from '../components/ui/UiSheet.vue'
import UiSkeleton from '../components/ui/UiSkeleton.vue'
import { useMediaQuery } from '../composables/useMediaQuery'
import { useAreasStore } from '../stores/areas'
import { useMailStore } from '../stores/mail'

const store = useMailStore()
const areas = useAreasStore()
const error = ref('')
const notice = ref('')
const busy = ref(false)
const narrow = useMediaQuery('(max-width: 899px)')

onMounted(() => Promise.all([store.load(), store.loadAccounts(), areas.load()]))

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
    <PageHeader title="Mail">
      <template #meta><span class="num">{{ store.counts.unhandled }} unhandled, {{ store.counts.needs_reply }} need a reply</span></template>
      <UiButton :loading="store.syncing" @click="sync">Sync now</UiButton>
      <RouterLink :to="{ name: 'settings' }" class="link-btn">Accounts</RouterLink>
    </PageHeader>
    <MailFilters :filters="store.filters" :accounts="store.accounts" @change="store.load()" @reset="store.resetFilters()" />
    <p v-if="error || store.error" class="error notice">{{ error || store.error }}</p>
    <p v-if="notice" class="muted small notice">{{ notice }}</p>

    <div class="layout" :class="{ split: store.selected && !narrow }">
      <ul class="list">
        <li v-if="store.loading && !store.items.length"><UiSkeleton :lines="6" /></li>
        <li v-else-if="!store.items.length">
          <UiEmpty title="No emails match" :hint="store.accounts.length ? 'Change the filters or sync.' : 'No mail accounts are configured (MAIL_ACCOUNTS_JSON).'">
            <template #icon><PhTray /></template>
          </UiEmpty>
        </li>
        <EmailRow
          v-for="e in store.items"
          :key="e.id"
          :email="e"
          :active="e.id === store.selected?.id"
          @open="open"
          @handled="setHandled"
        />
      </ul>
      <Transition name="panel">
        <aside v-if="store.selected && !narrow" class="card detail-panel">
          <EmailDetail :email="store.selected" :busy="busy" @close="store.close()" @update="update" @task="createTask" @reclassify="reclassify" />
        </aside>
      </Transition>
    </div>

    <UiSheet :open="Boolean(store.selected) && narrow" title="Email" @close="store.close()">
      <EmailDetail v-if="store.selected" :email="store.selected" :busy="busy" @close="store.close()" @update="update" @task="createTask" @reclassify="reclassify" />
    </UiSheet>
  </div>
</template>

<style scoped>
.notice { margin-top: var(--sp-3); }
.layout { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-5); margin-top: var(--sp-4); align-items: start; }
@media (min-width: 900px) { .layout.split { grid-template-columns: minmax(0, 1fr) minmax(340px, 44%); } }
.list { display: flex; flex-direction: column; gap: var(--sp-2); min-width: 0; }
.detail-panel { position: sticky; top: calc(var(--bar-h) + var(--sp-4)); margin: 0; }
.panel-enter-active { transition: opacity var(--dur-panel) var(--ease-out), transform var(--dur-panel) var(--ease-out); }
.panel-leave-active { transition: opacity var(--dur-hover) ease; }
.panel-enter-from { opacity: 0; transform: translateX(8px); }
.panel-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .panel-enter-from { transform: none; } }
</style>
