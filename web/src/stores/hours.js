import { defineStore } from 'pinia'
import * as hoursApi from '../api/hours'
import { addDays, mondayOf } from '../lib/dates'

const TIMER_KEY = 'pozzy.hours.timer'

function readTimer() {
  try {
    const raw = localStorage.getItem(TIMER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useHoursStore = defineStore('hours', {
  state: () => ({
    weekStart: mondayOf(),
    logs: [],
    summary: null,
    loading: false,
    error: '',
    timer: readTimer(), // { startedAt: iso, area_id, note, tags }
  }),
  getters: {
    weekEnd: (s) => addDays(s.weekStart, 6),
    timerRunning: (s) => Boolean(s.timer),
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const [logs, summary] = await Promise.all([
          hoursApi.listHours({ from: this.weekStart, to: this.weekEnd }),
          hoursApi.hoursWeek(this.weekStart),
        ])
        this.logs = logs
        this.summary = summary
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async setWeek(weekStart) {
      this.weekStart = weekStart
      await this.load()
    },
    async create(body) {
      await hoursApi.createHours(body)
      await this.load()
    },
    async update(id, body) {
      await hoursApi.updateHours(id, body)
      await this.load()
    },
    async remove(id) {
      await hoursApi.deleteHours(id)
      await this.load()
    },
    startTimer({ area_id = null, note = '', tags = [] } = {}) {
      this.timer = { startedAt: new Date().toISOString(), area_id, note, tags }
      try {
        localStorage.setItem(TIMER_KEY, JSON.stringify(this.timer))
      } catch {}
    },
    cancelTimer() {
      this.timer = null
      try {
        localStorage.removeItem(TIMER_KEY)
      } catch {}
    },
    async stopTimer(overrides = {}) {
      if (!this.timer) return null
      const started = new Date(this.timer.startedAt)
      const minutes = Math.max(1, Math.round((Date.now() - started.getTime()) / 60000))
      const body = {
        minutes,
        area_id: this.timer.area_id || null,
        note: this.timer.note || null,
        tags: this.timer.tags || [],
        ...overrides,
      }
      const log = await hoursApi.createHours(body)
      this.cancelTimer()
      await this.load()
      return log
    },
  },
})
