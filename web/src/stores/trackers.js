import { defineStore } from 'pinia'
import * as trackersApi from '../api/trackers'
import { mondayOf, today } from '../lib/dates'

// Quick taps update the cell at once and the server's row replaces it when the call lands;
// nothing reloads the whole week. `version` bumps on every write so charts and stats refetch.
// Every write returns the cell as it was before ({ value, status, note }) so a toast can undo it.
export const useTrackersStore = defineStore('trackers', {
  state: () => ({
    weekStart: mondayOf(),
    // The day the Today screen shows; the loaded week always contains it.
    day: today(),
    week: null,
    includeInactive: false,
    loading: false,
    error: '',
    histories: {},
    stats: {},
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
    byId: (s) => (id) => s.week?.trackers.find((t) => t.id === id) ?? null,
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
    // Move the Today screen to another day, loading its week when it is not the one on screen.
    async setDay(day) {
      this.day = day
      const monday = mondayOf(day)
      if (monday !== this.week?.week_start) await this.setWeek(monday)
    },
    async create(body) {
      const t = await trackersApi.createTracker(body)
      await this.load()
      return t
    },
    async update(id, body) {
      const t = await trackersApi.updateTracker(id, body)
      delete this.stats[id]
      await this.load()
      return t
    },
    async remove(id) {
      await trackersApi.deleteTracker(id)
      delete this.stats[id]
      await this.load()
    },
    async reorder(ids) {
      if (this.week) {
        const order = new Map(ids.map((id, i) => [id, i]))
        this.week.trackers.sort((a, b) => (order.get(a.id) ?? 999) - (order.get(b.id) ?? 999))
      }
      await trackersApi.reorderTrackers(ids)
    },
    _patchRow(row) {
      if (!this.week) return
      const i = this.week.trackers.findIndex((t) => t.id === row.id)
      if (i === -1) return
      // Rows of another week (a write on a cell outside the shown week) are ignored.
      if (row.days[0]?.date !== this.week.week_start) return
      this.week.trackers[i] = row
    },
    _finish(id, res) {
      if (res?.row) this._patchRow(res.row)
      delete this.histories[id]
      delete this.stats[id]
      this.version += 1
      return res
    },
    _snapshot(id, date) {
      const c = this.cell(id, date)
      return { value: c?.value ?? null, status: c?.status ?? null, note: c?.note ?? null }
    },
    // Expected value after one tap, applied before the server answers.
    _guess(t, current, direction) {
      if (t.type === 'daily_bool') return current ? 0 : 1
      const step = t.type === 'weekly_count' ? 1 : t.target_period === 'day' && t.target_value ? t.target_value : 1
      const next = (current || 0) + direction * step
      return next <= 0 ? null : Math.round(next * 100) / 100
    },
    _optimistic(id, date, value, status = 'done') {
      const t = this.week?.trackers.find((x) => x.id === id)
      const d = t?.days.find((x) => x.date === date)
      if (!t || !d) return
      d.value = value
      d.status = value === null ? null : status
      const weekly = t.target_period === 'week'
      d.met = status === 'skipped' || value === null ? false : t.type === 'daily_bool' || weekly || t.target_value == null ? value > 0 : value >= t.target_value
      t.week_total = t.days.reduce((s, x) => s + (x.status === 'skipped' ? 0 : x.value || 0), 0)
      if (weekly) t.week_met = t.target_value ? t.week_total >= t.target_value : t.week_total > 0
    },
    async _write(id, date, direction, call) {
      const t = this.week?.trackers.find((x) => x.id === id)
      const before = this._snapshot(id, date)
      const current = before.status === 'skipped' ? 0 : before.value
      if (t) this._optimistic(id, date, this._guess(t, current, direction))
      try {
        const res = await call()
        this._finish(id, res)
        return { previous: before, value: res?.value ?? null }
      } catch (err) {
        if (t) this._optimistic(id, date, before.value, before.status || 'done')
        throw err
      }
    },
    tick(id, date) {
      return this._write(id, date, 1, () => trackersApi.tickTracker(id, date))
    },
    untick(id, date) {
      return this._write(id, date, -1, () => trackersApi.untickTracker(id, date))
    },
    // Exact write from the check-in sheet: value, status (done or skipped) and note together.
    async setEntry(id, date, value, note, status = 'done') {
      const before = this._snapshot(id, date)
      this._optimistic(id, date, status === 'skipped' ? 0 : value, status)
      try {
        const res = await trackersApi.upsertEntry(id, { date, value: status === 'skipped' ? 0 : value, note, status })
        this._finish(id, res)
        return { previous: before, value: res.value, status: res.status }
      } catch (err) {
        this._optimistic(id, date, before.value, before.status || 'done')
        throw err
      }
    },
    skip(id, date, note) {
      return this.setEntry(id, date, 0, note, 'skipped')
    },
    async clearEntry(id, date) {
      const before = this._snapshot(id, date)
      if (before.value === null && before.status === null) return { previous: before, value: null }
      this._optimistic(id, date, null)
      try {
        const res = await trackersApi.deleteEntry(id, date)
        this._finish(id, res)
      } catch (err) {
        this._optimistic(id, date, before.value, before.status || 'done')
        throw err
      }
      return { previous: before, value: null }
    },
    // Put a cell back to what it was before a write (undo): no value and no status means no entry.
    revert(id, date, previous) {
      if (!previous || (previous.value === null && !previous.status)) return this.clearEntry(id, date)
      return this.setEntry(id, date, previous.value ?? 0, previous.note ?? '', previous.status || 'done')
    },
    async history(id, weeks = 'all') {
      if (!this.histories[id]) this.histories[id] = await trackersApi.trackerHistory(id, weeks)
      return this.histories[id]
    },
    async loadStats(id) {
      if (!this.stats[id]) this.stats[id] = await trackersApi.trackerStats(id)
      return this.stats[id]
    },
  },
})
