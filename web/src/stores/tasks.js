import { defineStore } from 'pinia'
import * as tasksApi from '../api/tasks'

export const QUADRANTS = [
  { key: 'do', label: 'Do first', hint: 'urgent + important' },
  { key: 'schedule', label: 'Schedule', hint: 'important, not urgent' },
  { key: 'delegate', label: 'Delegate', hint: 'urgent, not important' },
  { key: 'eliminate', label: 'Eliminate', hint: 'neither' },
]

export const useTasksStore = defineStore('tasks', {
  state: () => ({
    items: [],
    loading: false,
    error: '',
    filters: { include_closed: false, area_id: '', q: '' },
  }),
  getters: {
    open: (s) => s.items.filter((t) => t.status !== 'done' && t.status !== 'dropped'),
    byQuadrant: (s) => (key) => s.items.filter((t) => t.quadrant === key && t.status !== 'done' && t.status !== 'dropped'),
    byId: (s) => (id) => s.items.find((t) => t.id === id),
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        this.items = await tasksApi.listTasks({
          include_closed: this.filters.include_closed ? 1 : undefined,
          area_id: this.filters.area_id || undefined,
          q: this.filters.q || undefined,
        })
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    _replace(task) {
      const i = this.items.findIndex((t) => t.id === task.id)
      if (i === -1) this.items.unshift(task)
      else this.items[i] = task
      return task
    },
    async create(body) {
      return this._replace(await tasksApi.createTask(body))
    },
    async update(id, body) {
      return this._replace(await tasksApi.updateTask(id, body))
    },
    async move(id, quadrant) {
      const current = this.byId(id)
      if (current && current.quadrant === quadrant) return current
      return this._replace(await tasksApi.moveTask(id, quadrant))
    },
    async complete(id, actualMinutes) {
      const task = await tasksApi.completeTask(id, actualMinutes)
      if (this.filters.include_closed) this._replace(task)
      else this.items = this.items.filter((t) => t.id !== id)
      return task
    },
    async remove(id) {
      await tasksApi.deleteTask(id)
      this.items = this.items.filter((t) => t.id !== id)
    },
    suggestSlot(id, body) {
      return tasksApi.suggestSlot(id, body)
    },
    async schedule(id, body) {
      return this._replace(await tasksApi.scheduleTask(id, body))
    },
    async unschedule(id) {
      return this._replace(await tasksApi.unscheduleTask(id))
    },
  },
})
