/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        base: {
          950: "#05070a",
          900: "#0b0f14",
          800: "#111722",
          700: "#1b2331",
          600: "#2a3547",
        },
        accent: {
          500: "#22d3ee",
          400: "#38bdf8",
        },
      },
    },
  },
  plugins: [],
};
