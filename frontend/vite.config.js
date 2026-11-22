
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/api/accounts': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/api/cart': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/api/wishlist': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/api/orders': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/api/payments': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
