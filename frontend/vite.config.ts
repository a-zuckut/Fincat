import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

// Vite config for React + TS frontend talking to FastAPI backend on 8000
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/stocks': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
    },
  },
});
