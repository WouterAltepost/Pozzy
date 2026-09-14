import { defineStore } from 'pinia'
import * as calendarApi from '../api/calendar'
import { addDays, mondayOf, today, weekDays } from '../lib/dates'

// Local midnight of a YYYY-MM-DD day as an ISO string with the browser offset (Europe/Amsterdam).
export function dayStartIso(day) {
  const [y, m, d] = day.split('-').map(Number)
  return new Date(y, m - 1, d).toISOString()
}

export const useCalendarStore = defineStore('calendar', {
  state: () => ({
    view: 'week', // 'week' | 'day'
    anchor: today(), // any day in the shown week, or the shown day
    events: [],
    tasks: [],
    loading: false,
    error: '',
    account: null,
    accountError: '',
    syncing: false,
    syncMessage: '',
  }),
  getters: {
    days(s) {
      return s.view === 'week' ? weekDays(mondayOf(s.anchor)) : [s.anchor]
    },
    rangeStart() {
      return this.days[0]
    },
    rangeEndExclusive() {
      return addDays(this.days[this.days.length - 1], 1)
    },
    selectedCalendars(s) {
      const known = s.account?.known_calendars || []
      const selected = new Set(s.account?.calendar_urls || [])
      return known.filter((c) => selected.has(c.url))
    },
    calendarName(s) {
      return (url) => (s.account?.known_calendars || []).find((c) => c.url === url)?.name || ''
    },
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const data = await calendarApi.listEvents({ start: dayStartIso(this.rangeStart), end: dayStartIso(this.rangeEndExclusive) })
        this.events = data.events
        this.tasks = data.tasks
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    setView(view) {
      if (view !== this.view) {
        this.view = view
        return this.load()
      }
    },
    setAnchor(day) {
      this.anchor = day
      return this.load()
    },
    step(direction) {
      return this.setAnchor(addDays(this.anchor, direction * (this.view === 'week' ? 7 : 1)))
    },
    goToday() {
      return this.setAnchor(today())
    },
    async createEvent(body) {
      const created = await calendarApi.createEvent(body)
      await this.load()
      return created
    },
    async updateEvent(id, body) {
      const updated = await calendarApi.updateEvent(id, body)
      await this.load()
      return updated
    },
    async removeEvent(id) {
      await calendarApi.deleteEvent(id)
      this.events = this.events.filter((e) => e.id !== id)
    },
    async sync() {
      this.syncing = true
      this.syncMessage = ''
      try {
        const res = await calendarApi.syncNow()
        this.syncMessage = res.message
        if (res.account) this.account = res.account
        await this.load()
      } catch (err) {
        this.syncMessage = err.message
      } finally {
        this.syncing = false
      }
    },
    async loadAccount() {
      this.accountError = ''
      try {
        this.account = await calendarApi.getAccount()
      } catch (err) {
        this.accountError = err.message
      }
    },
    async saveAccount(patch) {
      this.accountError = ''
      try {
        this.account = await calendarApi.updateAccount(patch)
      } catch (err) {
        this.accountError = err.message
        throw err
      }
    },
    async discover() {
      this.accountError = ''
      try {
        const res = await calendarApi.discoverCalendars()
        this.account = res.account
        return res.calendars
      } catch (err) {
        this.accountError = err.message
        throw err
      }
    },
  },
})
