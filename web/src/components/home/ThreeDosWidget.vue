<script setup>
import { useWidgetLink } from '../../composables/useWidgetLink'
import { onMounted, ref } from 'vue'
import { PhCheckSquare } from '@phosphor-icons/vue'
import { createDo, listDos, updateDo } from '../../api/dos'
import { formatDay, today } from '../../lib/dates'
import UiBadge from '../ui/UiBadge.vue'
import UiButton from '../ui/UiButton.vue'
import UiEmpty from '../ui/UiEmpty.vue'

// Self-contained: fetches its own data, renders nothing on failure (BUILD.md).
const dos = ref(null)
const failed = ref(false)
const title = ref('')

async function load() {
  try {
    dos.value = await listDos({ date: today() })
    failed.value = false
  } catch {
    failed.value = true
  }
}

async function toggle(item) {
  try {
    const updated = await updateDo(item.id, { done: !item.done })
    Object.assign(item, updated)
  } catch {
    load()
  }
}

async function add() {
  const t = title.value.trim()
  if (!t) return
  try {
    await createDo({ date: today(), title: t })
    title.value = ''
    await load()
  } catch {
    failed.value = true
  }
}

onMounted(load)
const link = useWidgetLink('goals')
</script>

<template>
  <section v-if="!failed && dos" class="card widget clickable" tabindex="0" role="link" :aria-label="'Open goals'" @click="link.onClick" @keydown="link.onKey">
    <div class="card-head">
      <h2>Today's three do's</h2>
      <span class="meta">{{ formatDay(today()) }}</span>
    </div>
    <ul v-if="dos.length">
      <li v-for="d in dos" :key="d.id" class="list-row" :class="{ done: d.done }">
        <input type="checkbox" :checked="d.done" :aria-label="d.title" @change="toggle(d)" />
        <span class="title">{{ d.title }}</span>
        <UiBadge v-if="d.warning" tone="warn">rolled {{ d.roll_count }}x</UiBadge>
        <UiBadge v-else-if="d.roll_count" tone="neutral">rolled</UiBadge>
      </li>
    </ul>
    <UiEmpty v-else compact title="Nothing set for today" hint="Three things that would make today a good day.">
      <template #icon><PhCheckSquare /></template>
      <template #action><RouterLink :to="{ name: 'goals' }" class="link-btn">Set three do's</RouterLink></template>
    </UiEmpty>
    <form v-if="dos.length < 3" class="add" @submit.prevent="add">
      <input v-model="title" type="text" placeholder="Add a do" aria-label="Add a do" />
      <UiButton type="submit" :disabled="!title.trim()">Add</UiButton>
    </form>
  </section>
</template>

<style scoped>
.title { flex: 1; min-width: 0; }
.add { display: flex; gap: var(--sp-2); margin-top: var(--sp-3); }
.add input { flex: 1; }
</style>
