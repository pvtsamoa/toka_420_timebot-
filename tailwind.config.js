/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
    './lib/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#0a0a0a',
        neonPurple: '#b026ff',
        neonBlue: '#00d4ff',
        neonGreen: '#6dff67',
        neonYellow: '#ffe45c',
      },
      boxShadow: {
        neon: '0 0 0 1px rgba(255,255,255,0.08), 0 0 24px rgba(176, 38, 255, 0.45), 0 0 38px rgba(0, 212, 255, 0.18)',
        lime: '0 0 0 1px rgba(255,255,255,0.08), 0 0 24px rgba(109, 255, 103, 0.45)',
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        pulseRing: 'pulseRing 500ms ease-out',
        shimmer: 'shimmer 2.2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        pulseRing: {
          '0%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(0.96)' },
          '100%': { transform: 'scale(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '200% 50%' },
        },
      },
    },
  },
  plugins: [],
};