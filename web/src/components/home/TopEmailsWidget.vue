<script setup>
import { useWidgetLink } from '../../composables/useWidgetLink'
import { onMounted, ref } from 'vue'
import { PhTray } from '@phosphor-icons/vue'
import { topEmails, updateEmail } from '../../api/mail'
import PriorityBadge from '../mail/PriorityBadge.vue'
import UiBadge from '../ui/UiBadge.vue'
import UiEmpty from '../ui/UiEmpty.vue'

const emails = ref(null)
const failed = ref(false)

async function load() {
  try {
    emails.value = await topEmails()
    failed.value = false
  } catch {
    failed.value = true
  }
}

async function handled(e) {
  try {
    await updateEmail(e.id, { handled: true })
    emails.value = emails.value.filter((x) => x.id !== e.id)
  } catch {
    load()
  }
}

onMounted(load)
const link = useWidgetLink('mail')
</script>

<template>
  <section v-if="!failed && emails" class="card widget clickable" tabindex="0" role="link" :aria-label="'Open mail'" @click="link.onClick" @keydown="link.onKey">
    <div class="card-head">
      <h2>Top emails</h2>
      <span class="meta"><RouterLink :to="{ name: 'mail' }">Inbox</RouterLink></span>
    </div>
    <ul v-if="emails.length">
      <li v-for="e in emails" :key="e.id" class="list-row">
        <input type="checkbox" title="Mark handled" :aria-label="'Mark handled: ' + e.subject" @change="handled(e)" />
        <span class="account" :style="{ background: e.account?.color || 'var(--ink-3)' }" :title="e.account?.label"></span>
        <PriorityBadge :priority="e.priority" />
        <span class="text">
          <span class="from truncate">{{ e.from_name || e.from_email }}</span>
          <a v-if="e.gmail_url" :href="e.gmail_url" target="_blank" rel="noopener" class="subject truncate">{{ e.subject }}</a>
          <span v-else class="subject truncate">{{ e.subject }}</span>
        </span>
        <UiBadge v-if="e.needs_reply" tone="info">reply</UiBadge>
      </li>
    </ul>
    <UiEmpty v-else compact title="Inbox handled" hint="Nothing unhandled in the top of the inbox.">
      <template #icon><PhTray /></template>
    </UiEmpty>
  </section>
</template>

<style scoped>
.account { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.from { font-size: var(--fs-sm); color: var(--ink-3); }
.subject { color: inherit; text-decoration: none; font-size: var(--fs-md); }
.subject:hover { text-decoration: underline; }
</style>
