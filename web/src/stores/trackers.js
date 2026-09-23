import { defineStore } from 'pinia'
import * as trackersApi from '../api/trackers'
import { mondayOf } from '../lib/dates'

// Quick taps update the cell at once and the server's row replaces it when the call lands;
// nothing reloads the whole week any more. `version` bumps on every write so the series
// chart can refetch.
export const useTrackersStore = defineStore('trackers', {
  state: () => ({
    weekStart: mondayOf(),
    week: null,
    includeInactive: false,
    loading: false,
    error: '',
    histories: {},
    version: 0,
  }),
  getters: {
    trackers: (s) => s.week?.trackers ?? [],
    grouped() {
      const groups = new Map()
      for (const t of this.trackers) {
        const key = t.area_name || 'No area'
        if (!groups.has(key)) groups.set(key, { area: key, color: t.area_color || '#9ca3af', trackers: [] })
        groups.get(key).trackers.push(t)
      }
      return [...groups.values()]
    },
    cell: (s) => (id, date) => s.week?.trackers.find((t) => t.id === id)?.days.find((d) => d.date === date) ?? null,
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        this.week = await trackersApi.trackerWeek(this.weekStart, this.includeInactive)
        this.weekStart = this.week.week_start
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
      await trackersApi.createTracker(body)
      await this.load()
    },
    async update(id, body) {
      await trackersApi.updateTracker(id, body)
      await this.load()
    },
    async remove(id) {
      await trackersApi.deleteTracker(id)
      await this.load()
    },
    _patchRow(row) {
      if (!this.week) return
      const i = this.week.trackers.findIndex((t) => t.id === row.id)
      if (i === -1) return
      // Rows of another week (a tick on a cell outside the shown week) are ignored.
      if (row.days[0]?.date !== this.week.week_start) return
      this.week.trackers[i] = row
    },
    _finish(id, res) {
      if (res?.row) this._patchRow(res.row)
      delete this.histories[id]
      this.version += 1
      return res
    },
    // Expected value after one tap, applied before the server answers.
    _guess(t, current, direction) {
      if (t.type === 'daily_bool') return current ? 0 : 1
      const step = t.type === 'weekly_count' ? 1 : t.target_period === 'day' && t.target_value ? t.target_value : 1
      const next = (current || 0) + direction * step
      return next <= 0 ? null : Math.round(next * 100) / 100
    },
    _optimistic(id, date, value) {
      const t = this.week?.trackers.find((x) => x.id === id)
      const d = t?.days.find((x) => x.date === date)
      if (!t || !d) return
      d.value = value
      d.met = t.type === 'daily_bool' ? value > 0 : t.target_value == null ? value > 0 : value >= t.target_value
      t.week_total = t.days.reduce((s, x) => s + (x.value || 0), 0)
    },
    async _write(id, date, direction, call) {
      const t = this.week?.trackers.find((x) => x.id === id)
      const before = this.cell(id, date)?.value ?? null
      if (t) this._optimistic(id, date, this._guess(t, before, direction))
      try {
        const res = await call()
        this._finish(id, res)
        return { previous: before, value: res?.value ?? null }
      } catch (err) {
        if (t) this._optimistic(id, date, before)
        throw err
      }
    },
    tick(id, date) {
      return this._write(id, date, 1, () => trackersApi.tickTracker(id, date))
    },
    untick(id, date) {
      return this._write(id, date, -1, () => trackersApi.untickTracker(id, date))
    },
    async setEntry(id, date, value, note) {
      const before = this.cell(id, date)?.value ?? null
      const res = await trackersApi.upsertEntry(id, { date, value, note })
      this._finish(id, res)
      return { previous: before, value: res.value }
    },
    async clearEntry(id, date) {
      const before = this.cell(id, date)?.value ?? null
      const res = await trackersApi.deleteEntry(id, date)
      this._finish(id, res)
      return { previous: before, value: null }
    },
    // Put a cell back to what it was before a tap (undo): null means no entry.
    revert(id, date, previous) {
      return previous === null || previous === undefined ? this.clearEntry(id, date) : this.setEntry(id, date, previous)
    },
    async history(id, weeks = 'all') {
      if (!this.histories[id]) this.histories[id] = await trackersApi.trackerHistory(id, weeks)
      return this.histories[id]
    },
  },
})
