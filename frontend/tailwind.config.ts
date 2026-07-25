import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./features/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void:        "#050508",
        surface:     "#0d0f17",
        panel:       "#121520",
        border:      "rgba(255,255,255,0.07)",
        amber:       "#f59e0b",
        "amber-dim": "rgba(245,158,11,0.15)",
        blue:        "#3b82f6",
        violet:      "#8b5cf6",
        green:       "#10b981",
        muted:       "rgba(255,255,255,0.35)",
        ink:         "rgba(255,255,255,0.88)",
        // Legacy tokens (kept for backward compatibility)
        graphite:    "#0B0F14",
        panelBorder: "#1F2A38",
        steel:       "#8FA3B8",
        statusGreen: "#3ECF8E",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
      borderRadius: {
        "2xl": "14px",
        "3xl": "20px",
      },
      animation: {
        "fade-up":     "fade-up 0.5s cubic-bezier(0.16,1,0.3,1) forwards",
        "fade-in":     "fade-in 0.4s ease forwards",
        "scale-in":    "scale-in 0.35s cubic-bezier(0.16,1,0.3,1) forwards",
        "float":       "float 4s ease-in-out infinite",
        "spin-slow":   "spin-slow 8s linear infinite",
        "pulse-amber": "pulse-amber 2s ease infinite",
        "pulse-blue":  "pulse-blue 2s ease infinite",
        "pulse-green": "pulse-green 2s ease infinite",
        "shimmer":     "shimmer 2s infinite",
      },
    },
  },
  plugins: [],
};
export default config;
