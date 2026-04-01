/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#0a0e1a",
        "navy-light": "#111827",
        terminal: "#00d4aa",
        danger: "#ff4757",
        warning: "#ffa502",
        border: "#1e2d3d",
        "text-muted": "#a4b0be",
      },
      fontFamily: {
        mono: ['"IBM Plex Mono"', "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
