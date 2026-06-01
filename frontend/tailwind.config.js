/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'gradient': 'gradient 15s ease infinite',
        'ping-slow': 'ping-slow 5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-slow': 'pulse-slow 4s ease-in-out infinite',
        'zoom': 'zoom 6s ease-in-out infinite',
        'bounce-slow': 'bounce-slow 7s ease-in-out infinite',
        'float-particle': 'float-particle 8s linear infinite',
      },
      keyframes: {
        'gradient': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'ping-slow': {
          '0%': { transform: 'scale(0.95)', opacity: '0.5' },
          '50%': { transform: 'scale(1.5)', opacity: '0.2' },
          '100%': { transform: 'scale(0.95)', opacity: '0.5' },
        },
        'pulse-slow': {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.3' },
          '50%': { transform: 'scale(1.3)', opacity: '0.1' },
        },
        'zoom': {
          '0%, 100%': { transform: 'scale(0.8)', opacity: '0.3' },
          '50%': { transform: 'scale(1.4)', opacity: '0.1' },
        },
        'bounce-slow': {
          '0%, 100%': { transform: 'translateY(0) scale(1)', opacity: '0.2' },
          '50%': { transform: 'translateY(-30px) scale(1.1)', opacity: '0.1' },
        },
        'float-particle': {
          '0%, 100%': { transform: 'translateY(0px) translateX(0px)', opacity: '0' },
          '25%': { opacity: '0.6' },
          '50%': { transform: 'translateY(-80px) translateX(40px)', opacity: '0.3' },
          '75%': { opacity: '0.6' },
        },
      },
    },
  },
  plugins: [],
}