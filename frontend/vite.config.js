import path from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const dirname = path.dirname(fileURLToPath(import.meta.url))

// serves ../data (out.mp4, metrics.json) at the site root, so the 260MB
// video doesn't need to be copied into the frontend project
export default defineConfig({
  plugins: [react()],
  publicDir: path.resolve(dirname, '../data'),
})
