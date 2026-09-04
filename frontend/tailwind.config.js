/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef6ff',
          100: '#d9ebff',
          500: '#0066cc',
          600: '#0052a3',
          700: '#0c2340',
          800: '#08172b',
          900: '#040b15',
        },
      },
    },
  },
  plugins: [],
}
