import { defineStore } from 'pinia'
import * as mailApi from '../api/mail'

const emptyFilters = () => ({ account_id: '', category: '', area_id: '', needs_reply: '', handled: '0', priority: '', q: '' })

export const useMailStore = defineStore('mail', {
  state: () => ({
    items: [],
    accounts: [],
    counts: { unhandled: 0, needs_reply: 0, unclassified: 0 },
    selected: null,
    loading: false,
    syncing: false,
    error: '',
    filters: emptyFilters(),
  }),
  getters: {
    accountById: (s) => Object.fromEntries(s.accounts.map((a) => [a.id, a])),
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const [items, counts] = await Promise.all([mailApi.listEmails(this.filters), mailApi.mailCounts()])
        this.items = items
        this.counts = counts
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async loadAccounts() {
      try {
        this.accounts = await mailApi.listAccounts()
      } catch (err) {
        this.error = err.message
      }
    },
    resetFilters() {
      this.filters = emptyFilters()
      return this.load()
    },
    async open(id) {
      this.selected = await mailApi.getEmail(id)
      return this.selected
    },
    close() {
      this.selected = null
    },
    _replace(email) {
      const index = this.items.findIndex((e) => e.id === email.id)
      if (index >= 0) this.items[index] = { ...this.items[index], ...email }
      if (this.selected?.id === email.id) this.selected = { ...this.selected, ...email }
    },
    async update(id, body) {
      const email = await mailApi.updateEmail(id, body)
      this._replace(email)
      // Handled rows leave the default (unhandled) list.
      if ('handled' in body && this.filters.handled !== 'all' && String(Number(email.handled)) !== this.filters.handled) {
        this.items = this.items.filter((e) => e.id !== id)
      }
      this.counts = await mailApi.mailCounts().catch(() => this.counts)
      return email
    },
    async markHandled(id, handled = true) {
      return this.update(id, { handled })
    },
    async createTask(id, body = {}) {
      const result = await mailApi.createTaskFromEmail(id, body)
      if (this.selected?.id === id) this.selected = { ...this.selected, task_id: result.task.id }
      return result
    },
    async reclassify(id) {
      const email = await mailApi.reclassifyEmail(id)
      this._replace(email)
      return email
    },
    async sync() {
      this.syncing = true
      this.error = ''
      try {
        const result = await mailApi.syncMail()
        await Promise.all([this.load(), this.loadAccounts()])
        return result
      } catch (err) {
        this.error = err.message
        throw err
      } finally {
        this.syncing = false
      }
    },
    async updateAccount(id, body) {
      const account = await mailApi.updateAccount(id, body)
      const index = this.accounts.findIndex((a) => a.id === id)
      if (index >= 0) this.accounts[index] = account
      return account
    },
    async testAccount(id) {
      const result = await mailApi.testAccount(id)
      const index = this.accounts.findIndex((a) => a.id === id)
      if (index >= 0 && result.account) this.accounts[index] = result.account
      return result
    },
  },
})
