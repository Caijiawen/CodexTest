/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bitcoin: '#f7931a',
        ethereum: '#627eea',
        solana: '#9945ff',
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}