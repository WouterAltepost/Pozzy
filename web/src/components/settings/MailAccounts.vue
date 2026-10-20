<script setup>
import { accountName } from '../../lib/mail'
import { onMounted, reactive, ref } from 'vue'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { formatDateTime } from '../../lib/dates'
import { tick } from '../../lib/haptics'
import { useMailStore } from '../../stores/mail'
import UiBadge from '../ui/UiBadge.vue'
import UiButton from '../ui/UiButton.vue'

// Mounted inside SettingsView's Integrations card.
const store = useMailStore()
const status = reactive({})
const error = ref('')
const notice = ref('')
// Phone: one small plate per account (switch, tag, status with Test), then Sync now.
const phone = useMediaQuery('(max-width: 1023px)')
function flip(account) {
  tick()
  toggle(account)
}

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
  <section v-if="phone" class="ios-sec">
    <h2 class="ios-head">Mail accounts</h2>
    <p v-if="!store.accounts.length" class="ios-plate ios-row muted">No accounts configured</p>
    <div v-for="a in store.accounts" :key="a.id" class="ios-plate acct" :class="{ off: !a.enabled }">
      <div class="ios-row">
        <input type="color" class="swatch" :value="a.color || '#6F727A'" aria-label="Account colour" @change="saveMeta(a, 'color', $event.target.value)" />
        <span class="lbl"><span class="name truncate">{{ accountName(a) }}</span><span class="sub truncate">{{ a.email }}</span></span>
        <input type="checkbox" role="switch" :checked="a.enabled" :aria-label="'Sync ' + accountName(a)" @change="flip(a)" />
      </div>
      <label class="ios-row">
        <span class="lbl">Tag</span>
        <input class="tag-in" type="text" :value="a.label" maxlength="60" placeholder="None" @change="saveMeta(a, 'label', $event.target.value)" />
      </label>
      <div class="ios-row">
        <span class="lbl status">
          <span v-if="status[a.id]">{{ status[a.id] }}</span>
          <span v-else-if="a.last_error" class="bad">{{ a.last_error }}</span>
          <span v-else-if="a.last_synced_at" class="num">Synced {{ formatDateTime(a.last_synced_at) }}</span>
          <span v-else>Never synced</span>
        </span>
        <button type="button" class="test" @click="test(a)">Test</button>
      </div>
    </div>
    <div class="ios-plate">
      <button type="button" class="ios-row act" :disabled="store.syncing || !store.accounts.length" @click="sync">{{ store.syncing ? 'Syncing…' : 'Sync now' }}</button>
    </div>
    <p v-if="error || store.error" class="ios-foot err">{{ error || store.error }}</p>
    <p v-if="notice" class="ios-foot">{{ notice }}</p>
    <p class="ios-foot">Accounts and app passwords come from MAIL_ACCOUNTS_JSON in the environment; passwords are never stored in the database. IMAP access is read-only. The sync also runs every 15 minutes.</p>
  </section>
  <div v-else class="integration">
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

/* Phone: inset grouped plates, as in the iOS Settings app. */
@media (max-width: 1023px) {
  .ios-sec { margin-bottom: var(--sp-8); }
  .ios-head { margin: 0 16px 6px; font-size: 0.8125rem; font-weight: 400; text-transform: uppercase; color: var(--ink-3); }
  .ios-plate { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; margin: 0 0 var(--sp-4); }
  .ios-row { position: relative; display: flex; align-items: center; gap: 12px; width: 100%; min-height: 44px; padding: 6px 16px; border: 0; background: none; color: var(--ink); font: inherit; font-size: 1.0625rem; text-align: left; }
  .ios-row + .ios-row::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .lbl { flex: 1; min-width: 0; display: flex; flex-direction: column; }
  .acct.off .name, .acct.off .swatch { opacity: 0.5; }
  .acct .ios-row:first-child + .ios-row::before { left: 52px; }
  .swatch { width: 24px; height: 24px; padding: 0; border: 0; border-radius: 50%; overflow: hidden; background: none; flex: none; }
  .swatch::-webkit-color-swatch-wrapper { padding: 0; }
  .swatch::-webkit-color-swatch { border: 0; border-radius: 50%; }
  .name { font-size: 1.0625rem; }
  .sub { font-size: 0.9375rem; color: var(--ink-3); }
  .ios-row .tag-in { width: 160px; height: 32px; padding: 0; background: transparent; text-align: right; color: var(--ink-3); }
  .ios-row .tag-in:focus-visible { box-shadow: none; color: var(--ink); }
  .status { font-size: 0.9375rem; color: var(--ink-3); }
  .status .bad { color: var(--danger); }
  .test { flex: none; height: 32px; padding: 0 4px; border: 0; background: none; color: var(--brand); font: inherit; font-size: 1.0625rem; }
  .test:active { opacity: 0.4; }
  .act { color: var(--brand); }
  .act:active:not(:disabled) { background: var(--surface-3); }
  .act:disabled { color: var(--ink-4); }
  .ios-foot { margin: -8px 16px 0; font-size: 0.8125rem; line-height: 1.4; color: var(--ink-3); }
  .ios-foot + .ios-foot { margin-top: 6px; }
  .ios-foot.err { color: var(--danger); }
}
</style>
