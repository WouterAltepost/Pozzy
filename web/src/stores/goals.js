import { defineStore } from 'pinia'
import * as dosApi from '../api/dos'
import * as goalsApi from '../api/goals'
import { mondayOf, today, tomorrow } from '../lib/dates'

export const useGoalsStore = defineStore('goals', {
  state: () => ({
    weekStart: mondayOf(),
    goals: [],
    dos: [],
    loading: false,
    error: '',
    suggestions: null,
  }),
  getters: {
    dosFor: (s) => (day) => s.dos.filter((d) => d.date === day).sort((a, b) => a.position - b.position),
    todayDos() {
      return this.dosFor(today())
    },
    tomorrowDos() {
      return this.dosFor(tomorrow())
    },
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const [goals, dos] = await Promise.all([goalsApi.listGoals(this.weekStart), dosApi.listDos({ from: today(), to: tomorrow() })])
        this.weekStart = goals.week_start
        this.goals = goals.goals
        this.dos = dos
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async loadWeek(weekStart) {
      this.weekStart = weekStart
      const data = await goalsApi.listGoals(weekStart)
      this.weekStart = data.week_start
      this.goals = data.goals
    },
    _replaceGoal(goal) {
      const i = this.goals.findIndex((g) => g.id === goal.id)
      if (i === -1) this.goals.push(goal)
      else this.goals[i] = goal
      return goal
    },
    async createGoal(body) {
      return this._replaceGoal(await goalsApi.createGoal({ ...body, week_start: this.weekStart }))
    },
    async updateGoal(id, body) {
      return this._replaceGoal(await goalsApi.updateGoal(id, body))
    },
    async progressGoal(id, delta = 1) {
      return this._replaceGoal(await goalsApi.addGoalProgress(id, delta))
    },
    async removeGoal(id) {
      await goalsApi.deleteGoal(id)
      this.goals = this.goals.filter((g) => g.id !== id)
    },
    _replaceDo(item) {
      const i = this.dos.findIndex((d) => d.id === item.id)
      if (i === -1) this.dos.push(item)
      else this.dos[i] = item
      return item
    },
    async createDo(body) {
      return this._replaceDo(await dosApi.createDo(body))
    },
    async updateDo(id, body) {
      return this._replaceDo(await dosApi.updateDo(id, body))
    },
    async toggleDo(item) {
      return this.updateDo(item.id, { done: !item.done })
    },
    async removeDo(id) {
      await dosApi.deleteDo(id)
      this.dos = this.dos.filter((d) => d.id !== id)
    },
    async suggest(day) {
      this.suggestions = await dosApi.suggestDos(day)
      return this.suggestions
    },
    async rolloverNow() {
      const res = await dosApi.rolloverNow()
      await this.load()
      return res.message
    },
  },
})
