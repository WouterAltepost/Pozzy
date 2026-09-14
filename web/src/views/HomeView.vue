<script setup>
import { onMounted, reactive } from 'vue'
import { getAreas, getHealth, getMe } from '../api/core'

// Each block loads independently so one failing call never blanks the page.
const me = reactive({ data: null, error: '', loading: true })
const health = reactive({ data: null, error: '', loading: true })
const areas = reactive({ data: [], error: '', loading: true })

async function load(target, fn) {
  target.loading = true
  target.error = ''
  try {
    target.data = await fn()
  } catch (err) {
    target.error = err.message
  } finally {
    target.loading = false
  }
}

function refresh() {
  load(me, getMe)
  load(health, getHealth)
  load(areas, getAreas)
}

onMounted(refresh)
</script>

<template>
  <section class="card">
    <h2>Me (GET /api/me)</h2>
    <p v-if="me.loading" class="muted">Loading...</p>
    <p v-else-if="me.error" class="error">{{ me.error }}</p>
    <p v-else>Logged in as <strong>{{ me.data.email }}</strong><br /><span class="muted">id {{ me.data.id }}</span></p>
  </section>

  <section class="card">
    <h2>API health (GET /api/health)</h2>
    <p v-if="health.loading" class="muted">Loading...</p>
    <p v-else-if="health.error" class="error">{{ health.error }}</p>
    <p v-else>
      status <strong :class="{ ok: health.data.status === 'ok' }">{{ health.data.status }}</strong>,
      db <strong :class="{ ok: health.data.db, error: !health.data.db }">{{ health.data.db ? 'connected' : 'unreachable' }}</strong>,
      time <span class="muted">{{ health.data.time }}</span>
    </p>
  </section>

  <section class="card">
    <h2>Areas (GET /api/areas)</h2>
    <p v-if="areas.loading" class="muted">Loading...</p>
    <p v-else-if="areas.error" class="error">{{ areas.error }}</p>
    <ul v-else class="areas">
      <li v-for="area in areas.data" :key="area.id">
        <span class="swatch" :style="{ background: area.color }"></span>{{ area.name }}
      </li>
    </ul>
  </section>

  <button type="button" @click="refresh">Refresh</button>
</template>
