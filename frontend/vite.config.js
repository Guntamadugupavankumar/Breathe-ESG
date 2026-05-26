import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'https://breathe-esg-backend-lxcp.onrender.com',
        changeOrigin: true,
        secure: true,
      }
    }
  }
})