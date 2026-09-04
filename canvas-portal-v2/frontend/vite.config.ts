import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': resolve(__dirname, './src') },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
      '/health': { target: 'http://localhost:8080', changeOrigin: true },
      '/auth/me': { target: 'http://localhost:8080', changeOrigin: true },
      '/auth/realms': {
        target: 'https://35.239.58.96:8443',
        changeOrigin: true,
        secure: false,
      },
      '/auth/resources': {
        target: 'https://35.239.58.96:8443',
        changeOrigin: true,
        secure: false,
      },
      '/auth/js': {
        target: 'https://35.239.58.96:8443',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
