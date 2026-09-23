import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

// Local dev: /api is proxied to Flask so the browser never deals with CORS
// and VITE_API_BASE can stay empty. On Railway VITE_API_BASE points at the api service.
export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'mark-dark.svg', 'apple-touch-icon.png', 'logo.png', 'fonts/geist-latin.woff2'],
      manifest: {
        name: 'Pozzy',
        short_name: 'Pozzy',
        description: 'Personal operating system: agenda, mail triage, tasks, goals, tracking, hours, study.',
        theme_color: '#F2F2F7',
        background_color: '#F2F2F7',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'pwa-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // App shell and built assets are precached (cache-first). API is network-first with a short fallback.
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/api/'),
            handler: 'NetworkFirst',
            options: { cacheName: 'pozzy-api', networkTimeoutSeconds: 8, expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 } },
          },
          {
            urlPattern: ({ url }) => /\.(?:png|svg|ico|woff2?)$/.test(url.pathname),
            handler: 'CacheFirst',
            options: { cacheName: 'pozzy-assets', expiration: { maxEntries: 60, maxAgeSeconds: 60 * 60 * 24 * 30 } },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET || 'http://127.0.0.1:5000', // macOS AirPlay holds 5000: API_PROXY_TARGET=http://127.0.0.1:5001 npm run dev
        changeOrigin: true,
      },
    },
  },
})
