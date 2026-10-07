import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: '#0a0e17',
        panel: '#111827',
        accent: '#22d3ee',
        accent2: '#a855f7',
        fire: '#fb923c',
      },
      boxShadow: {
        glow: '0 0 18px rgba(34, 211, 238, 0.35)',
      },
    },
  },
} satisfies Config
