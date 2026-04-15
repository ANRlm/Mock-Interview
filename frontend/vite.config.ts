import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import fs from 'node:fs'

const certKeyPath = path.resolve(__dirname, './certs/dev-key.pem')
const certPath = path.resolve(__dirname, './certs/dev-cert.pem')
const useDevHttps = String(process.env.VITE_DEV_HTTPS ?? '').toLowerCase() === 'true'
const hasHttpsCert = fs.existsSync(certKeyPath) && fs.existsSync(certPath)
const httpsConfig = useDevHttps && hasHttpsCert
  ? {
      key: fs.readFileSync(certKeyPath),
      cert: fs.readFileSync(certPath),
    }
  : undefined

if (useDevHttps && !hasHttpsCert) {
  console.warn('VITE_DEV_HTTPS=true but dev cert is missing; fallback to HTTP.')
}

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  base: './',
  server: {
    port: 5173,
    host: '0.0.0.0',
    https: httpsConfig,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/ws': {
        target: apiProxyTarget.replace('http', 'ws'),
        ws: true,
        changeOrigin: true,
      },
    },
  },
})