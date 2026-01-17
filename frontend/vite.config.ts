import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/vars.scss" as *;`,
      },
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
})
