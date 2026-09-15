<script setup>
import { accountName } from '../../lib/mail'
import { onMounted, reactive, ref } from 'vue'
import { formatDateTime } from '../../lib/dates'
import { useMailStore } from '../../stores/mail'
import UiBadge from '../ui/UiBadge.vue'
import UiButton from '../ui/UiButton.vue'

// Mounted inside SettingsView's Integrations card.
const store = useMailStore()
const status = reactive({})
const error = ref('')
const notice = ref('')

onMounted(() => store.loadAccounts())

async function toggle(account) {
  error.value = ''
  try {
    await store.updateAccount(account.id, { enabled: !account.enabled })
  } catch (err) {
    error.value = err.message
  }
}

async function saveMeta(account, field, value) {
  error.value = ''
  try {
    await store.updateAccount(account.id, { [field]: value })
  } catch (err) {
    error.value = err.message
  }
}

async function test(account) {
  status[account.id] = 'testing'
  try {
    const result = await store.testAccount(account.id)
    status[account.id] = `ok, ${result.messages} messages in INBOX`
  } catch (err) {
    status[account.id] = `failed: ${err.message}`
    store.loadAccounts()
  }
}

async function sync() {
  error.value = ''
  notice.value = ''
  try {
    const result = await store.sync()
    const inserted = result.accounts.reduce((n, a) => n + (a.inserted || 0), 0)
    notice.value = `Synced ${inserted} new email(s), ${result.classified.classified} classified.`
  } catch (err) {
    error.value = err.message
  }
}
</script>

<template>
  <div class="integration">
    <h3>Mail accounts</h3>
    <p class="muted small">
      Accounts and app passwords come from <code>MAIL_ACCOUNTS_JSON</code> in the environment. Passwords are never stored in the database.
      IMAP access is read-only: nothing in Gmail is changed.
    </p>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <p v-if="notice" class="muted small">{{ notice }}</p>
    <p v-if="!store.accounts.length" class="muted small">No accounts configured.</p>
    <ul v-else class="accounts">
      <li v-for="a in store.accounts" :key="a.id" class="account" :class="{ off: !a.enabled }">
        <input type="color" :value="a.color || '#6F727A'" title="Colour" aria-label="Account colour" @change="saveMeta(a, 'color', $event.target.value)" />
        <span class="name">{{ accountName(a) }}</span>
        <input class="label" type="text" :value="a.label" maxlength="60" aria-label="Tag" title="Shown as a tag on each email. Reset from MAIL_ACCOUNTS_JSON on the next sync." @change="saveMeta(a, 'label', $event.target.value)" />
        <span class="email muted small truncate">{{ a.email }}</span>
        <label class="check"><input type="checkbox" :checked="a.enabled" @change="toggle(a)" /> Enabled</label>
        <UiButton size="sm" @click="test(a)">Test</UiButton>
        <span class="info xs">
          <span v-if="status[a.id]" class="muted">{{ status[a.id] }}</span>
          <UiBadge v-else-if="a.last_error" tone="danger" :title="a.last_error">{{ a.last_error }}</UiBadge>
          <span v-else-if="a.last_synced_at" class="muted num">synced {{ formatDateTime(a.last_synced_at) }}, last UID {{ a.last_uid }}</span>
          <span v-else class="muted">never synced</span>
        </span>
      </li>
    </ul>
    <div class="actions">
      <UiButton :loading="store.syncing" :disabled="!store.accounts.length" @click="sync">Sync now</UiButton>
      <span class="muted small">The job also runs every 15 minutes.</span>
    </div>
  </div>
</template>

<style scoped>
.integration { display: flex; flex-direction: column; gap: var(--sp-2); border-top: 1px solid var(--line); padding-top: var(--sp-4); }
h3 { font-size: var(--fs-base); }
.accounts { display: flex; flex-direction: column; gap: var(--sp-2); }
.account { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); padding: var(--sp-2) var(--sp-3); background: var(--surface-2); border-radius: var(--r-md); }
.account.off { opacity: 0.6; }
.name { font-weight: 600; font-size: var(--fs-md); white-space: nowrap; }
.label { height: var(--control-h-sm); width: 110px; font-size: var(--fs-md); }
.email { flex: 1 1 160px; min-width: 0; }
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-md); }
.info { flex-basis: 100%; }
.actions { display: flex; align-items: center; gap: var(--sp-3); margin-top: var(--sp-1); }
</style>
