// vitest.config.js
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true, // ← esto habilita expect, describe, it, etc.
    environment: 'jsdom', // ← necesario para pruebas de React
    setupFiles: './vitest.setup.js' // archivo opcional de setup
  }
})
