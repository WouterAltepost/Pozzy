import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// Order and names from docs/ROUTES.md. Widgets and views link by route name.
export const NAV = [
  { path: '/', name: 'home', label: 'Home', view: () => import('../views/HomeView.vue') },
  { path: '/agenda', name: 'agenda', label: 'Agenda', view: () => import('../views/AgendaView.vue') },
  { path: '/tasks', name: 'tasks', label: 'Tasks', view: () => import('../views/TasksView.vue') },
  { path: '/goals', name: 'goals', label: 'Goals', view: () => import('../views/GoalsView.vue') },
  { path: '/mail', name: 'mail', label: 'Mail', view: () => import('../views/MailView.vue') },
  { path: '/trackers', name: 'trackers', label: 'Tracking', view: () => import('../views/TrackersView.vue') },
  { path: '/hours', name: 'hours', label: 'Hours', view: () => import('../views/HoursView.vue') },
  { path: '/capture', name: 'capture', label: 'Capture', view: () => import('../views/CaptureView.vue') },
  { path: '/study', name: 'study', label: 'Study', view: () => import('../views/StudyView.vue') },
  { path: '/notes', name: 'notes', label: 'Notes', view: () => import('../views/NotesView.vue') },
  { path: '/review', name: 'review', label: 'Review', view: () => import('../views/WeeklyReviewView.vue') },
  { path: '/settings', name: 'settings', label: 'Settings', view: () => import('../views/SettingsView.vue') },
]

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  ...NAV.map((r) => ({ path: r.path, name: r.name, component: r.view })),
  { path: '/:pathMatch(.*)*', redirect: { name: 'home' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.init()

  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : {} }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'home' }
  }
  return true
})

export default router
