<script setup>
import { onMounted, ref } from 'vue'
import { topEmails, updateEmail } from '../../api/mail'
import PriorityBadge from '../mail/PriorityBadge.vue'

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
</script>

<template>
  <section v-if="!failed && emails" class="card widget">
    <h2>Top emails <RouterLink :to="{ name: 'mail' }" class="muted small">inbox</RouterLink></h2>
    <ul>
      <li v-for="e in emails" :key="e.id">
        <input type="checkbox" title="Mark handled" @change="handled(e)" />
        <span class="account" :style="{ background: e.account?.color || '#9ca3af' }" :title="e.account?.label"></span>
        <PriorityBadge :priority="e.priority" />
        <span class="text">
          <span class="from">{{ e.from_name || e.from_email }}</span>
          <a v-if="e.gmail_url" :href="e.gmail_url" target="_blank" rel="noopener" class="subject">{{ e.subject }}</a>
          <span v-else class="subject">{{ e.subject }}</span>
        </span>
        <span v-if="e.needs_reply" class="reply">reply</span>
      </li>
      <li v-if="!emails.length" class="muted">Inbox handled.</li>
    </ul>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; }
.small { font-size: 0.78rem; font-weight: normal; }
ul { list-style: none; padding: 0; margin: 0; }
li { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0; font-size: 0.9rem; }
.account { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.from { font-size: 0.75rem; color: #6b7280; }
.subject { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: inherit; text-decoration: none; }
.subject:hover { text-decoration: underline; }
.reply { font-size: 0.7rem; background: #dbeafe; color: #1d4ed8; padding: 0 0.3rem; border-radius: 3px; font-weight: 600; }
</style>
