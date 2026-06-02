/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        saffron:  { DEFAULT: "#FF6B2B", light: "#FF8C55", dark: "#D94F10" },
        ashoka:   { DEFAULT: "#0A3D91", light: "#1254C0", dark: "#072A63" },
        jade:     { DEFAULT: "#138808", light: "#1AAD0A", dark: "#0D5F06" },
        cream:    { DEFAULT: "#FFF8EF", dark: "#F5EDE0" },
        charcoal: { DEFAULT: "#1A1A2E", light: "#2D2D4A" },
      },
      fontFamily: {
        display: ["'Noto Serif Devanagari'", "serif"],
        body:    ["'Noto Sans'", "sans-serif"],
        mono:    ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        card:  "0 4px 24px rgba(10, 61, 145, 0.08)",
        glow:  "0 0 24px rgba(255, 107, 43, 0.25)",
        "glow-blue": "0 0 24px rgba(10, 61, 145, 0.25)",
      },
      backgroundImage: {
        "india-gradient":   "linear-gradient(135deg, #FF6B2B 0%, #0A3D91 50%, #138808 100%)",
        "saffron-gradient": "linear-gradient(135deg, #FF6B2B, #FF8C55)",
        "blue-gradient":    "linear-gradient(135deg, #0A3D91, #1254C0)",
        "hero-pattern":     "radial-gradient(ellipse at 20% 50%, rgba(255,107,43,0.12) 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, rgba(10,61,145,0.10) 0%, transparent 60%)",
      },
      animation: {
        "pulse-slow":    "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "bounce-subtle": "bounce-subtle 2s ease-in-out infinite",
        "wave":          "wave 1.2s ease-in-out infinite",
        "slide-in":      "slide-in 0.4s ease-out",
        "fade-up":       "fade-up 0.5s ease-out",
      },
      keyframes: {
        "bounce-subtle": {
          "0%, 100%": { transform: "translateY(-4px)" },
          "50%":      { transform: "translateY(0)"    },
        },
        "wave": {
          "0%, 60%, 100%": { transform: "initial" },
          "30%":           { transform: "translateY(-8px)" },
        },
        "slide-in": {
          from: { transform: "translateX(-12px)", opacity: 0 },
          to:   { transform: "translateX(0)",     opacity: 1 },
        },
        "fade-up": {
          from: { transform: "translateY(16px)", opacity: 0 },
          to:   { transform: "translateY(0)",    opacity: 1 },
        },
      },
    },
  },
  plugins: [],
};
