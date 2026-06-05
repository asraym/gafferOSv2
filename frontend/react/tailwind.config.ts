import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['var(--font-display)', 'Barlow Condensed', 'sans-serif'],
        body:    ['var(--font-body)', 'Barlow', 'sans-serif'],
        mono:    ['var(--font-mono)', 'JetBrains Mono', 'monospace'],
      },
      fontWeight: {
        600: '600',
        700: '700',
        800: '800',
        900: '900',
      },
      colors: {
        base:    '#F7F3EE',
        surface: '#EDE4D8',
        border:  '#C8B89A',
        accent:  '#B86A3C',
        text:    '#3D3530',
        muted:   '#8C7A63',
        success: '#5A8A6A',
        alert:   '#C8612A',
      },
    },
  },
  plugins: [],
}

export default config