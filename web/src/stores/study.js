import { defineStore } from 'pinia'
import * as studyApi from '../api/study'

export const APPLICATION_STATUSES = ['found', 'applied', 'interview', 'offer', 'rejected']

export const useStudyStore = defineStore('study', {
  state: () => ({
    courses: [],
    deadlines: [],
    applications: [],
    includeClosedCourses: false,
    includeDoneDeadlines: false,
    loading: false,
    error: '',
  }),
  getters: {
    applicationsByStatus: (s) => (status) => s.applications.filter((a) => a.status === status),
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const [courses, deadlines, applications] = await Promise.all([
          studyApi.listCourses(this.includeClosedCourses),
          studyApi.listDeadlines(this.includeDoneDeadlines),
          studyApi.listApplications(),
        ])
        this.courses = courses
        this.deadlines = deadlines
        this.applications = applications
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async createCourse(body) {
      await studyApi.createCourse(body)
      await this.load()
    },
    async updateCourse(id, body) {
      await studyApi.updateCourse(id, body)
      await this.load()
    },
    async removeCourse(id) {
      await studyApi.deleteCourse(id)
      await this.load()
    },
    async createDeadline(body) {
      await studyApi.createDeadline(body)
      await this.load()
    },
    async updateDeadline(id, body) {
      await studyApi.updateDeadline(id, body)
      await this.load()
    },
    async removeDeadline(id) {
      await studyApi.deleteDeadline(id)
      await this.load()
    },
    async createApplication(body) {
      await studyApi.createApplication(body)
      await this.load()
    },
    async updateApplication(id, body) {
      const row = await studyApi.updateApplication(id, body)
      const i = this.applications.findIndex((a) => a.id === id)
      if (i !== -1) this.applications[i] = row
      return row
    },
    async removeApplication(id) {
      await studyApi.deleteApplication(id)
      this.applications = this.applications.filter((a) => a.id !== id)
    },
  },
})
