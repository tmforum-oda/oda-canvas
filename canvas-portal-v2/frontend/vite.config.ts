import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, '')
  const backend = env.VITE_DEV_BACKEND_URL || 'http://localhost:8080'
  const keycloak = env.VITE_DEV_KEYCLOAK_PROXY_TARGET || 'https://35.239.58.96:8443'

  const toBackend = { target: backend, changeOrigin: true }
  const toKeycloak = { target: keycloak, changeOrigin: true, secure: false }

  return {
    plugins: [react()],
    resolve: {
      alias: { '@': resolve(__dirname, './src') },
    },
    server: {
      port: 3000,
      proxy: {
        '/api': toBackend,
        '/health': toBackend,
        // Backend-owned session endpoints. Keep in sync with the /auth/*
        // locations in nginx/default.conf.template.
        '/auth/me': toBackend,
        '/auth/login': toBackend,
        '/auth/refresh': toBackend,
        '/auth/logout': toBackend,
        '/auth/set-initial-password': toBackend,
        '/auth/security-status': toBackend,
        '/auth/realms': toKeycloak,
        '/auth/resources': toKeycloak,
        '/auth/js': toKeycloak,
        '/auth/admin': toKeycloak,
      },
    },
  }
})
