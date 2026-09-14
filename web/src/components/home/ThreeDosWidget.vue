<script setup>
import { onMounted, ref } from 'vue'
import { createDo, listDos, updateDo } from '../../api/dos'
import { formatDay, today } from '../../lib/dates'

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
</script>

<template>
  <section v-if="!failed && dos" class="card widget">
    <h2>Today's three do's <span class="muted">{{ formatDay(today()) }}</span></h2>
    <ul>
      <li v-for="d in dos" :key="d.id" :class="{ done: d.done }">
        <input type="checkbox" :checked="d.done" @change="toggle(d)" />
        <span>{{ d.title }}</span>
        <span v-if="d.warning" class="warn">rolled {{ d.roll_count }}x</span>
      </li>
      <li v-if="!dos.length" class="muted">Nothing set for today. <RouterLink :to="{ name: 'goals' }">Set three do's</RouterLink></li>
    </ul>
    <form v-if="dos.length < 3" class="add" @submit.prevent="add">
      <input v-model="title" type="text" placeholder="Add a do" />
      <button type="submit">Add</button>
    </form>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; }
ul { list-style: none; padding: 0; margin: 0; }
li { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0; }
li.done span { text-decoration: line-through; color: #9ca3af; }
.warn { color: #b91c1c; font-size: 0.75rem; font-weight: 600; }
.add { display: flex; gap: 0.4rem; margin-top: 0.4rem; }
.add input { flex: 1; font: inherit; padding: 0.3rem; border: 1px solid #d1d5db; border-radius: 4px; }
</style>
