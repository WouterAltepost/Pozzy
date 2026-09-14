import { defineStore } from 'pinia'
import * as settingsApi from '../api/settings'

export const useSettingsStore = defineStore('settings', {
  state: () => ({ values: null, defaults: null, jobRuns: [], loading: false, saving: false, error: '' }),
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const [values, defaults] = await Promise.all([settingsApi.getSettings(), settingsApi.getSettingDefaults()])
        this.values = values
        this.defaults = defaults
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async loadJobRuns() {
      try {
        this.jobRuns = await settingsApi.listJobRuns(50)
      } catch (err) {
        this.error = err.message
      }
    },
    async save(patch) {
      this.saving = true
      this.error = ''
      try {
        this.values = await settingsApi.updateSettings(patch)
      } catch (err) {
        this.error = err.message
        throw err
      } finally {
        this.saving = false
      }
    },
  },
})
