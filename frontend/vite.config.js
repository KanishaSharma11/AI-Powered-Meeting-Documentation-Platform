import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // Lets the dev server proxy API calls to the FastAPI backend,
      // so the frontend can just call "/api/..." in both dev and
      // production (where it's served behind the same origin/reverse
      // proxy) without an env-based base URL switch.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})