import { defineStore } from 'pinia'
import { getAreas } from '../api/core'

// Shared read-only cache of the four life areas. Stream A owns this file.
export const useAreasStore = defineStore('areas', {
  state: () => ({ items: [], loaded: false, loading: false, error: '' }),
  getters: {
    byId: (s) => Object.fromEntries(s.items.map((a) => [a.id, a])),
    name: (s) => (id) => s.items.find((a) => a.id === id)?.name ?? '',
    color: (s) => (id) => s.items.find((a) => a.id === id)?.color ?? '#9ca3af',
  },
  actions: {
    async load(force = false) {
      if ((this.loaded && !force) || this.loading) return
      this.loading = true
      this.error = ''
      try {
        this.items = await getAreas()
        this.loaded = true
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
  },
})
