<script setup>
import { computed, onMounted, ref } from 'vue'
import { formatDateTime } from '../../lib/dates'
import { useCalendarStore } from '../../stores/calendar'

// Mounted by stream E inside SettingsView's Integrations card. Self-contained:
// loads the account, lets Wouter pick which calendars sync and where Pozzy writes.
const store = useCalendarStore()
const selected = ref([])
const writeUrl = ref('')
const enabled = ref(true)
const busy = ref(false)
const message = ref('')

const account = computed(() => store.account)
const calendars = computed(() => account.value?.known_calendars || [])

function fill() {
  if (!account.value) return
  selected.value = [...account.value.calendar_urls]
  writeUrl.value = account.value.write_calendar_url || ''
  enabled.value = account.value.enabled
}

onMounted(async () => {
  await store.loadAccount()
  fill()
})

async function discover() {
  busy.value = true
  message.value = ''
  try {
    const list = await store.discover()
    fill()
    message.value = `Found ${list.length} calendars.`
  } catch {
    // store.accountError is shown
  } finally {
    busy.value = false
  }
}

async function save() {
  busy.value = true
  message.value = ''
  try {
    if (writeUrl.value && !selected.value.includes(writeUrl.value)) selected.value.push(writeUrl.value)
    await store.saveAccount({ calendar_urls: selected.value, write_calendar_url: writeUrl.value || null, enabled: enabled.value })
    fill()
    message.value = 'Saved. The next sync applies the selection.'
  } catch {
    // store.accountError is shown
  } finally {
    busy.value = false
  }
}

async function syncNow() {
  busy.value = true
  message.value = ''
  await store.sync()
  fill()
  message.value = store.syncMessage
  busy.value = false
}
</script>

<template>
  <div class="calendar-accounts">
    <h3>iCloud calendar</h3>
    <p v-if="store.accountError" class="error">{{ store.accountError }}</p>
    <p v-if="!account" class="muted small">Not configured. Set ICLOUD_USERNAME and ICLOUD_APP_PASSWORD in the environment and restart the API.</p>
    <template v-else>
      <p class="small">
        <strong>{{ account.name }}</strong> <span class="muted">{{ account.username }}</span><br />
        <span class="muted">{{ account.last_synced_at ? 'Last synced ' + formatDateTime(account.last_synced_at) : 'Never synced' }}</span>
        <span v-if="account.last_sync_error" class="error"> {{ account.last_sync_error }}</span>
      </p>
      <label class="inline"><input v-model="enabled" type="checkbox" /> Sync enabled</label>
      <p v-if="!calendars.length" class="muted small">No calendars discovered yet.</p>
      <div v-else class="list">
        <label v-for="c in calendars" :key="c.url" class="inline">
          <input v-model="selected" type="checkbox" :value="c.url" /> {{ c.name }}
        </label>
      </div>
      <label v-if="calendars.length" class="write">
        Pozzy writes new events to
        <select v-model="writeUrl">
          <option v-for="c in calendars" :key="c.url" :value="c.url">{{ c.name }}</option>
        </select>
      </label>
      <div class="actions">
        <button type="button" :disabled="busy" @click="discover">{{ calendars.length ? 'Refresh calendar list' : 'Discover calendars' }}</button>
        <button type="button" :disabled="busy || !calendars.length" @click="save">Save calendars</button>
        <button type="button" :disabled="busy" @click="syncNow">Sync now</button>
        <span class="muted small">{{ message }}</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
h3 { font-size: 0.95rem; margin: 0.5rem 0 0.4rem; }
.small { font-size: 0.85rem; }
.inline { display: flex; align-items: center; gap: 0.4rem; font-size: 0.9rem; }
.list { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; margin: 0.4rem 0; }
.write { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #4b5563; margin: 0.4rem 0; }
select { font: inherit; padding: 0.3rem; border: 1px solid #d1d5db; border-radius: 4px; }
.actions { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
</style>
