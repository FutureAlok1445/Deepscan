export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'ds-bg': '#0a0a0f',
        'ds-bg-alt': '#0f0f1a',
        'ds-card': '#12121f',
        'ds-red': '#ff3c00',
        'ds-silver': '#e0e0e0',
        'ds-yellow': '#ffd700',
        'ds-cyan': '#00f5ff',
        'ds-green': '#39ff14',
      },
      fontFamily: {
        grotesk: ['Space Grotesk', 'sans-serif'],
        mono: ['Space Mono', 'monospace'],
      },
      borderWidth: {
        '3': '3px',
      },
      boxShadow: {
        brutal: '8px 8px 0 #000000',
        'brutal-red': '8px 8px 0 #ff3c00',
        'brutal-white': '8px 8px 0 #ffffff',
        'brutal-sm': '4px 4px 0 #000000',
        'brutal-lg': '12px 12px 0 #000000',
        'brutal-glow': '0 0 30px rgba(255,60,0,0.3)',
      },
    },
  },
  plugins: [],
}
