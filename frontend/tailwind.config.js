/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        'surface-base': '#F8FAFC',
        'surface-card': '#FFFFFF',
        'surface-card-sub': '#F1F5F9',
        'surface-hover': '#EEF2F6',
        'border-subtle': '#E2E8F0',
        'border-strong': '#CBD5E1',
        'accent-action': '#3B82F6',
        'accent-action-hover': '#2563EB',
        'accent-live': '#059669',
        'accent-alert': '#D97706',
        'accent-danger': '#E11D48',
      }
    },
  },
  plugins: [],
}
