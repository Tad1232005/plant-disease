/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        leaf: {
          50: '#f2fbf5',
          100: '#ddf7e6',
          200: '#bcedcb',
          300: '#8cdda8',
          400: '#55c47d',
          500: '#2fa861',
          600: '#21894c',
          700: '#1d6d40',
          800: '#1b5736',
          900: '#17472e',
        },
      },
      boxShadow: {
        soft: '0 18px 45px -24px rgba(20, 74, 45, 0.28)',
      },
      backgroundImage: {
        'hero-glow': 'radial-gradient(circle at 85% 15%, rgba(140, 221, 168, 0.35), transparent 32%), radial-gradient(circle at 5% 95%, rgba(221, 247, 230, 0.9), transparent 38%)',
      },
    },
  },
  plugins: [],
}
