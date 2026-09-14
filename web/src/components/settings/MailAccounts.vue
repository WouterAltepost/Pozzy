<script setup>
import { onMounted, reactive, ref } from 'vue'
import { formatDateTime } from '../../lib/dates'
import { useMailStore } from '../../stores/mail'

// Stream E mounts this in SettingsView.vue at #settings-mail-accounts.
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
  status[account.id] = 'testing...'
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
  <div class="mail-accounts">
    <h3>Mail accounts</h3>
    <p class="muted small">
      Accounts and app passwords come from <code>MAIL_ACCOUNTS_JSON</code> in the environment. Passwords are never stored in the database.
      IMAP access is read-only: nothing in Gmail is changed.
    </p>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <p v-if="notice" class="muted small">{{ notice }}</p>
    <p v-if="!store.accounts.length" class="muted">No accounts configured.</p>
    <ul v-else>
      <li v-for="a in store.accounts" :key="a.id" :class="{ off: !a.enabled }">
        <input type="color" :value="a.color || '#9ca3af'" title="Colour" @change="saveMeta(a, 'color', $event.target.value)" />
        <input class="label" type="text" :value="a.label" maxlength="60" title="Label" @change="saveMeta(a, 'label', $event.target.value)" />
        <span class="email">{{ a.email }}</span>
        <label class="check small"><input type="checkbox" :checked="a.enabled" @change="toggle(a)" /> enabled</label>
        <button type="button" @click="test(a)">Test</button>
        <span class="muted small info">
          <span v-if="status[a.id]">{{ status[a.id] }}</span>
          <span v-else-if="a.last_error" class="error">{{ a.last_error }}</span>
          <span v-else-if="a.last_synced_at">synced {{ formatDateTime(a.last_synced_at) }}, last UID {{ a.last_uid }}</span>
          <span v-else>never synced</span>
        </span>
      </li>
    </ul>
    <div class="actions">
      <button type="button" :disabled="store.syncing || !store.accounts.length" @click="sync">{{ store.syncing ? 'Syncing...' : 'Sync now' }}</button>
      <span class="muted small">The job also runs every 15 minutes.</span>
    </div>
  </div>
</template>

<style scoped>
h3 { font-size: 0.95rem; margin: 0.75rem 0 0.25rem; }
.small { font-size: 0.8rem; }
ul { list-style: none; padding: 0; margin: 0.5rem 0; display: flex; flex-direction: column; gap: 0.4rem; }
li { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; padding: 0.4rem 0.5rem; border: 1px solid #e5e7eb; border-radius: 4px; }
li.off { opacity: 0.6; }
input[type='color'] { width: 28px; height: 24px; padding: 0; border: 1px solid #d1d5db; border-radius: 4px; background: none; }
.label { font: inherit; font-size: 0.85rem; padding: 0.25rem 0.4rem; border: 1px solid #d1d5db; border-radius: 4px; width: 120px; }
.email { font-size: 0.85rem; color: #374151; }
.check { display: flex; align-items: center; gap: 0.3rem; }
.info { flex-basis: 100%; }
.actions { display: flex; align-items: center; gap: 0.75rem; }
code { background: #f3f4f6; padding: 0 0.25rem; border-radius: 3px; }
</style>
