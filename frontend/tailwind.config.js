/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#1B1E28",
        surface: "#181B24",
        "surface-soft": "#14161F",
        ink: {
          DEFAULT: "#F4F5F7",
          soft: "#dadde6",
          faint: "#d6deee",
        },
        line: "#2A2E3A",
        rail: {
          DEFAULT: "#0F1117",
          soft: "#1B1E28",
        },
        accent: {
          DEFAULT: "#4F46E5",
          soft: "#232544",
          hover: "#6366F1",
        },
        signal: {
          safe: "#4ADE80",
          "safe-soft": "#16321F",
          warn: "#FBBF24",
          "warn-soft": "#3A2A0F",
          danger: "#F87171",
          "danger-soft": "#3A1919",
          neutral: "#94A3B8",
          "neutral-soft": "#242832",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 17, 23, 0.04), 0 1px 8px rgba(15, 17, 23, 0.03)",
      },
    },
  },
  plugins: [],
};
