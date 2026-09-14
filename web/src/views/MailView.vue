<script setup>
import { onMounted, ref } from 'vue'
import EmailDetail from '../components/mail/EmailDetail.vue'
import EmailRow from '../components/mail/EmailRow.vue'
import MailFilters from '../components/mail/MailFilters.vue'
import { useAreasStore } from '../stores/areas'
import { useMailStore } from '../stores/mail'

const store = useMailStore()
const areas = useAreasStore()
const error = ref('')
const notice = ref('')
const busy = ref(false)

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
    <div class="head">
      <h1>Mail</h1>
      <span class="muted">{{ store.counts.unhandled }} unhandled, {{ store.counts.needs_reply }} need a reply</span>
      <button type="button" :disabled="store.syncing" @click="sync">{{ store.syncing ? 'Syncing...' : 'Sync now' }}</button>
      <RouterLink :to="{ name: 'settings' }" class="muted small">accounts</RouterLink>
    </div>
    <MailFilters :filters="store.filters" :accounts="store.accounts" @change="store.load()" @reset="store.resetFilters()" />
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <p v-if="notice" class="muted">{{ notice }}</p>

    <div class="layout" :class="{ split: store.selected }">
      <ul class="list">
        <li v-if="store.loading && !store.items.length" class="muted">Loading...</li>
        <li v-else-if="!store.items.length" class="muted">
          No emails match. <span v-if="!store.accounts.length">No mail accounts are configured (MAIL_ACCOUNTS_JSON).</span>
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
      <EmailDetail
        v-if="store.selected"
        :email="store.selected"
        :busy="busy"
        @close="store.close()"
        @update="update"
        @task="createTask"
        @reclassify="reclassify"
      />
    </div>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; margin: 0; }
.head { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; margin-bottom: 0.75rem; }
.small { font-size: 0.8rem; }
.layout { display: grid; grid-template-columns: 1fr; gap: 1rem; margin-top: 0.75rem; align-items: start; }
@media (min-width: 900px) { .layout.split { grid-template-columns: minmax(0, 1fr) minmax(320px, 46%); } }
.list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.3rem; }
</style>
