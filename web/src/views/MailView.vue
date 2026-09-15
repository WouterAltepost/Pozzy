<script setup>
import { ref } from 'vue'
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
import { useAreasStore } from '../stores/areas'
import { useMailStore } from '../stores/mail'

const store = useMailStore()
const areas = useAreasStore()
const error = ref('')
const notice = ref('')
const busy = ref(false)
const ready = useReady(() => Promise.all([store.load(), store.loadAccounts(), areas.load()]))

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

    <UiLoadGate :ready="ready" label="Loading mail">
      <ul class="list">
        <li v-if="!store.items.length">
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
    </UiLoadGate>

    <UiModal :open="Boolean(store.selected)" size="lg" @close="store.close()">
      <EmailDetail v-if="store.selected" :email="store.selected" :busy="busy" @close="store.close()" @update="update" @task="createTask" @reclassify="reclassify" />
    </UiModal>
  </div>
</template>

<style scoped>
.notice { margin-top: var(--sp-3); }
.list { display: flex; flex-direction: column; gap: var(--sp-2); min-width: 0; margin-top: var(--sp-4); }
</style>
