/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        soc: {
          bg: '#0F172A',       // Slate 900
          card: '#1E293B',     // Slate 800
          border: '#334155',   // Slate 700
          hover: '#334155',
          accent: '#3B82F6',   // Blue 500
          critical: '#EF4444', // Red 500
          high: '#F97316',     // Orange 500
          medium: '#F59E0B',   // Amber 500
          low: '#10B981',      // Emerald 500
          info: '#06B6D4'      // Cyan 500
        }
      }
    },
  },
  plugins: [],
}
