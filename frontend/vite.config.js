import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  server: {
    port: 3000,
    proxy: {
      '/run':    'http://localhost:8001',
      '/tasks':  'http://localhost:8001',
      '/task':   'http://localhost:8001',
      '/health': 'http://localhost:8001',
    },
  },

  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './vitest.setup.js',
  },
})
