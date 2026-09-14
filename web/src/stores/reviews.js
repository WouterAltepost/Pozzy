import { defineStore } from 'pinia'
import * as reviewsApi from '../api/reviews'
import { mondayOf } from '../lib/dates'

export const useReviewsStore = defineStore('reviews', {
  state: () => ({ week: mondayOf(), review: null, list: [], loading: false, error: '' }),
  actions: {
    async load(week = this.week) {
      this.week = week
      this.loading = true
      this.error = ''
      try {
        this.review = await reviewsApi.getReview(week)
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async loadList() {
      try {
        this.list = await reviewsApi.listReviews()
      } catch (err) {
        this.error = err.message
      }
    },
    async generate() {
      this.review = await reviewsApi.generateReview(this.week)
      return this.review
    },
    async refreshStats() {
      this.review = await reviewsApi.refreshReviewStats(this.week)
    },
    async update(body) {
      this.review = await reviewsApi.updateReview(this.week, body)
    },
    async finalize() {
      const out = await reviewsApi.finalizeReview(this.week)
      this.review = out.review
      return out.created_goals
    },
  },
})
