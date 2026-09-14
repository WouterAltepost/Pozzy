import { defineStore } from 'pinia'
import * as capturesApi from '../api/captures'

export const useCapturesStore = defineStore('captures', {
  state: () => ({ items: [], loading: false, error: '' }),
  getters: {
    open: (s) => s.items.filter((c) => c.status === 'new'),
    handled: (s) => s.items.filter((c) => c.status !== 'new'),
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        this.items = await capturesApi.listCaptures()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    replace(capture) {
      const i = this.items.findIndex((c) => c.id === capture.id)
      if (i === -1) this.items.unshift(capture)
      else this.items[i] = capture
    },
    // Stores the text at once (works with AI off), then asks for a proposal.
    async submit(text) {
      const created = await capturesApi.createCapture(text)
      this.replace(created)
      try {
        const processed = await capturesApi.processCapture(created.id)
        this.replace(processed)
        return processed
      } catch (err) {
        this.error = err.message
        return created
      }
    },
    async process(id) {
      const c = await capturesApi.processCapture(id)
      this.replace(c)
      return c
    },
    async confirm(id, body) {
      const out = await capturesApi.confirmCapture(id, body)
      this.replace(out.capture)
      return out
    },
    async discard(id) {
      this.replace(await capturesApi.discardCapture(id))
    },
    async remove(id) {
      await capturesApi.deleteCapture(id)
      this.items = this.items.filter((c) => c.id !== id)
    },
  },
})
