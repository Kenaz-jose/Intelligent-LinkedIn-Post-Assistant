/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: '#F4F3EF',
        surface: '#FBFAF7',
        'surface-muted': '#EEEDE9',
        ink: '#25282A',
        'ink-secondary': '#777B7B',
        'ink-muted': '#999C9B',
        border: '#DEDDD8',
        selected: '#DFE4E5',
        success: '#7D8C89',
        warning: '#A98E62',
        error: '#A4564D',
        graphite: '#2D343A',
      },
      fontFamily: {
        editorial: ['Newsreader', 'serif'],
        sans: ['"DM Sans"', 'sans-serif'],
      },
      borderRadius: {
        'button': '16px',
        'card': '20px',
        'pill': '999px',
        'control': '10px',
        'option': '13px',
      },
      boxShadow: {
        'quiet': '0 2px 4px rgba(0, 0, 0, 0.02)',
        'soft': '0 4px 12px rgba(45, 52, 58, 0.06)',
      },
      maxWidth: {
        'workspace': '1320px',
      }
    },
  },
  plugins: [],
}

