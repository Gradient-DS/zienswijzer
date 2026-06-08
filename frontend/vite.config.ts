import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        // 127.0.0.1 (not "localhost"): on macOS "localhost" resolves to IPv6
        // ::1 first, which can collide with other :8000 publishers (e.g. a
        // Docker container). Pinning IPv4 hits the local uvicorn directly.
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
