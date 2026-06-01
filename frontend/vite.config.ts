import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    headers: {
      // Vite dev sunucusu HMR ve source map için eval kullanır.
      // 'unsafe-eval' olmadan Framer Motion animasyonları ve hot reload çalışmaz.
      "Content-Security-Policy": [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https: blob:",
        "media-src 'self' blob:",
        "connect-src 'self' http://localhost:8000 ws://localhost:5173 ws://localhost:*",
      ].join("; "),
    },
  },
})
