import { defineStore } from 'pinia'
import * as trackersApi from '../api/trackers'
import { mondayOf } from '../lib/dates'

export const useTrackersStore = defineStore('trackers', {
  state: () => ({
    weekStart: mondayOf(),
    week: null,
    includeInactive: false,
    loading: false,
    error: '',
    histories: {},
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
    async tick(id, date) {
      await trackersApi.tickTracker(id, date)
      await this.load()
      delete this.histories[id]
    },
    async setEntry(id, date, value, note) {
      await trackersApi.upsertEntry(id, { date, value, note })
      await this.load()
      delete this.histories[id]
    },
    async clearEntry(id, date) {
      await trackersApi.deleteEntry(id, date)
      await this.load()
      delete this.histories[id]
    },
    async history(id, weeks = 'all') {
      if (!this.histories[id]) this.histories[id] = await trackersApi.trackerHistory(id, weeks)
      return this.histories[id]
    },
  },
})
