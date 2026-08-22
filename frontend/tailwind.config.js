/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F6F7F9",
        surface: "#FFFFFF",
        ink: {
          DEFAULT: "#12151C",
          soft: "#4B5262",
          faint: "#8A90A0",
        },
        line: "#E2E5EA",
        rail: {
          DEFAULT: "#0F1117",
          soft: "#1B1E28",
        },
        accent: {
          DEFAULT: "#4F46E5",
          soft: "#EEF0FD",
          hover: "#4338CA",
        },
        signal: {
          safe: "#16A34A",
          "safe-soft": "#EAF7EE",
          warn: "#D97706",
          "warn-soft": "#FDF3E4",
          danger: "#DC2626",
          "danger-soft": "#FCEAEA",
          neutral: "#64748B",
          "neutral-soft": "#EEF0F3",
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
