/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ivory: "#FAF8F4",
        surface: "#FFFFFF",
        ink: "#211F1C",
        muted: "#706B64",
        line: "#E8E1D7",
        dark: "#171513",
        champagne: "#F3EBDA",
        beige: "#EFE9DF",
        brown: "#5C4A3A",
        gold: { DEFAULT: "#C9A45C", deep: "#8A6A24", soft: "#E9D9B4" },
      },
      fontFamily: {
        display: ['"Playfair Display"', "Georgia", '"Times New Roman"', "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", '"Segoe UI"', "sans-serif"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(33,31,28,0.04), 0 8px 24px -14px rgba(33,31,28,0.14)",
        lift: "0 2px 4px rgba(33,31,28,0.05), 0 20px 40px -18px rgba(33,31,28,0.24)",
      },
      keyframes: {
        "fade-up": { from: { opacity: "0", transform: "translateY(16px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "fade-down": { from: { opacity: "0", transform: "translateY(-12px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        "scale-in": { from: { opacity: "0", transform: "scale(0.97)" }, to: { opacity: "1", transform: "scale(1)" } },
        "sheet-up": { from: { transform: "translateY(100%)" }, to: { transform: "translateY(0)" } },
        "slide-left": { from: { transform: "translateX(100%)" }, to: { transform: "translateX(0)" } },
        "heart-pop": { "0%": { transform: "scale(1)" }, "45%": { transform: "scale(1.35)" }, "100%": { transform: "scale(1)" } },
        "ring-pulse": { "0%": { transform: "scale(0.8)", opacity: "0.7" }, "100%": { transform: "scale(1.7)", opacity: "0" } },
        shimmer: { "0%": { backgroundPosition: "-400px 0" }, "100%": { backgroundPosition: "400px 0" } },
        float: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-6px)" } },
      },
      animation: {
        "fade-up": "fade-up 0.7s cubic-bezier(0.22,1,0.36,1) backwards",
        "fade-in": "fade-in 0.5s ease-out both",
        "fade-down": "fade-down 0.35s ease-out both",
        "scale-in": "scale-in 0.25s ease-out both",
        "sheet-up": "sheet-up 0.35s cubic-bezier(0.22,1,0.36,1) both",
        "slide-left": "slide-left 0.35s cubic-bezier(0.22,1,0.36,1) both",
        "heart-pop": "heart-pop 0.4s ease-out",
        "ring-pulse": "ring-pulse 2.4s ease-out infinite",
        float: "float 7s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
