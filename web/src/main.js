import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import { applyTheme } from './composables/useTheme'
import { track } from './lib/nav'

applyTheme()
// Which way the next page change animates on the phone (push, pop or none).
router.afterEach(track)

const app = createApp(App)
app.provide('weight', 'light') // Phosphor: thin precise lines everywhere unless an icon says otherwise
app.use(createPinia()).use(router).mount('#app')
