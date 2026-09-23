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
    suggestions: null, // { from, to, items, total_minutes, per_area }
    loading: false,
    error: '',
    timer: readTimer(), // { startedAt: iso, area_id, note, tags }
  }),
  getters: {
    weekEnd: (s) => addDays(s.weekStart, 6),
    timerRunning: (s) => Boolean(s.timer),
    suggestionCount: (s) => s.suggestions?.items.length ?? 0,
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const [logs, summary, suggestions] = await Promise.all([
          hoursApi.listHours({ from: this.weekStart, to: this.weekEnd }),
          hoursApi.hoursWeek(this.weekStart),
          hoursApi.hoursSuggestions().catch(() => this.suggestions), // never blocks the page
        ])
        this.logs = logs
        this.summary = summary
        this.suggestions = suggestions
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
    // Writes patch the list in place and refresh only the week totals (one call instead of two).
    _inWeek(log) {
      return log.date >= this.weekStart && log.date <= this.weekEnd
    },
    _insert(log) {
      if (!this._inWeek(log)) return
      this.logs = [log, ...this.logs.filter((l) => l.id !== log.id)].sort((a, b) => (a.date === b.date ? (a.created_at < b.created_at ? 1 : -1) : a.date < b.date ? 1 : -1))
    },
    async _refreshSummary() {
      try {
        this.summary = await hoursApi.hoursWeek(this.weekStart)
      } catch (err) {
        this.error = err.message
      }
    },
    async create(body) {
      const log = await hoursApi.createHours(body)
      this._insert(log)
      await this._refreshSummary()
      return log
    },
    async update(id, body) {
      const log = await hoursApi.updateHours(id, body)
      this.logs = this.logs.filter((l) => l.id !== id)
      this._insert(log)
      await this._refreshSummary()
      return log
    },
    async remove(id) {
      const gone = this.logs.find((l) => l.id === id)
      this.logs = this.logs.filter((l) => l.id !== id)
      try {
        await hoursApi.deleteHours(id)
      } catch (err) {
        if (gone) this._insert(gone)
        throw err
      }
      await this._refreshSummary()
    },
    async loadSuggestions() {
      this.suggestions = await hoursApi.hoursSuggestions()
    },
    // Accept: the rows leave the card at once, the logs land in the week list from the response.
    async acceptSuggestions(items) {
      const refs = new Set(items.map((i) => i.ref))
      const kept = this.suggestions?.items || []
      this._dropSuggestions(refs)
      try {
        const { created } = await hoursApi.acceptHoursSuggestions(items)
        for (const log of created) this._insert(log)
        await this._refreshSummary()
        return created
      } catch (err) {
        if (this.suggestions) this.suggestions.items = kept
        throw err
      }
    },
    async dismissSuggestions(refs) {
      const kept = this.suggestions?.items || []
      this._dropSuggestions(new Set(refs))
      try {
        await hoursApi.dismissHoursSuggestions(refs)
      } catch (err) {
        if (this.suggestions) this.suggestions.items = kept
        throw err
      }
    },
    _dropSuggestions(refs) {
      if (!this.suggestions) return
      const items = this.suggestions.items.filter((i) => !refs.has(i.ref))
      const perArea = {}
      for (const i of items) perArea[i.area_name || 'Unassigned'] = (perArea[i.area_name || 'Unassigned'] || 0) + i.minutes
      this.suggestions = {
        ...this.suggestions,
        items,
        total_minutes: items.reduce((s, i) => s + i.minutes, 0),
        per_area: Object.entries(perArea).map(([area, minutes]) => ({ area, minutes })).sort((a, b) => b.minutes - a.minutes),
      }
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
      const log = await this.create(body)
      this.cancelTimer()
      return log
    },
  },
})
