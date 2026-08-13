/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f7f9fb",
        surface: "#f7f9fb",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f2f4f6",
        "surface-container": "#eceef0",
        "surface-container-high": "#e6e8ea",
        "surface-container-highest": "#e0e3e5",

        primary: "#000000",
        secondary: "#0058be",
        "secondary-container": "#2170e4",

        "on-surface": "#191c1e",
        "on-surface-variant": "#45464d",

        outline: "#76777d",
        "outline-variant": "#c6c6cd",

        error: "#ba1a1a",
        "error-container": "#ffdad6",

        "tertiary-fixed-dim": "#4edea3",
        "on-tertiary-container": "#009668",
      },

      fontFamily: {
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },

      borderRadius: {
        DEFAULT: "0.25rem",
        lg: "0.5rem",
        xl: "0.75rem",
      },
    },
  },
  plugins: [],
};