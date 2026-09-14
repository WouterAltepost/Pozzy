import { defineStore } from 'pinia'
import { supabase } from '../lib/supabase'

let initPromise = null

export const useAuthStore = defineStore('auth', {
  state: () => ({
    session: null,
    initialized: false,
  }),
  getters: {
    user: (state) => state.session?.user ?? null,
    isAuthenticated: (state) => Boolean(state.session),
  },
  actions: {
    // Restores a persisted session once and keeps the store in sync afterwards.
    init() {
      if (this.initialized) return Promise.resolve()
      if (!initPromise) {
        initPromise = supabase.auth.getSession().then(({ data }) => {
          this.session = data.session
          supabase.auth.onAuthStateChange((_event, session) => {
            this.session = session
          })
          this.initialized = true
        })
      }
      return initPromise
    },
    async login(email, password) {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) throw error
      this.session = data.session
    },
    async logout() {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
      this.session = null
    },
  },
})
