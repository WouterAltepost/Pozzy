import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Local dev: /api is proxied to Flask so the browser never deals with CORS
// and VITE_API_BASE can stay empty. On Railway VITE_API_BASE points at the api service.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
