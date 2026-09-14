import { defineStore } from 'pinia'
import * as notesApi from '../api/notes'

export const useNotesStore = defineStore('notes', {
  state: () => ({ items: [], loading: false, error: '', filters: { area_id: '', tag: '', q: '' } }),
  getters: {
    allTags: (s) => [...new Set(s.items.flatMap((n) => n.tags || []))].sort(),
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        this.items = await notesApi.listNotes(this.filters)
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async create(body) {
      const note = await notesApi.createNote(body)
      await this.load()
      return note
    },
    async update(id, body) {
      const note = await notesApi.updateNote(id, body)
      await this.load()
      return note
    },
    async remove(id) {
      await notesApi.deleteNote(id)
      this.items = this.items.filter((n) => n.id !== id)
    },
  },
})
